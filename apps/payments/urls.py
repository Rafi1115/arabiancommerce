from django.urls import path
from apps.payments.views import (
    SimulatePortalView,
    SimulateCallbackAPIView,
    StripeWebhookAPIView,
    StripeCallbackRedirectView,
    TabbyCallbackRedirectView,
    TamaraCallbackRedirectView
)

app_name = 'payments'

urlpatterns = [
    # Simulation Portal
    path('simulate-portal/<str:transaction_id>/', SimulatePortalView.as_view(), name='simulate_portal'),
    path('simulate-callback/', SimulateCallbackAPIView.as_view(), name='simulate_callback'),
    
    # Real Provider Hooks & Callbacks
    path('webhook/stripe/', StripeWebhookAPIView.as_view(), name='stripe_webhook'),
    path('callback/stripe/<str:status_type>/', StripeCallbackRedirectView.as_view(), name='stripe_callback'),
    path('callback/tabby/<str:status_type>/', TabbyCallbackRedirectView.as_view(), name='tabby_callback'),
    path('callback/tamara/<str:status_type>/', TamaraCallbackRedirectView.as_view(), name='tamara_callback'),
]
