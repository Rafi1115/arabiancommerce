from rest_framework import generics, status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from apps.core.utils.mixins import BaseResponseMixin
from apps.accounts.serializers import AdminLoginSerializer, AdminChangePasswordSerializer, DeliveryZoneSerializer
from apps.accounts.models import DeliveryZone


class AdminLoginView(BaseResponseMixin, generics.GenericAPIView):
    """
    Admin dashboard login — email + password.
    Only works for is_staff=True users.
    """
    serializer_class = AdminLoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)

        return self.success_response(
            data={
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "is_staff": user.is_staff,
                    "is_superuser": user.is_superuser,
                },
            },
            message="Admin login successful.",
        )


class AdminChangePasswordView(BaseResponseMixin, generics.GenericAPIView):
    """
    Admin changes their own password.
    Requires current password + new password.
    """
    serializer_class = AdminChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return self.success_response(message="Password changed successfully.")


class AdminLogoutView(BaseResponseMixin, generics.GenericAPIView):
    """Blacklist refresh token."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return self.error_response(
                    message="Refresh token is required.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            token = RefreshToken(refresh_token)
            token.blacklist()
            return self.success_response(message="Logged out successfully.")
        except Exception:
            return self.error_response(
                message="Invalid or expired refresh token.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )


# ─────────────────────────── DELIVERY ZONE MANAGEMENT ───────────────────────────

class DeliveryZoneListCreateView(BaseResponseMixin, generics.ListCreateAPIView):
    """
    GET /api/admin/delivery-zones/ → List all delivery zones
    POST /api/admin/delivery-zones/ → Create new delivery zone
    """
    serializer_class = DeliveryZoneSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = DeliveryZone.objects.all()

    def get_queryset(self):
        queryset = DeliveryZone.objects.all()
        city = self.request.query_params.get('city')
        is_active = self.request.query_params.get('is_active')
        
        if city:
            queryset = queryset.filter(city__icontains=city)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
        return queryset.order_by('city', 'name')


class DeliveryZoneDetailView(BaseResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/admin/delivery-zones/<pk>/ → Get delivery zone details
    PUT /api/admin/delivery-zones/<pk>/ → Update delivery zone
    DELETE /api/admin/delivery-zones/<pk>/ → Delete delivery zone
    """
    serializer_class = DeliveryZoneSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = DeliveryZone.objects.all()