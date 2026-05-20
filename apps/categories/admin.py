from django.contrib import admin
from .models import Category, SubCategory, PackagingType


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'subtitle', 'status', 'created_at', 'updated_at')
    search_fields = ('name', 'subtitle')
    list_filter = ('status',)
    ordering = ('name',)


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'status', 'created_at', 'updated_at')
    search_fields = ('name', 'category__name')
    list_filter = ('status',)
    ordering = ('name',)


@admin.register(PackagingType)
class PackagingTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'created_at', 'updated_at')
    list_filter = ('status',)
