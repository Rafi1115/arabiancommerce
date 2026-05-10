from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from apps.core.utils.mixins import BaseResponseMixin
from apps.accounts.serializers import (
    AddressCreateUpdateSerializer,
    AddressSerializer,
    SendRegistrationOTPSerializer,
    VerifyRegistrationOTPSerializer,
    SendLoginOTPSerializer,
    VerifyLoginOTPSerializer,
    ResendOTPSerializer,
    UserProfileSerializer,
    ProfileUpdateSerializer,
    AccountSoftDeleteSerializer,
    AccountRestoreSerializer,
    AddressSerializer,
    AddressCreateUpdateSerializer,
)

from apps.accounts.models import Address
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model

User = get_user_model()


def _jwt_response(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "user": {"phone": user.phone, "id": user.id},
    }


# ── REGISTRATION ───────────────────────────────────────────────────────────────

class SendRegistrationOTPView(BaseResponseMixin, generics.GenericAPIView):
    serializer_class = SendRegistrationOTPSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, otp_code, action = serializer.save()

        return self.success_response(
            data={
                "phone": user.phone,
                "name": user.profile.name,
                "otp_code": otp_code,  # DEV ONLY — remove in production
            },
            message="OTP sent successfully." if action == "created" else "OTP resent to unverified account.",
            status_code=status.HTTP_200_OK,
        )

class VerifyRegistrationOTPView(BaseResponseMixin, generics.GenericAPIView):
    """Step 2: Verify OTP → activate account + return JWT."""
    serializer_class = VerifyRegistrationOTPSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        return self.success_response(
            data=_jwt_response(user),
            message="Registration successful.",
            status_code=status.HTTP_201_CREATED,
        )


# ── LOGIN ──────────────────────────────────────────────────────────────────────

class SendLoginOTPView(BaseResponseMixin, generics.GenericAPIView):
    """Step 1: Send OTP to phone for login."""
    serializer_class = SendLoginOTPSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, otp_code = serializer.save()

        return self.success_response(
            data={
                "phone": user.phone,
                "otp_code": otp_code,  # DEV ONLY — remove in production
            },
            message="OTP sent successfully.",
            status_code=status.HTTP_200_OK,
        )


class VerifyLoginOTPView(BaseResponseMixin, generics.GenericAPIView):
    """Step 2: Verify OTP → return JWT."""
    serializer_class = VerifyLoginOTPSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        return self.success_response(
            data=_jwt_response(user),
            message="Login successful.",
            status_code=status.HTTP_200_OK,
        )


# ── RESEND OTP ─────────────────────────────────────────────────────────────────

class ResendOTPView(BaseResponseMixin, generics.GenericAPIView):
    serializer_class = ResendOTPSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, otp_code = serializer.save()

        return self.success_response(
            data={
                "phone": user.phone if user else None,
                "otp_code": otp_code,  # DEV ONLY — remove in production
            },
            message="OTP resent successfully.",
        )


# ── LOGOUT ─────────────────────────────────────────────────────────────────────

class LogoutView(BaseResponseMixin, generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]

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


# ── PROFILE ────────────────────────────────────────────────────────────────────

class UserProfileView(BaseResponseMixin, generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        profile, _ = User.objects.get(pk=self.request.user.pk).profile.__class__.objects.get_or_create(
            user=self.request.user
        )
        return profile

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return self.success_response(data=serializer.data, message="Profile retrieved.")

    def put(self, request, *args, **kwargs):
        serializer = ProfileUpdateSerializer(
            self.get_object(), data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.success_response(data=serializer.data, message="Profile updated.")

    def patch(self, request, *args, **kwargs):
        return self.put(request, *args, **kwargs)


# ── ACCOUNT MANAGEMENT ─────────────────────────────────────────────────────────

class AccountSoftDeleteView(BaseResponseMixin, generics.GenericAPIView):
    serializer_class = AccountSoftDeleteSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.soft_delete()
        return self.success_response(message="Account deactivated successfully.")


class AccountRestoreView(BaseResponseMixin, generics.GenericAPIView):
    serializer_class = AccountRestoreSerializer
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.user.restore()
        return self.success_response(
            data={"phone": serializer.user.phone},
            message="Account restored successfully.",
        )
    

class AddressListCreateView(BaseResponseMixin, generics.GenericAPIView):
    """List all addresses + add new one."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        addresses = Address.objects.filter(user=request.user.profile)
        serializer = AddressSerializer(addresses, many=True)
        return self.success_response(
            data=serializer.data,
            message="Addresses retrieved."
        )

    def post(self, request):
        serializer = AddressCreateUpdateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        address = serializer.save()
        return self.success_response(
            data=AddressSerializer(address).data,
            message="Address added successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class AddressDetailView(BaseResponseMixin, generics.GenericAPIView):
    """Edit or delete a specific address."""
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk, request):
        try:
            return Address.objects.get(pk=pk, user=request.user.profile)
        except Address.DoesNotExist:
            return None

    def patch(self, request, pk):
        address = self.get_object(pk, request)
        if not address:
            return self.error_response(
                message="Address not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        serializer = AddressCreateUpdateSerializer(
            address,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.success_response(
            data=AddressSerializer(address).data,
            message="Address updated successfully.",
        )

    def delete(self, request, pk):
        address = self.get_object(pk, request)
        if not address:
            return self.error_response(
                message="Address not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        address.delete()
        return self.success_response(message="Address deleted successfully.")