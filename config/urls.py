from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # Customer auth (phone OTP)
    path("api/auth/", include("apps.accounts.urls")),

    # API endpoints
    path("api/", include("apps.categories.urls")),
    path("api/", include("apps.products.urls")),
    path("api/", include("apps.orders.urls")),
    path("api/", include("apps.dashboard.urls")),
    path("api/", include("apps.notifications.urls")),
    path("api/", include("apps.payments.urls")),
    path("api/", include("apps.banners.urls")),
    path("api/", include("apps.core.urls")),

    # Webhooks
    # path("api/webhooks/", include("apps.payments.urls.webhook_urlpatterns")),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
