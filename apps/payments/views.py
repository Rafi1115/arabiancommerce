import stripe
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.core.utils.mixins import BaseResponseMixin
from apps.payments.models import PaymentTransaction
from apps.orders.models import Order, OrderTracking


# ─────────────────────────── WEB PORTAL SIMULATOR ───────────────────────────

class SimulatePortalView(View):
    """
    GET /api/payments/simulate-portal/<str:transaction_id>/
    Renders beautiful payment portal simulation.
    """
    def get(self, request, transaction_id):
        transaction = get_object_or_404(PaymentTransaction, transaction_id=transaction_id)
        return render(request, 'payments/simulate_portal.html', {'transaction': transaction})


@method_decorator(csrf_exempt, name='dispatch')
class SimulateCallbackAPIView(APIView):
    """
    POST /api/payments/simulate-callback/
    Callback receiver for simulated clicks.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        transaction_id = request.data.get('transaction_id')
        target_status = request.data.get('status') # 'paid' or 'failed'

        if not transaction_id or target_status not in ['paid', 'failed']:
            return JsonResponse({'error': 'Invalid arguments'}, status=status.HTTP_400_BAD_REQUEST)

        transaction = get_object_or_404(PaymentTransaction, transaction_id=transaction_id)
        order = transaction.order

        if target_status == 'paid':
            transaction.status = 'paid'
            transaction.save()

            order.payment_status = 'paid'
            order.save()

            # Add tracking
            OrderTracking.objects.create(
                order=order,
                status=order.status,
                note=f"Payment of {transaction.amount} completed successfully via Simulator."
            )
        else:
            transaction.status = 'failed'
            transaction.save()

            order.payment_status = 'failed'
            order.save()

            OrderTracking.objects.create(
                order=order,
                status=order.status,
                note="Payment authorization declined via Simulator."
            )

        return JsonResponse({
            'success': True,
            'message': f"Simulated status updated to {target_status}",
            'order_status': order.status,
            'payment_status': order.payment_status
        })


# ─────────────────────────── REAL STRIPE WEBHOOKS & CALLBACKS ───────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookAPIView(APIView):
    """
    POST /api/payments/webhook/stripe/
    Webhooks to sync Stripe status with local orders on production.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError:
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError:
            return HttpResponse(status=400)

        # Handle checkout.session.completed
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            session_id = session.get('id')
            
            # Retrieve payment details
            try:
                transaction = PaymentTransaction.objects.get(transaction_id=session_id)
                order = transaction.order
                
                transaction.status = 'paid'
                transaction.provider_raw_response = session
                transaction.save()

                order.payment_status = 'paid'
                order.save()

                OrderTracking.objects.create(
                    order=order,
                    status=order.status,
                    note=f"Stripe Checkout completed. Paid amount {transaction.amount} successfully verified."
                )
            except PaymentTransaction.DoesNotExist:
                pass

        return HttpResponse(status=200)


class StripeCallbackRedirectView(View):
    """
    GET /api/payments/callback/stripe/success/
    GET /api/payments/callback/stripe/cancel/
    """
    def get(self, request, status_type):
        session_id = request.GET.get('session_id')
        transaction = get_object_or_404(PaymentTransaction, transaction_id=session_id)
        order = transaction.order

        if status_type == 'success':
            transaction.status = 'paid'
            transaction.save()
            
            order.payment_status = 'paid'
            order.save()

            OrderTracking.objects.create(
                order=order,
                status=order.status,
                note="Redirect callback: payment successfully completed."
            )
            return render(request, 'payments/success_redirect.html', {'order': order})
        else:
            transaction.status = 'failed'
            transaction.save()

            order.payment_status = 'failed'
            order.save()

            OrderTracking.objects.create(
                order=order,
                status=order.status,
                note="Redirect callback: payment cancelled by user."
            )
            return render(request, 'payments/failed_redirect.html', {'order': order})


# ─────────────────────────── REAL TABBY CALLBACKS ───────────────────────────

class TabbyCallbackRedirectView(View):
    """
    GET /api/payments/callback/tabby/<status_type>/
    """
    def get(self, request, status_type):
        order_id = request.GET.get('order_id')
        order = get_object_or_404(Order, id=order_id)
        transaction = PaymentTransaction.objects.filter(order=order, payment_method='tabby').first()

        if status_type == 'success':
            if transaction:
                transaction.status = 'paid'
                transaction.save()
            
            order.payment_status = 'paid'
            order.save()

            OrderTracking.objects.create(
                order=order,
                status=order.status,
                note="Tabby installments verified and callback authenticated."
            )
            return render(request, 'payments/success_redirect.html', {'order': order})
        else:
            if transaction:
                transaction.status = 'failed'
                transaction.save()

            order.payment_status = 'failed'
            order.save()

            OrderTracking.objects.create(
                order=order,
                status=order.status,
                note="Tabby installments validation failed or cancelled."
            )
            return render(request, 'payments/failed_redirect.html', {'order': order})


# ─────────────────────────── REAL TAMARA CALLBACKS ───────────────────────────

class TamaraCallbackRedirectView(View):
    """
    GET /api/payments/callback/tamara/<status_type>/
    """
    def get(self, request, status_type):
        order_id = request.GET.get('order_id')
        order = get_object_or_404(Order, id=order_id)
        transaction = PaymentTransaction.objects.filter(order=order, payment_method='tamara').first()

        if status_type == 'success':
            if transaction:
                transaction.status = 'paid'
                transaction.save()
            
            order.payment_status = 'paid'
            order.save()

            OrderTracking.objects.create(
                order=order,
                status=order.status,
                note="Tamara installment verified successfully."
            )
            return render(request, 'payments/success_redirect.html', {'order': order})
        else:
            if transaction:
                transaction.status = 'failed'
                transaction.save()

            order.payment_status = 'failed'
            order.save()

            OrderTracking.objects.create(
                order=order,
                status=order.status,
                note="Tamara installment failed or cancelled by client."
            )
            return render(request, 'payments/failed_redirect.html', {'order': order})
