from rest_framework import serializers
from .models import Category, PackagingType


class CategorySerializer(serializers.ModelSerializer):
    item_count = serializers.ReadOnlyField()
    icon = serializers.ImageField(required=False)

    class Meta:
        model = Category
        fields = ['id', 'name', 'icon', 'item_count', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'item_count']


class CategoryCreateSerializer(serializers.ModelSerializer):
    icon = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Category
        fields = ['name', 'icon', 'status']

    def validate_name(self, value):
        if Category.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Category with this name already exists.")
        return value


class CategoryUpdateSerializer(serializers.ModelSerializer):
    icon = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Category
        fields = ['name', 'icon', 'status']

    def validate_name(self, value):
        instance = self.instance
        if Category.objects.filter(name__iexact=value).exclude(pk=instance.pk).exists():
            raise serializers.ValidationError("Category with this name already exists.")
        return value


class PackagingTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackagingType
        fields = ['id', 'name', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class PackagingTypeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackagingType
        fields = ['name', 'status']

    def validate_name(self, value):
        if PackagingType.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Packaging type with this name already exists.")
        return value


class PackagingTypeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackagingType
        fields = ['name', 'status']

    def validate_name(self, value):
        instance = self.instance
        if PackagingType.objects.filter(name__iexact=value).exclude(pk=instance.pk).exists():
            raise serializers.ValidationError("Packaging type with this name already exists.")
        return value
