from django.contrib import admin
from .models import PickupLocation, Order, OrderItem, OrderTracking

@admin.register(PickupLocation)
class PickupLocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'address', 'latitude', 'longitude', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'address')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


class OrderTrackingInline(admin.TabularInline):
    model = OrderTracking
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'receive_method', 'pickup_location', 'total', 'created_at')
    list_filter = ('status', 'receive_method', 'payment_method', 'created_at')
    search_fields = ('order_number', 'user__phone', 'user__email')
    inlines = [OrderItemInline, OrderTrackingInline]

