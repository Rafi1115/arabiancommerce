from django.contrib import admin
from .models import Document, FAQ

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("title", "content")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "category", "sort_order", "is_active", "updated_at")
    list_filter = ("category", "is_active")
    search_fields = ("question", "answer")
    list_editable = ("sort_order", "is_active")
