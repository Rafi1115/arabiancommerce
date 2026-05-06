from django.urls import path
from . import views

urlpatterns = [
    path('admin/dashboard/stats/', views.DashboardStatsView.as_view(), name='admin-dashboard-stats'),
    path('admin/dashboard/sales/', views.SalesPerformanceView.as_view(), name='admin-dashboard-sales'),
    path('admin/dashboard/top-inventory/', views.TopInventoryView.as_view(), name='admin-dashboard-top-inventory'),
    path('admin/dashboard/recent-orders/', views.RecentOrdersView.as_view(), name='admin-dashboard-recent-orders'),
]
