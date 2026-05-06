from django.urls import path
from . import views

# Public URLs (mobile app)
urlpatterns = [
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
]

# Admin URLs (dashboard)
urlpatterns += [
    # Products
    path('admin/products/', views.AdminProductListView.as_view(), name='admin-product-list'),
    path('admin/products/create/', views.AdminProductCreateView.as_view(), name='admin-product-create'),
    path('admin/products/<int:pk>/', views.AdminProductDetailView.as_view(), name='admin-product-detail'),
    path('admin/products/<int:pk>/update/', views.AdminProductDetailView.as_view(), name='admin-product-update'),
    path('admin/products/<int:pk>/delete/', views.AdminProductDetailView.as_view(), name='admin-product-delete'),
    path('admin/products/<int:pk>/toggle-status/', views.AdminProductToggleStatusView.as_view(), name='admin-product-toggle'),

    # Cut Types
    path('admin/products/<int:pk>/cut-types/', views.ProductCutTypeView.as_view(), name='admin-product-cut-types'),
    path('admin/products/<int:pk>/cut-types/<int:ct_id>/', views.ProductCutTypeView.as_view(), name='admin-product-cut-type-delete'),

    # Inventory
    path('admin/inventory/', views.AdminInventoryListView.as_view(), name='admin-inventory-list'),
    path('admin/inventory/<int:product_pk>/', views.AdminInventoryUpdateView.as_view(), name='admin-inventory-update'),
]
