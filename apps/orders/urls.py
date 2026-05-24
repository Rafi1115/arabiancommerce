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
    path('pickup-locations/', views.PickupLocationListView.as_view(), name='pickup-locations'),

    # Orders
    path('orders/', views.MyOrderListView.as_view(), name='my-orders'),
    path('orders/<int:pk>/', views.MyOrderDetailView.as_view(), name='my-order-detail'),
    path('orders/<int:pk>/cancel/', views.CancelOrderView.as_view(), name='order-cancel'),
]

# Admin URLs
urlpatterns += [
    path('admin/orders/', views.AdminOrderListView.as_view(), name='admin-order-list'),
    path('admin/orders/<int:pk>/', views.AdminOrderDetailView.as_view(), name='admin-order-detail'),
    path('admin/orders/<int:pk>/update-status/', views.AdminOrderDetailView.as_view(), name='admin-order-update-status'),
    path('admin/pickup-locations/', views.AdminPickupLocationListView.as_view(), name='admin-pickup-location-list-create'),
    path('admin/pickup-locations/<int:pk>/', views.AdminPickupLocationDetailView.as_view(), name='admin-pickup-location-detail'),
]
