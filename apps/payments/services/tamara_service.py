import requests
import uuid
import os
from django.conf import settings
from apps.payments.models import PaymentTransaction


class TamaraService:
    @staticmethod
    def is_configured():
        key = os.getenv('TAMARA_API_KEY', '')
        return bool(key and not key.startswith('your_') and not key.startswith('mock_'))

    @classmethod
    def create_checkout_session(cls, order):
        # Fallback to simulated portal if Tamara credentials are dummy or missing
        if not cls.is_configured():
            mock_session_id = f"tm_sim_{uuid.uuid4().hex}"
            payment_url = f"http://127.0.0.1:8000/api/payments/simulate-portal/{mock_session_id}/"

            transaction = PaymentTransaction.objects.create(
                order=order,
                payment_method='tamara',
                transaction_id=mock_session_id,
                amount=order.total,
                status='pending',
                payment_url=payment_url,
                provider_raw_response={"mode": "simulated", "note": "Tamara credentials missing/dummy"}
            )
            return transaction

        try:
            # Live/Sandbox Tamara Checkout API
            url = "https://api-sandbox.tamara.co/api/v2/checkout"
            headers = {
                "Authorization": f"Bearer {os.getenv('TAMARA_API_KEY')}",
                "Content-Type": "application/json"
            }

            # Map order items
            items_payload = []
            for item in order.items.all():
                items_payload.append({
                    "reference_id": str(item.id),
                    "name": item.product_name,
                    "type": "General",
                    "quantity": item.quantity,
                    "unit_price": {
                        "amount": float(item.unit_price),
                        "currency": "SAR"
                    },
                    "total_amount": {
                        "amount": float(item.subtotal),
                        "currency": "SAR"
                    }
                })

            payload = {
                "order_reference_id": order.order_number,
                "total_amount": {
                    "amount": float(order.total),
                    "currency": "SAR"
                },
                "description": f"Arabian Commerce Purchase #{order.order_number}",
                "country_code": "SA",
                "payment_type": "PAY_BY_INSTALMENTS",
                "locale": "en_US",
                "consumer": {
                    "first_name": order.user.profile.name.split()[0] if order.user and hasattr(order.user, 'profile') and order.user.profile.name else "Guest",
                    "last_name": order.user.profile.name.split()[-1] if order.user and hasattr(order.user, 'profile') and order.user.profile.name and len(order.user.profile.name.split()) > 1 else "Buyer",
                    "phone_number": order.user.phone if order.user else "+966501234567",
                    "email": order.user.email if order.user and order.user.email else "buyer@example.com"
                },
                "items": items_payload,
                "merchant_url": {
                    "success": f"http://127.0.0.1:8000/api/payments/callback/tamara/success/?order_id={order.id}",
                    "failure": f"http://127.0.0.1:8000/api/payments/callback/tamara/failure/?order_id={order.id}",
                    "cancel": f"http://127.0.0.1:8000/api/payments/callback/tamara/cancel/?order_id={order.id}",
                    "notification": f"http://127.0.0.1:8000/api/payments/webhook/tamara/"
                }
            }

            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                res_data = response.json()
                checkout_id = res_data.get('checkout_id')
                checkout_url = res_data.get('checkout_url')

                if not checkout_url:
                    checkout_url = f"http://127.0.0.1:8000/api/payments/simulate-portal/{checkout_id}/"

                transaction = PaymentTransaction.objects.create(
                    order=order,
                    payment_method='tamara',
                    transaction_id=checkout_id,
                    amount=order.total,
                    status='pending',
                    payment_url=checkout_url,
                    provider_raw_response=res_data
                )
                return transaction
            else:
                raise Exception(f"Tamara registration failed with status {response.status_code}: {response.text}")
        except Exception as e:
            # Fallback to simulated on exception
            mock_session_id = f"tm_sim_err_{uuid.uuid4().hex}"
            payment_url = f"http://127.0.0.1:8000/api/payments/simulate-portal/{mock_session_id}/"

            transaction = PaymentTransaction.objects.create(
                order=order,
                payment_method='tamara',
                transaction_id=mock_session_id,
                amount=order.total,
                status='pending',
                payment_url=payment_url,
                provider_raw_response={"mode": "simulated_fallback", "error": str(e)}
            )
            return transaction
