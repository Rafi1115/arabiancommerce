import stripe
import uuid
from django.conf import settings
from apps.payments.models import PaymentTransaction

# Set Stripe Secret Key
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')


class StripeService:
    @staticmethod
    def is_configured():
        key = getattr(settings, 'STRIPE_SECRET_KEY', '')
        return bool(key and not key.startswith('your_') and not key.startswith('mock_'))

    @classmethod
    def create_checkout_session(cls, order):
        amount_in_cents = int(order.total * 100)
        
        # Check if stripe keys are configured properly, otherwise use Sandbox Simulator
        if not cls.is_configured():
            mock_session_id = f"cs_sim_{uuid.uuid4().hex}"
            payment_url = f"http://127.0.0.1:8000/api/payments/simulate-portal/{mock_session_id}/"
            
            transaction = PaymentTransaction.objects.create(
                order=order,
                payment_method='card',
                transaction_id=mock_session_id,
                amount=order.total,
                status='pending',
                payment_url=payment_url,
                provider_raw_response={"mode": "simulated", "note": "Stripe credentials missing/dummy"}
            )
            return transaction

        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'aed',
                        'product_data': {
                            'name': f"Order #{order.order_number}",
                            'description': "Arabian Commerce Purchase",
                        },
                        'unit_amount': amount_in_cents,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=f"http://127.0.0.1:8000/api/payments/callback/stripe/success/?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"http://127.0.0.1:8000/api/payments/callback/stripe/cancel/?session_id={{CHECKOUT_SESSION_ID}}",
                client_reference_id=str(order.id)
            )

            transaction = PaymentTransaction.objects.create(
                order=order,
                payment_method='card',
                transaction_id=session.id,
                amount=order.total,
                status='pending',
                payment_url=session.url,
                provider_raw_response=session
            )
            return transaction
        except Exception as e:
            # Fallback to simulation on Stripe exception
            mock_session_id = f"cs_sim_err_{uuid.uuid4().hex}"
            payment_url = f"http://127.0.0.1:8000/api/payments/simulate-portal/{mock_session_id}/"
            
            transaction = PaymentTransaction.objects.create(
                order=order,
                payment_method='card',
                transaction_id=mock_session_id,
                amount=order.total,
                status='pending',
                payment_url=payment_url,
                provider_raw_response={"mode": "simulated_fallback", "error": str(e)}
            )
            return transaction
