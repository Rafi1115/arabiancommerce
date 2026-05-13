from rest_framework import serializers
from .models import Cart, CartItem, Order, OrderItem, OrderTracking
from apps.products.serializers import ProductListSerializer
from apps.accounts.serializers import AddressSerializer
from apps.accounts.models import Address


# ─────────────────────────── CART ───────────────────────────

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    cut_type_name = serializers.CharField(source='cut_type.name', read_only=True)
    packaging_type_name = serializers.CharField(source='packaging_type.packaging_type.name', read_only=True)
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'cut_type_name', 'packaging_type_name', 'quantity', 'subtotal']


class CartItemAddSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    cut_type_id = serializers.IntegerField(required=False, allow_null=True)
    packaging_type_id = serializers.IntegerField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate_product_id(self, value):
        from apps.products.models import Product
        if not Product.objects.filter(pk=value, status=True).exists():
            raise serializers.ValidationError("Product not found or unavailable.")
        return value

    def validate(self, data):
        from apps.products.models import CutType, ProductCutType, ProductPackagingType
        product_id = data.get('product_id')
        cut_type_id = data.get('cut_type_id')
        packaging_type_id = data.get('packaging_type_id')

        if cut_type_id:
            if not ProductCutType.objects.filter(product_id=product_id, cut_type_id=cut_type_id).exists():
                raise serializers.ValidationError("Cut type does not belong to this product.")

        if packaging_type_id:
            if not ProductPackagingType.objects.filter(pk=packaging_type_id, product_id=product_id).exists():
                raise serializers.ValidationError("Packaging type does not belong to this product.")

        return data


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.ReadOnlyField()
    item_count = serializers.ReadOnlyField()
    delivery_fee = serializers.SerializerMethodField()
    grand_total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'item_count', 'total', 'delivery_fee', 'grand_total']

    def get_delivery_fee(self, obj):
        # Get delivery fee from user's default address
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                default_address = request.user.profile.addresses.filter(is_default=True).first()
                if default_address and default_address.delivery_zone:
                    return float(default_address.delivery_zone.delivery_fee)
            except:
                pass
        # Fallback to default fee
        return 89 if obj.items.exists() else 0

    def get_grand_total(self, obj):
        return float(obj.total) + self.get_delivery_fee(obj)


# ─────────────────────────── ORDER ───────────────────────────

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_name', 'product_image',
            'cut_type_name', 'packaging_type_name', 'quantity',
            'unit_price', 'subtotal'
        ]


class OrderTrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderTracking
        fields = ['id', 'status', 'note', 'timestamp']


class OrderListSerializer(serializers.ModelSerializer):
    """Lightweight — for list views and order history"""
    first_item_image = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'payment_method',
            'total', 'first_item_image', 'created_at'
        ]

    def get_first_item_image(self, obj):
        first = obj.items.first()
        if first and first.product_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(first.product_image.url)
        return None


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    tracking = OrderTrackingSerializer(many=True, read_only=True)
    delivery_address = AddressSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'payment_method', 'payment_status',
            'receive_method', 'delivery_type', 'scheduled_at',   # ← new
            'delivery_address', 'items', 'subtotal', 'delivery_fee', 'total',
            'tracking', 'notes', 'created_at', 'updated_at'
        ]


class CheckoutSerializer(serializers.Serializer):
    address_id = serializers.IntegerField()
    payment_method = serializers.ChoiceField(choices=['cash', 'card', 'tabby', 'tamara'])
    receive_method = serializers.ChoiceField(
        choices=['home_delivery', 'receive_in_market'],
        default='home_delivery'
    )
    delivery_type = serializers.ChoiceField(
        choices=['today', 'scheduled'],
        default='today'
    )
    scheduled_at = serializers.DateTimeField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data.get('delivery_type') == 'scheduled' and not data.get('scheduled_at'):
            raise serializers.ValidationError({
                'scheduled_at': 'scheduled_at is required when delivery_type is scheduled.'
            })
        return data

    def validate_address_id(self, value):
        from apps.accounts.models import Address
        request = self.context.get('request')
        if not Address.objects.filter(pk=value, user__user=request.user).exists():
            raise serializers.ValidationError("Address not found.")
        return value


# ─────────────────────────── ADMIN ORDER ───────────────────────────

class AdminOrderListSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    customer_email = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer_name', 'customer_email',
            'total', 'payment_method', 'payment_status', 'status', 'created_at'
        ]

    def get_customer_name(self, obj):
        return obj.user.get_full_name() if obj.user else 'N/A'

    def get_customer_email(self, obj):
        return obj.user.email if obj.user else 'N/A'


class AdminOrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    tracking = OrderTrackingSerializer(many=True, read_only=True)
    delivery_address = AddressSerializer(read_only=True)
    customer_name = serializers.SerializerMethodField()
    customer_email = serializers.SerializerMethodField()
    customer_phone = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer_name', 'customer_email', 'customer_phone',
            'status', 'payment_method', 'payment_status', 'receive_method', 'delivery_type', 'scheduled_at',   # ← new
            'delivery_address', 'items', 'subtotal', 'delivery_fee', 'total',
            'tracking', 'notes', 'created_at', 'updated_at'
        ]

    def get_customer_name(self, obj):
        return obj.user.get_full_name() if obj.user else 'N/A'

    def get_customer_email(self, obj):
        return obj.user.email if obj.user else 'N/A'

    def get_customer_phone(self, obj):
        return obj.user.phone if obj.user else 'N/A'


class AdminOrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[s[0] for s in Order.STATUS_CHOICES])
    note = serializers.CharField(required=False, allow_blank=True)
