from django.urls import path
from . import views

# Public URLs (mobile app)
urlpatterns = [
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('packaging-types/', views.PackagingTypeListView.as_view(), name='packaging-type-list'),
]

# Admin URLs (dashboard)
urlpatterns += [
    # Categories
    path('admin/categories/', views.CategoryListView.as_view(), name='admin-category-list'),
    path('admin/categories/create/', views.CategoryCreateView.as_view(), name='admin-category-create'),
    path('admin/categories/<int:pk>/', views.CategoryDetailView.as_view(), name='admin-category-detail'),
    path('admin/categories/<int:pk>/update/', views.CategoryDetailView.as_view(), name='admin-category-update'),
    path('admin/categories/<int:pk>/delete/', views.CategoryDetailView.as_view(), name='admin-category-delete'),
    path('admin/categories/<int:pk>/toggle-status/', views.CategoryToggleStatusView.as_view(), name='admin-category-toggle'),

    # Packaging Types
    path('admin/packaging-types/', views.PackagingTypeListView.as_view(), name='admin-packaging-list'),
    path('admin/packaging-types/create/', views.PackagingTypeCreateView.as_view(), name='admin-packaging-create'),
    path('admin/packaging-types/<int:pk>/', views.PackagingTypeDetailView.as_view(), name='admin-packaging-detail'),
    path('admin/packaging-types/<int:pk>/update/', views.PackagingTypeDetailView.as_view(), name='admin-packaging-update'),
    path('admin/packaging-types/<int:pk>/delete/', views.PackagingTypeDetailView.as_view(), name='admin-packaging-delete'),
    path('admin/packaging-types/<int:pk>/toggle-status/', views.PackagingTypeToggleStatusView.as_view(), name='admin-packaging-toggle'),
]
