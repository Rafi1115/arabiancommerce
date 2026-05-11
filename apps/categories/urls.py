from . import views
from django.urls import path

urlpatterns = [
    # Public
    path('list/', views.CategoryListView.as_view(), name='category-list'),
    path('sub/list/', views.SubCategoryListView.as_view(), name='subcategory-list'),
    path('packaging-types/', views.PackagingTypeListView.as_view(), name='packaging-type-list'),

    # Admin - Categories
    path('admin/categories/', views.AdminCategoryListView.as_view(), name='admin-category-list'),
    path('admin/categories/create/', views.CategoryCreateView.as_view(), name='admin-category-create'),
    path('admin/categories/<int:pk>/', views.CategoryDetailView.as_view(), name='admin-category-detail'),
    path('admin/categories/<int:pk>/update/', views.CategoryDetailView.as_view(), name='admin-category-update'),
    path('admin/categories/<int:pk>/delete/', views.CategoryDetailView.as_view(), name='admin-category-delete'),
    path('admin/categories/<int:pk>/toggle-status/', views.CategoryToggleStatusView.as_view(), name='admin-category-toggle'),

    # Admin - SubCategories
    path('admin/subcategories/', views.AdminSubCategoryListView.as_view(), name='admin-subcategory-list'),
    path('admin/subcategories/create/', views.SubCategoryCreateView.as_view(), name='admin-subcategory-create'),
    path('admin/subcategories/<int:pk>/', views.SubCategoryDetailView.as_view(), name='admin-subcategory-detail'),
    path('admin/subcategories/<int:pk>/update/', views.SubCategoryDetailView.as_view(), name='admin-subcategory-update'),
    path('admin/subcategories/<int:pk>/delete/', views.SubCategoryDetailView.as_view(), name='admin-subcategory-delete'),
    path('admin/subcategories/<int:pk>/toggle-status/', views.SubCategoryToggleStatusView.as_view(), name='admin-subcategory-toggle'),

    # Admin - Packaging Types
    path('admin/packaging-types/', views.AdminPackagingTypeListView.as_view(), name='admin-packaging-list'),
    path('admin/packaging-types/create/', views.PackagingTypeCreateView.as_view(), name='admin-packaging-create'),
    path('admin/packaging-types/<int:pk>/', views.PackagingTypeDetailView.as_view(), name='admin-packaging-detail'),
    path('admin/packaging-types/<int:pk>/update/', views.PackagingTypeDetailView.as_view(), name='admin-packaging-update'),
    path('admin/packaging-types/<int:pk>/delete/', views.PackagingTypeDetailView.as_view(), name='admin-packaging-delete'),
    path('admin/packaging-types/<int:pk>/toggle-status/', views.PackagingTypeToggleStatusView.as_view(), name='admin-packaging-toggle'),
]