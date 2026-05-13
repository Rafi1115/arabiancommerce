from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("Phone number is required")
        user = self.model(phone=phone, **extra_fields)
        user.set_unusable_password()  # No password — OTP only
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        user = self.model(phone=phone, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractUser):
    """
    Custom user model — phone number is the unique identifier.
    No password required; auth is OTP-based.
    """
    username = models.CharField(max_length=150, unique=False, blank=True, null=True)
    email = models.EmailField(blank=True, null=True, unique=True)
    phone = models.CharField(max_length=20, unique=True)

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_blocked = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.phone

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.is_active = False
        self.save()

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.is_active = True
        self.save()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"


class OTP(models.Model):
    PURPOSE_CHOICES = [
        ("registration", "Registration"),
        ("login", "Login"),
        ("phone_change", "Phone Change"),
        ("other", "Other"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otps")
    otp = models.CharField(max_length=6)
    purpose = models.CharField(max_length=50, choices=PURPOSE_CHOICES)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.phone} — {self.purpose} OTP"

    def is_valid(self):
        return not self.is_used and self.expires_at > timezone.now()

    class Meta:
        verbose_name = "OTP"
        verbose_name_plural = "OTPs"


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to="accounts/profile_pictures/", blank=True, null=True
    )
    address = models.TextField(blank=True)
    last_active = models.DateTimeField(auto_now=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile — {self.user.phone}"
    

class Address(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='addresses')
    title = models.CharField(max_length=100)
    full_address = models.TextField()
    city = models.CharField(max_length=100, blank=True)
    area = models.CharField(max_length=100, blank=True)  # neighborhood/district
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    delivery_zone = models.ForeignKey('DeliveryZone', on_delete=models.SET_NULL, null=True, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.user.user} - {self.title}"

    def save(self, *args, **kwargs):
        # If this address is set as default, unset others
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        
        # Auto-assign delivery zone if not set and we have city/area
        if not self.delivery_zone and self.city and self.area:
            self.delivery_zone = self._find_delivery_zone()
        
        super().save(*args, **kwargs)
    
    def _find_delivery_zone(self):
        """Find matching delivery zone based on city and area"""
        from django.db.models import Q
        
        # Try exact city + area match
        zone = DeliveryZone.objects.filter(
            city__iexact=self.city,
            areas__icontains=self.area,
            is_active=True
        ).first()
        
        if zone:
            return zone
            
        # Try city match only
        zone = DeliveryZone.objects.filter(
            city__iexact=self.city,
            is_active=True
        ).first()
        
        return zone


class DeliveryZone(models.Model):
    """
    Delivery zones for location-based pricing
    """
    name = models.CharField(max_length=100, unique=True)  # e.g., "Downtown Dubai", "Jumeirah"
    city = models.CharField(max_length=100)
    areas = models.JSONField(default=list, help_text="List of areas covered by this zone")  # ["area1", "area2"]
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    estimated_delivery_time = models.CharField(max_length=50, blank=True, help_text="e.g., '30-45 mins', '1-2 hours'")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['city', 'name']

    def __str__(self):
        return f"{self.name} ({self.city}) - AED {self.delivery_fee}"



@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, "profile"):
        instance.profile.save()