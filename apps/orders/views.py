from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from apps.core.utils.mixins import BaseResponseMixin
from .models import Cart, CartItem, Order, OrderItem, OrderTracking
from .serializers import (
    CartSerializer,
    CartItemAddSerializer,
    OrderListSerializer,
    OrderDetailSerializer,
    CheckoutSerializer,
    AdminOrderListSerializer,
    AdminOrderDetailSerializer,
    AdminOrderStatusUpdateSerializer,
)

DELIVERY_FEE = Decimal('89')


def get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


# ─────────────────────────── CART VIEWS ───────────────────────────

class CartView(BaseResponseMixin, APIView):
    """
    GET /api/cart/   → get my cart
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            cart = get_or_create_cart(request.user)
            serializer = CartSerializer(cart, context={'request': request})
            return self.success_response(data=serializer.data)
        except Exception as exc:
            return self.handle_exception(exc)


class CartAddItemView(BaseResponseMixin, APIView):
    """
    POST /api/cart/add/
    Body: product_id, cut_type_id (optional), packaging_type_id (optional), quantity
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            serializer = CartItemAddSerializer(data=request.data)
            if not serializer.is_valid():
                return self.error_response(
                    message="Validation failed",
                    error_code="VALIDATION_ERROR",
                    errors=serializer.errors
                )

            data = serializer.validated_data
            cart = get_or_create_cart(request.user)

            from apps.products.models import Product, CutType, ProductPackagingType
            product = Product.objects.get(pk=data['product_id'])
            cut_type = CutType.objects.get(pk=data['cut_type_id']) if data.get('cut_type_id') else None
            packaging_type = ProductPackagingType.objects.get(pk=data['packaging_type_id']) if data.get('packaging_type_id') else None

            # Check if same combo already in cart → just update quantity
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                cut_type=cut_type,
                packaging_type=packaging_type,
                defaults={'quantity': data['quantity']}
            )
            if not created:
                cart_item.quantity += data['quantity']
                cart_item.save()

            cart.refresh_from_db()
            return self.success_response(
                data=CartSerializer(cart, context={'request': request}).data,
                message="Item added to cart"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class CartUpdateItemView(BaseResponseMixin, APIView):
    """
    PATCH  /api/cart/items/<item_id>/   → update quantity
    DELETE /api/cart/items/<item_id>/   → remove item
    """
    permission_classes = [IsAuthenticated]

    def get_item(self, request, item_id):
        try:
            cart = get_or_create_cart(request.user)
            return CartItem.objects.get(pk=item_id, cart=cart)
        except CartItem.DoesNotExist:
            return None

    def patch(self, request, item_id):
        try:
            item = self.get_item(request, item_id)
            if not item:
                return self.not_found_response("Cart item not found")

            quantity = request.data.get('quantity')
            if not quantity or int(quantity) < 1:
                return self.bad_request_response("Quantity must be at least 1")

            item.quantity = int(quantity)
            item.save()

            cart = get_or_create_cart(request.user)
            return self.success_response(
                data=CartSerializer(cart, context={'request': request}).data,
                message="Cart updated"
            )
        except Exception as exc:
            return self.handle_exception(exc)

    def delete(self, request, item_id):
        try:
            item = self.get_item(request, item_id)
            if not item:
                return self.not_found_response("Cart item not found")
            item.delete()
            cart = get_or_create_cart(request.user)
            return self.success_response(
                data=CartSerializer(cart, context={'request': request}).data,
                message="Item removed from cart"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class CartClearView(BaseResponseMixin, APIView):
    """
    DELETE /api/cart/clear/
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        try:
            cart = get_or_create_cart(request.user)
            cart.items.all().delete()
            return self.success_response(message="Cart cleared")
        except Exception as exc:
            return self.handle_exception(exc)


# ─────────────────────────── CHECKOUT ───────────────────────────

class CheckoutView(BaseResponseMixin, APIView):
    """
    POST /api/checkout/
    Converts cart → order. Clears cart after.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            cart = get_or_create_cart(request.user)
            if not cart.items.exists():
                return self.bad_request_response("Your cart is empty")

            serializer = CheckoutSerializer(data=request.data, context={'request': request})
            if not serializer.is_valid():
                return self.error_response(
                    message="Validation failed",
                    error_code="VALIDATION_ERROR",
                    errors=serializer.errors
                )

            data = serializer.validated_data
            from apps.accounts.models import Address
            address = Address.objects.get(pk=data['address_id'], user__user=request.user)

            subtotal = cart.total
            total = subtotal + DELIVERY_FEE

            # Create order
            order = Order.objects.create(
                user=request.user,
                delivery_address=address,
                payment_method=data['payment_method'],
                subtotal=subtotal,
                delivery_fee=DELIVERY_FEE,
                total=total,
                notes=data.get('notes', ''),
            )

            # Create order items from cart (snapshot prices)
            for cart_item in cart.items.select_related('product', 'cut_type', 'packaging_type__packaging_type'):
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    product_name=cart_item.product.name,
                    product_image=cart_item.product.image,
                    cut_type_name=cart_item.cut_type.name if cart_item.cut_type else '',
                    packaging_type_name=cart_item.packaging_type.packaging_type.name if cart_item.packaging_type else '',
                    quantity=cart_item.quantity,
                    unit_price=cart_item.product.price,
                    subtotal=cart_item.subtotal,
                )

            # Initial tracking entry
            OrderTracking.objects.create(
                order=order,
                status='order_confirmed',
                note='Order placed successfully'
            )

            # Clear cart
            cart.items.all().delete()

            return self.created_response(
                data=OrderDetailSerializer(order, context={'request': request}).data,
                message="Order placed successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


# ─────────────────────────── CUSTOMER ORDER VIEWS ───────────────────────────

class MyOrderListView(BaseResponseMixin, APIView):
    """
    GET /api/orders/          → my orders
    GET /api/orders/history/  → completed/cancelled orders
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            orders = Order.objects.filter(user=request.user)
            mode = request.query_params.get('mode')
            if mode == 'history':
                orders = orders.filter(status__in=['delivered', 'cancelled'])
            else:
                orders = orders.exclude(status__in=['delivered', 'cancelled'])

            serializer = OrderListSerializer(orders, many=True, context={'request': request})
            return self.success_response(data=serializer.data)
        except Exception as exc:
            return self.handle_exception(exc)


class MyOrderDetailView(BaseResponseMixin, APIView):
    """
    GET /api/orders/<pk>/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            try:
                order = Order.objects.prefetch_related('items', 'tracking').get(pk=pk, user=request.user)
            except Order.DoesNotExist:
                return self.not_found_response("Order not found")
            serializer = OrderDetailSerializer(order, context={'request': request})
            return self.success_response(data=serializer.data)
        except Exception as exc:
            return self.handle_exception(exc)


# ─────────────────────────── ADMIN ORDER VIEWS ───────────────────────────

class AdminOrderListView(BaseResponseMixin, APIView):
    """
    GET /api/admin/orders/
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            orders = Order.objects.select_related('user', 'delivery_address').all()
            status = request.query_params.get('status')
            search = request.query_params.get('search')
            payment_method = request.query_params.get('payment_method')

            if status:
                orders = orders.filter(status=status)
            if payment_method:
                orders = orders.filter(payment_method=payment_method)
            if search:
                orders = orders.filter(order_number__icontains=search) | \
                         orders.filter(user__first_name__icontains=search) | \
                         orders.filter(user__last_name__icontains=search)

            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 10))
            start = (page - 1) * page_size
            end = start + page_size
            total = orders.count()

            serializer = AdminOrderListSerializer(orders[start:end], many=True)
            return self.success_response(data={
                'results': serializer.data,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size,
            })
        except Exception as exc:
            return self.handle_exception(exc)


class AdminOrderDetailView(BaseResponseMixin, APIView):
    """
    GET   /api/admin/orders/<pk>/
    PATCH /api/admin/orders/<pk>/update-status/
    """
    permission_classes = [IsAdminUser]

    def get_object(self, pk):
        try:
            return Order.objects.prefetch_related('items', 'tracking').select_related(
                'user', 'delivery_address'
            ).get(pk=pk)
        except Order.DoesNotExist:
            return None

    def get(self, request, pk):
        try:
            order = self.get_object(pk)
            if not order:
                return self.not_found_response("Order not found")
            serializer = AdminOrderDetailSerializer(order, context={'request': request})
            return self.success_response(data=serializer.data)
        except Exception as exc:
            return self.handle_exception(exc)

    def patch(self, request, pk):
        try:
            order = self.get_object(pk)
            if not order:
                return self.not_found_response("Order not found")

            serializer = AdminOrderStatusUpdateSerializer(data=request.data)
            if not serializer.is_valid():
                return self.error_response(
                    message="Validation failed",
                    error_code="VALIDATION_ERROR",
                    errors=serializer.errors
                )

            data = serializer.validated_data
            order.status = data['status']
            order.save()

            # Log tracking entry
            OrderTracking.objects.create(
                order=order,
                status=data['status'],
                note=data.get('note', '')
            )

            return self.updated_response(
                data=AdminOrderDetailSerializer(order, context={'request': request}).data,
                message=f"Order status updated to {data['status']}"
            )
        except Exception as exc:
            return self.handle_exception(exc)
