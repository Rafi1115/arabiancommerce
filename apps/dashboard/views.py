from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta

from apps.core.utils.mixins import BaseResponseMixin
from apps.orders.models import Order
from apps.accounts.models import UserProfile
from apps.products.models import Inventory


class DashboardStatsView(BaseResponseMixin, APIView):
    """
    GET /api/admin/dashboard/stats/
    Returns: total customers, today's orders, total revenue, total orders
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            today = timezone.now().date()

            total_customers = UserProfile.objects.count()
            today_orders = Order.objects.filter(created_at__date=today).count()
            total_revenue = Order.objects.filter(
                status='delivered'
            ).aggregate(total=Sum('total'))['total'] or 0
            total_orders = Order.objects.count()

            return self.success_response(data={
                'total_customers': total_customers,
                'today_orders': today_orders,
                'total_revenue': float(total_revenue),
                'total_orders': total_orders,
            })
        except Exception as exc:
            return self.handle_exception(exc)


class SalesPerformanceView(BaseResponseMixin, APIView):
    """
    GET /api/admin/dashboard/sales/?period=30   → last N days monthly aggregation
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            period = int(request.query_params.get('period', 30))
            since = timezone.now() - timedelta(days=period * 12)  # ~12 months back

            sales = Order.objects.filter(
                created_at__gte=since,
                status='delivered'
            ).annotate(
                month=TruncMonth('created_at')
            ).values('month').annotate(
                revenue=Sum('total'),
                order_count=Count('id')
            ).order_by('month')

            data = [
                {
                    'month': entry['month'].strftime('%b'),
                    'revenue': float(entry['revenue'] or 0),
                    'order_count': entry['order_count'],
                }
                for entry in sales
            ]
            return self.success_response(data=data)
        except Exception as exc:
            return self.handle_exception(exc)


class TopInventoryView(BaseResponseMixin, APIView):
    """
    GET /api/admin/dashboard/top-inventory/
    Returns top products by stock level
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            top = Inventory.objects.select_related('product').order_by('-stock')[:5]
            data = [
                {
                    'product_id': inv.product.pk,
                    'product_name': inv.product.name,
                    'product_image': request.build_absolute_uri(inv.product.image.url) if inv.product.image else None,
                    'stock': float(inv.stock),
                }
                for inv in top
            ]
            return self.success_response(data=data)
        except Exception as exc:
            return self.handle_exception(exc)


class RecentOrdersView(BaseResponseMixin, APIView):
    """
    GET /api/admin/dashboard/recent-orders/
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            from apps.orders.serializers import AdminOrderListSerializer
            orders = Order.objects.select_related('user').order_by('-created_at')[:10]
            serializer = AdminOrderListSerializer(orders, many=True)
            return self.success_response(data=serializer.data)
        except Exception as exc:
            return self.handle_exception(exc)
