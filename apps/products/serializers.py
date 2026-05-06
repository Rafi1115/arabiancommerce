from rest_framework import serializers
from .models import Product, CutType, ProductPackagingType, Inventory, InventoryLog
from apps.categories.serializers import CategorySerializer, PackagingTypeSerializer


class CutTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CutType
        fields = ['id', 'name']


class ProductPackagingTypeSerializer(serializers.ModelSerializer):
    packaging_type = PackagingTypeSerializer(read_only=True)
    packaging_type_id = serializers.PrimaryKeyRelatedField(
        queryset=__import__('apps.categories.models', fromlist=['PackagingType']).PackagingType.objects.all(),
        source='packaging_type',
        write_only=True
    )

    class Meta:
        model = ProductPackagingType
        fields = ['id', 'packaging_type', 'packaging_type_id']


class InventorySerializer(serializers.ModelSerializer):
    available_stock = serializers.ReadOnlyField()

    class Meta:
        model = Inventory
        fields = ['id', 'stock', 'reserved', 'preorder', 'in_transit', 'available_stock', 'updated_at']
        read_only_fields = ['id', 'updated_at', 'available_stock']


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    category = CategorySerializer(read_only=True)
    stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'sku', 'category', 'price', 'image', 'rating', 'rating_count', 'stock', 'status']

    def get_stock(self, obj):
        try:
            return float(obj.inventory.stock)
        except Inventory.DoesNotExist:
            return 0


class ProductDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer including cut types, packaging, inventory"""
    category = CategorySerializer(read_only=True)
    cut_types = CutTypeSerializer(many=True, read_only=True)
    packaging_types = ProductPackagingTypeSerializer(many=True, read_only=True)
    inventory = InventorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'category', 'price', 'description',
            'image', 'rating', 'rating_count', 'cut_types', 'packaging_types',
            'inventory', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'sku', 'rating', 'rating_count', 'created_at', 'updated_at']


class ProductCreateSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(write_only=True)
    cut_types = serializers.ListField(
        child=serializers.CharField(max_length=100),
        write_only=True,
        required=False
    )
    packaging_type_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    initial_stock = serializers.DecimalField(
        max_digits=10, decimal_places=2,
        write_only=True, required=False, default=0
    )
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Product
        fields = [
            'name', 'category_id', 'price', 'description', 'image',
            'cut_types', 'packaging_type_ids', 'initial_stock', 'status'
        ]

    def validate_category_id(self, value):
        from apps.categories.models import Category
        if not Category.objects.filter(pk=value, status=True).exists():
            raise serializers.ValidationError("Category not found or inactive.")
        return value

    def validate_packaging_type_ids(self, value):
        from apps.categories.models import PackagingType
        for pid in value:
            if not PackagingType.objects.filter(pk=pid, status=True).exists():
                raise serializers.ValidationError(f"Packaging type {pid} not found or inactive.")
        return value

    def create(self, validated_data):
        from apps.categories.models import Category, PackagingType

        cut_types_data = validated_data.pop('cut_types', [])
        packaging_type_ids = validated_data.pop('packaging_type_ids', [])
        initial_stock = validated_data.pop('initial_stock', 0)
        category_id = validated_data.pop('category_id')

        category = Category.objects.get(pk=category_id)
        product = Product.objects.create(category=category, **validated_data)

        # Create cut types
        for ct_name in cut_types_data:
            CutType.objects.create(product=product, name=ct_name)

        # Create packaging type associations
        for pt_id in packaging_type_ids:
            pt = PackagingType.objects.get(pk=pt_id)
            ProductPackagingType.objects.create(product=product, packaging_type=pt)

        # Create inventory record
        Inventory.objects.create(product=product, stock=initial_stock)

        return product


class ProductUpdateSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(write_only=True, required=False)
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Product
        fields = ['name', 'category_id', 'price', 'description', 'image', 'status']

    def validate_category_id(self, value):
        from apps.categories.models import Category
        if not Category.objects.filter(pk=value, status=True).exists():
            raise serializers.ValidationError("Category not found or inactive.")
        return value

    def update(self, instance, validated_data):
        from apps.categories.models import Category
        category_id = validated_data.pop('category_id', None)
        if category_id:
            instance.category = Category.objects.get(pk=category_id)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class InventoryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = ['stock', 'reserved', 'preorder', 'in_transit']


# Admin inventory list serializer (shows product info alongside inventory)
class AdminInventorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.ImageField(source='product.image', read_only=True)
    sku = serializers.CharField(source='product.sku', read_only=True)
    category = serializers.CharField(source='product.category.name', read_only=True)
    price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    available_stock = serializers.ReadOnlyField()

    class Meta:
        model = Inventory
        fields = [
            'id', 'product_name', 'product_image', 'sku', 'category', 'price',
            'stock', 'reserved', 'preorder', 'in_transit', 'available_stock', 'updated_at'
        ]
