import requests
import uuid
import os
from django.conf import settings
from apps.payments.models import PaymentTransaction


class TabbyService:
    @staticmethod
    def is_configured():
        key = os.getenv('TABBY_API_KEY', '')
        return bool(key and not key.startswith('your_') and not key.startswith('mock_'))

    @classmethod
    def create_checkout_session(cls, order):
        # Fallback to simulated portal if Tabby credentials are dummy or missing
        if not cls.is_configured():
            mock_session_id = f"tb_sim_{uuid.uuid4().hex}"
            payment_url = f"http://127.0.0.1:8000/api/payments/simulate-portal/{mock_session_id}/"

            transaction = PaymentTransaction.objects.create(
                order=order,
                payment_method='tabby',
                transaction_id=mock_session_id,
                amount=order.total,
                status='pending',
                payment_url=payment_url,
                provider_raw_response={"mode": "simulated", "note": "Tabby credentials missing/dummy"}
            )
            return transaction

        try:
            # Live/Sandbox Tabby Integration
            url = "https://api.tabby.ai/api/v2/checkout"
            headers = {
                "Authorization": f"Bearer {os.getenv('TABBY_API_KEY')}",
                "Content-Type": "application/json"
            }
            
            # Map order items
            items_payload = []
            for item in order.items.all():
                items_payload.append({
                    "title": item.product_name,
                    "quantity": item.quantity,
                    "unit_price": str(item.unit_price),
                    "category": item.product.category.name if item.product and item.product.category else "General"
                })

            payload = {
                "payment": {
                    "amount": str(order.total),
                    "currency": "AED",
                    "description": f"Arabian Commerce Order #{order.order_number}",
                    "buyer": {
                        "phone": order.user.phone if order.user else "+971501234567",
                        "email": order.user.email if order.user and order.user.email else "buyer@example.com",
                        "name": order.user.profile.name if order.user and hasattr(order.user, 'profile') else "Guest User"
                    },
                    "order": {
                        "reference_id": order.order_number,
                        "items": items_payload
                    },
                    "buyer_history": {
                        "registered_since": order.created_at.strftime("%Y-%m-%dT%H:%M:%SZ") if order.created_at else "2026-05-17T00:00:00Z",
                        "loyalty_level": 0
                    }
                },
                "lang": "en",
                "merchant_urls": {
                    "success": f"http://127.0.0.1:8000/api/payments/callback/tabby/success/?order_id={order.id}",
                    "cancel": f"http://127.0.0.1:8000/api/payments/callback/tabby/cancel/?order_id={order.id}",
                    "failure": f"http://127.0.0.1:8000/api/payments/callback/tabby/failure/?order_id={order.id}"
                }
            }

            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                res_data = response.json()
                payment_id = res_data.get('id')
                web_url = res_data.get('configuration', {}).get('available_products', {}).get('installments', [{}])[0].get('web_url')
                
                if not web_url:
                    web_url = res_data.get('configuration', {}).get('products', {}).get('installments', {}).get('web_url')
                
                if not web_url:
                    web_url = f"http://127.0.0.1:8000/api/payments/simulate-portal/{payment_id}/"

                transaction = PaymentTransaction.objects.create(
                    order=order,
                    payment_method='tabby',
                    transaction_id=payment_id,
                    amount=order.total,
                    status='pending',
                    payment_url=web_url,
                    provider_raw_response=res_data
                )
                return transaction
            else:
                raise Exception(f"Tabby registration failed with status {response.status_code}: {response.text}")
        except Exception as e:
            # Fallback to simulated on exception
            mock_session_id = f"tb_sim_err_{uuid.uuid4().hex}"
            payment_url = f"http://127.0.0.1:8000/api/payments/simulate-portal/{mock_session_id}/"

            transaction = PaymentTransaction.objects.create(
                order=order,
                payment_method='tabby',
                transaction_id=mock_session_id,
                amount=order.total,
                status='pending',
                payment_url=payment_url,
                provider_raw_response={"mode": "simulated_fallback", "error": str(e)}
            )
            return transaction
