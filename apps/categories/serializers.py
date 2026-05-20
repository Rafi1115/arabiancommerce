from rest_framework import serializers
from .models import Category, SubCategory, PackagingType


class SubCategorySerializer(serializers.ModelSerializer):
    item_count = serializers.ReadOnlyField()

    class Meta:
        model = SubCategory
        fields = ['id', 'category', 'name', 'icon', 'item_count', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class SubCategoryCreateSerializer(serializers.ModelSerializer):
    icon = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = SubCategory
        fields = ['category', 'name', 'icon', 'status']

    def validate_name(self, value):
        if SubCategory.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("SubCategory with this name already exists.")
        return value


class SubCategoryUpdateSerializer(serializers.ModelSerializer):
    icon = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = SubCategory
        fields = ['category', 'name', 'icon', 'status']

    def validate_name(self, value):
        if SubCategory.objects.filter(name__iexact=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("SubCategory with this name already exists.")
        return value


class CategorySerializer(serializers.ModelSerializer):
    item_count = serializers.ReadOnlyField()
    image = serializers.ImageField(required=False)
    subcategories = SubCategorySerializer(many=True, read_only=True)  # nested

    class Meta:
        model = Category
        fields = ['id', 'name', 'subtitle', 'image', 'item_count', 'status', 'subcategories', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'item_count']


class CategoryCreateSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)  # icon → image

    class Meta:
        model = Category
        fields = ['name', 'subtitle', 'image', 'status']

    def validate_name(self, value):
        if Category.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Category with this name already exists.")
        return value


class CategoryUpdateSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Category
        fields = ['name', 'subtitle', 'image', 'status']

    def validate_name(self, value):
        if Category.objects.filter(name__iexact=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("Category with this name already exists.")
        return value


# PackagingType serializers unchanged
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
        if PackagingType.objects.filter(name__iexact=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("Packaging type with this name already exists.")
        return value