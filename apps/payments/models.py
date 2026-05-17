from django.db import models
from django.conf import settings


class PaymentTransaction(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('card', 'Credit/Debit Card (Stripe)'),
        ('tabby', 'Tabby Installments'),
        ('tamara', 'Tamara Installments'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid Successfully'),
        ('failed', 'Payment Failed'),
        ('refunded', 'Refunded'),
    ]

    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='transactions')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    transaction_id = models.CharField(max_length=255, unique=True, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_url = models.URLField(max_length=1000, blank=True)
    provider_raw_response = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Transaction {self.transaction_id} ({self.payment_method}) - {self.status}"
