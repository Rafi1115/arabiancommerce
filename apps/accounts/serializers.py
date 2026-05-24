from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from datetime import timedelta

from .models import OTP, Address, UserProfile, DeliveryZone
from .services.otp_service import generate_otp, send_otp_sms

User = get_user_model()

OTP_EXPIRY_MINUTES = 10


# ── HELPERS ────────────────────────────────────────────────────────────────────

def _create_and_send_otp(user, purpose: str) -> str:
    """Create OTP record + send SMS. Returns otp_code for dev response."""
    # Invalidate previous unused OTPs for same purpose
    OTP.objects.filter(user=user, purpose=purpose, is_used=False).update(is_used=True)

    otp_code = generate_otp(6)
    OTP.objects.create(
        user=user,
        otp=otp_code,
        purpose=purpose,
        expires_at=timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES),
    )
    send_otp_sms(user.phone, otp_code, purpose)
    return otp_code


def _verify_otp(user, otp_code: str, purpose: str) -> "OTP":
    """
    Verify OTP. Raises ValidationError on failure.
    Returns the OTP object on success.
    """
    try:
        otp = OTP.objects.filter(
            user=user, purpose=purpose, otp=otp_code, is_used=False
        ).latest("created_at")

        if not otp.is_valid():
            raise serializers.ValidationError({"otp": "OTP has expired."})

        return otp

    except OTP.DoesNotExist:
        raise serializers.ValidationError({"otp": "Invalid OTP."})


# ── REGISTRATION ───────────────────────────────────────────────────────────────

class SendRegistrationOTPSerializer(serializers.Serializer):
    """
    Step 1 of signup: user sends phone + profile info → get OTP.
    """
    phone = serializers.CharField(max_length=20)
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    address = serializers.CharField()  # goes into Address model as full_address

    # def validate_phone(self, value):
    #     value = value.strip()
    #     if not value.startswith("+"):
    #         raise serializers.ValidationError(
    #             "Phone number must include country code, e.g. +966501234567"
    #         )
    #     return value

    def validate_email(self, value):
        phone = self.initial_data.get("phone", "").strip()
        qs = UserProfile.objects.filter(email=value)
        # Exclude the current user's profile if phone matches
        if phone:
            qs = qs.exclude(user__phone=phone)
        if qs.exists():
            raise serializers.ValidationError("This email is already in use.")
        return value
    
    
    def save(self):
        phone = self.validated_data["phone"]
        name = self.validated_data["name"]
        email = self.validated_data["email"]
        address = self.validated_data["address"]

        if User.objects.filter(phone=phone).exists():
            user = User.objects.get(phone=phone)
            if user.is_active:
                raise serializers.ValidationError(
                    {"phone": "This phone number is already registered. Please login."}
                )
            # Not verified yet — update profile info and resend
            profile = user.profile
            profile.name = name
            profile.email = email
            profile.save()

            # Update or create default address
            Address.objects.update_or_create(
                user=profile,
                is_default=True,
                defaults={"title": "Home", "full_address": address},
            )

            otp_code = _create_and_send_otp(user, "registration")
            return user, otp_code, "resent"

        # New user — create inactive
        user = User.objects.create(phone=phone, is_active=False)

        # Profile is auto-created via signal — just update it
        profile = user.profile
        profile.name = name
        profile.email = email
        profile.save()

        # Create default address
        Address.objects.create(
            user=profile,
            title="Home",
            full_address=address,
            is_default=True,
        )

        otp_code = _create_and_send_otp(user, "registration")
        return user, otp_code, "created"

class VerifyRegistrationOTPSerializer(serializers.Serializer):
    """
    Step 2 of signup: user sends phone + OTP → account activated + JWT returned.
    """
    phone = serializers.CharField(max_length=20)
    otp = serializers.CharField(max_length=6, min_length=6)

    def validate(self, attrs):
        phone = attrs["phone"].strip()
        otp_code = attrs["otp"]

        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            raise serializers.ValidationError({"phone": "No account found with this phone number."})

        if user.is_blocked:
            raise serializers.ValidationError(
                {"non_field_errors": "Your account has been suspended. Contact support."}
            )

        otp_obj = _verify_otp(user, otp_code, "registration")

        # Activate
        otp_obj.is_used = True
        otp_obj.save()
        user.is_active = True
        user.save()

        attrs["user"] = user
        return attrs


# ── LOGIN ──────────────────────────────────────────────────────────────────────

class SendLoginOTPSerializer(serializers.Serializer):
    """
    Step 1 of login: user sends phone → get OTP.
    Only works for verified (active) accounts.
    """
    phone = serializers.CharField(max_length=20)

    # def validate_phone(self, value):
    #     value = value.strip()
    #     if not value.startswith("+"):
    #         raise serializers.ValidationError(
    #             "Phone number must include country code, e.g. +966501234567"
    #         )
    #     return value

    def save(self):
        phone = self.validated_data["phone"]

        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            # Security: don't reveal if number exists
            # But we need to tell frontend something useful for dev
            raise serializers.ValidationError(
                {"phone": "No account found with this phone number."}
            )

        if user.is_blocked:
            raise serializers.ValidationError(
                {"phone": "Your account has been suspended. Contact support."}
            )

        if not user.is_active:
            raise serializers.ValidationError(
                {"phone": "Phone number not verified yet. Please complete registration."}
            )

        otp_code = _create_and_send_otp(user, "login")
        return user, otp_code


