from django.urls import path
from . import views

# Customer / mobile URLs
urlpatterns = [
    # Cart
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/add/', views.CartAddItemView.as_view(), name='cart-add'),
    path('cart/items/<int:item_id>/', views.CartUpdateItemView.as_view(), name='cart-item'),
    path('cart/clear/', views.CartClearView.as_view(), name='cart-clear'),

    # Checkout
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),

    # Orders
    path('orders/', views.MyOrderListView.as_view(), name='my-orders'),
    path('orders/<int:pk>/', views.MyOrderDetailView.as_view(), name='my-order-detail'),
]

# Admin URLs
urlpatterns += [
    path('admin/orders/', views.AdminOrderListView.as_view(), name='admin-order-list'),
    path('admin/orders/<int:pk>/', views.AdminOrderDetailView.as_view(), name='admin-order-detail'),
    path('admin/orders/<int:pk>/update-status/', views.AdminOrderDetailView.as_view(), name='admin-order-update-status'),
]
