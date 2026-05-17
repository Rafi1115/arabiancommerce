from django.urls import path
from .views import (
    DocumentDetailView,
    FAQListView,
    AdminDocumentListCreateView,
    AdminDocumentDetailView,
    AdminFAQListCreateView,
    AdminFAQDetailView,
)

urlpatterns = [
    # Customer endpoints
    path("documents/<slug:slug>/", DocumentDetailView.as_view(), name="document-detail"),
    path("faqs/", FAQListView.as_view(), name="faq-list"),

    # Admin Dashboard CRUD endpoints
    path("admin/documents/", AdminDocumentListCreateView.as_view(), name="admin-document-list-create"),
    path("admin/documents/<slug:slug>/", AdminDocumentDetailView.as_view(), name="admin-document-detail"),
    path("admin/faqs/", AdminFAQListCreateView.as_view(), name="admin-faq-list-create"),
    path("admin/faqs/<int:pk>/", AdminFAQDetailView.as_view(), name="admin-faq-detail"),
]