class VerifyLoginOTPSerializer(serializers.Serializer):
    """
    Step 2 of login: user sends phone + OTP → JWT returned.
    """
    phone = serializers.CharField(max_length=20)
    otp = serializers.CharField(max_length=6, min_length=6)

    def validate(self, attrs):
        phone = attrs["phone"].strip()
        otp_code = attrs["otp"]

        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            raise serializers.ValidationError({"phone": "No account found with this phone number."})

        if user.is_blocked:
            raise serializers.ValidationError(
                {"non_field_errors": "Your account has been suspended. Contact support."}
            )

        otp_obj = _verify_otp(user, otp_code, "login")
        otp_obj.is_used = True
        otp_obj.save()

        attrs["user"] = user
        return attrs


# ── RESEND OTP ─────────────────────────────────────────────────────────────────

class ResendOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)
    purpose = serializers.ChoiceField(choices=["registration", "login"])

    def save(self):
        phone = self.validated_data["phone"].strip()
        purpose = self.validated_data["purpose"]

        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            # Security — don't reveal
            return None, None

        if user.is_blocked:
            raise serializers.ValidationError(
                {"phone": "Your account has been suspended."}
            )

        if purpose == "registration" and user.is_active:
            raise serializers.ValidationError(
                {"phone": "This account is already verified. Please login."}
            )

        if purpose == "login" and not user.is_active:
            raise serializers.ValidationError(
                {"phone": "Account not verified. Please complete registration first."}
            )

        otp_code = _create_and_send_otp(user, purpose)
        return user, otp_code


# ── PROFILE ────────────────────────────────────────────────────────────────────

class UserProfileSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(source="user.phone", read_only=True)
    profile_picture = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = UserProfile
        fields = ["phone", "name", "email", "profile_picture"]  
        read_only_fields = ["phone"]


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Update name and email on profile."""

    class Meta:
        model = UserProfile
        fields = ["name", "email", "profile_picture"]

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        instance.save()
        return instance


class AdminProfileSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(source="user.phone", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = UserProfile
        fields = ["phone", "email", "name", "profile_picture"]
        read_only_fields = ["phone", "email"]

    
class AddressSerializer(serializers.ModelSerializer):
    delivery_zone_name = serializers.CharField(source='delivery_zone.name', read_only=True)
    delivery_fee = serializers.DecimalField(source='delivery_zone.delivery_fee', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Address
        fields = [
            'id', 'title', 'full_address', 'city', 'area', 'latitude', 'longitude',
            'delivery_zone', 'delivery_zone_name', 'delivery_fee',
            'is_default', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']



class AddressCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            'title', 'full_address', 'city', 'area', 'latitude', 'longitude',
            'delivery_zone', 'is_default'
        ]

    def create(self, validated_data):
        user_profile = self.context['request'].user.profile
        return Address.objects.create(user=user_profile, **validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()  
        return instance
class DeliveryZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryZone
        fields = [
            'id', 'name', 'city', 'areas', 'delivery_fee', 'is_active',
            'estimated_delivery_time', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
# ── ACCOUNT MANAGEMENT ─────────────────────────────────────────────────────────

class AccountSoftDeleteSerializer(serializers.Serializer):
    confirm = serializers.BooleanField()

    def validate_confirm(self, value):
        if not value:
            raise serializers.ValidationError("You must confirm to delete your account.")
        return value


class AccountRestoreSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)

    def validate_phone(self, value):
        try:
            user = User.objects.get(phone=value.strip())
        except User.DoesNotExist:
            raise serializers.ValidationError("No account found with this phone number.")

        if not user.is_deleted:
            raise serializers.ValidationError("This account is not deleted.")

        self.user = user
        return value
    

#admin Serializer for listing all users in admin panel

class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs["email"]
        password = attrs["password"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "Invalid credentials."})

        if user.is_blocked:
            raise serializers.ValidationError({"email": "This account has been suspended."})

        if not user.is_staff:
            raise serializers.ValidationError({"email": "You do not have admin access."})

        # authenticate uses phone as USERNAME_FIELD, so we do manual check
        if not user.check_password(password):
            raise serializers.ValidationError({"password": "Invalid credentials."})

        if not user.is_active:
            raise serializers.ValidationError({"email": "This account is inactive."})

        attrs["user"] = user
        return attrs


class AdminChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password2"]:
            raise serializers.ValidationError({"new_password": "Passwords don't match."})
        return attrs

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value
    

