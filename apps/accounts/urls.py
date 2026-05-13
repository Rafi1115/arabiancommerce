from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from apps.accounts.views.customers_views import (
    AddressDetailView,
    AddressListCreateView,
    SendRegistrationOTPView,
    VerifyRegistrationOTPView,
    SendLoginOTPView,
    VerifyLoginOTPView,
    ResendOTPView,
    LogoutView,
    UserProfileView,
    AccountSoftDeleteView,
    AccountRestoreView,
)
from apps.accounts.views.admin_views import AdminLoginView, AdminChangePasswordView, AdminLogoutView, DeliveryZoneListCreateView, DeliveryZoneDetailView

# Customer urlpatterns
urlpatterns = [
    # Registration
    path("register/send-otp/", SendRegistrationOTPView.as_view(), name="register-send-otp"),
    path("register/verify-otp/", VerifyRegistrationOTPView.as_view(), name="register-verify-otp"),

    # Login
    path("login/send-otp/", SendLoginOTPView.as_view(), name="login-send-otp"),
    path("login/verify-otp/", VerifyLoginOTPView.as_view(), name="login-verify-otp"),

    # Shared
    path("resend-otp/", ResendOTPView.as_view(), name="resend-otp"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),

    # Profile
    path("profile/", UserProfileView.as_view(), name="user-profile"),

    # Account management
    path("account/delete/", AccountSoftDeleteView.as_view(), name="account-delete"),
    path("account/restore/", AccountRestoreView.as_view(), name="account-restore"),

    # Address
    path("addresses/", AddressListCreateView.as_view(), name="address-list-create"),
    path("addresses/<int:pk>/", AddressDetailView.as_view(), name="address-detail"),
]


# admin urlpatterns
urlpatterns += [
    path("admin/login/", AdminLoginView.as_view(), name="admin-login"),
    path("admin/logout/", AdminLogoutView.as_view(), name="admin-logout"),
    path("admin/change-password/", AdminChangePasswordView.as_view(), name="admin-change-password"),
    path("admin/delivery-zones/", DeliveryZoneListCreateView.as_view(), name="delivery-zone-list-create"),
    path("admin/delivery-zones/<int:pk>/", DeliveryZoneDetailView.as_view(), name="delivery-zone-detail"),
]