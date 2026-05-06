
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import User, OTP, UserProfile, Address


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('phone', 'email', 'username', 'is_active', 'is_staff', 'is_blocked', 'is_deleted', 'created_at')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'is_blocked', 'is_deleted', 'created_at')
    search_fields = ('phone', 'email', 'username')
    readonly_fields = ('created_at', 'updated_at', 'deleted_at')
    
    fieldsets = (
        ('Authentication', {
            'fields': ('phone', 'password')
        }),
        ('Personal Info', {
            'fields': ('username', 'email')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Status', {
            'fields': ('is_blocked', 'is_deleted', 'deleted_at')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')
        }),
    )
    
    actions = ['soft_delete_selected', 'restore_selected', 'block_selected', 'unblock_selected']
    
    def soft_delete_selected(self, request, queryset):
        for user in queryset:
            user.soft_delete()
        self.message_user(request, f"{queryset.count()} user(s) soft-deleted.")
    soft_delete_selected.short_description = "Soft delete selected users"
    
    def restore_selected(self, request, queryset):
        for user in queryset:
            user.restore()
        self.message_user(request, f"{queryset.count()} user(s) restored.")
    restore_selected.short_description = "Restore selected users"
    
    def block_selected(self, request, queryset):
        queryset.update(is_blocked=True, is_active=False)
        self.message_user(request, f"{queryset.count()} user(s) blocked.")
    block_selected.short_description = "Block selected users"
    
    def unblock_selected(self, request, queryset):
        queryset.update(is_blocked=False, is_active=True)
        self.message_user(request, f"{queryset.count()} user(s) unblocked.")
    unblock_selected.short_description = "Unblock selected users"


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_phone', 'otp', 'purpose', 'is_valid_display', 'is_used', 'expires_at', 'created_at')
    list_filter = ('purpose', 'is_used', 'created_at')
    search_fields = ('user__phone', 'otp')
    readonly_fields = ('created_at', 'updated_at')
    
    def user_phone(self, obj):
        return obj.user.phone
    user_phone.short_description = 'User Phone'
    
    def is_valid_display(self, obj):
        if obj.is_valid():
            return format_html('<span style="color: green; font-weight: bold;">✓ Valid</span>')
        elif obj.is_used:
            return format_html('<span style="color: red; font-weight: bold;">✗ Used</span>')
        else:
            return format_html('<span style="color: orange; font-weight: bold;">⚠ Expired</span>')
    is_valid_display.short_description = 'Status'
    
    fieldsets = (
        ('User & OTP', {
            'fields': ('user', 'otp', 'purpose')
        }),
        ('Status', {
            'fields': ('is_used', 'expires_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


class AddressInline(admin.TabularInline):
    model = Address
    extra = 1
    fields = ('title', 'full_address', 'is_default')
    show_change_link = True


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_phone', 'name', 'email', 'address_preview', 'last_active')
    list_filter = ('created_at', 'last_active')
    search_fields = ('user__phone', 'name', 'email')
    readonly_fields = ('created_at', 'updated_at', 'last_active')
    inlines = [AddressInline]
    
    def user_phone(self, obj):
        return obj.user.phone
    user_phone.short_description = 'User Phone'
    
    def address_preview(self, obj):
        first_address = obj.addresses.first()
        if first_address:
            return format_html('<span style="color: green;">✓ {}</span>', first_address.title)
        return format_html('<span style="color: gray;">✗ No address</span>')
    address_preview.short_description = 'Addresses'
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Profile Info', {
            'fields': ('name', 'email', 'profile_picture', 'address')
        }),
        ('Activity', {
            'fields': ('last_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_profile_info', 'title', 'full_address_preview', 'is_default', 'created_at')
    list_filter = ('is_default', 'created_at', 'updated_at')
    search_fields = ('user__user__phone', 'user__name', 'title', 'full_address')
    readonly_fields = ('created_at', 'updated_at')
    
    def user_profile_info(self, obj):
        return f"{obj.user.user.phone} - {obj.user.name or 'No name'}"
    user_profile_info.short_description = 'User'
    
    def full_address_preview(self, obj):
        return obj.full_address[:50] + '...' if len(obj.full_address) > 50 else obj.full_address
    full_address_preview.short_description = 'Address'
    
    actions = ['set_as_default']
    
    def set_as_default(self, request, queryset):
        for address in queryset:
            address.is_default = True
            address.save()
        self.message_user(request, f"{queryset.count()} address(es) set as default.")
    set_as_default.short_description = "Set selected address(es) as default"
    
    fieldsets = (
        ('User Profile', {
            'fields': ('user',)
        }),
        ('Address Details', {
            'fields': ('title', 'full_address', 'is_default')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )