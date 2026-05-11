from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.BannerListView.as_view(), name='banner-list'),
]

urlpatterns += [
    path('admin/list/', views.BannerListView.as_view(), name='admin-banner-list'),
    path('admin/create/', views.BannerCreateView.as_view(), name='admin-banner-create'),
    path('admin/<int:pk>/update/', views.BannerDetailView.as_view(), name='admin-banner-update'),
    path('admin/<int:pk>/delete/', views.BannerDetailView.as_view(), name='admin-banner-delete'),
]