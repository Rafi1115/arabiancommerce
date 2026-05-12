from rest_framework import serializers
from .models import Product, CutType, ProductCutType, ProductImage, ProductPackagingType, Inventory, InventoryLog, PackagingType
from apps.categories.serializers import CategorySerializer, PackagingTypeSerializer, SubCategorySerializer


class CutTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CutType
        fields = ['id', 'name', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class CutTypeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CutType
        fields = ['name', 'status']

    def validate_name(self, value):
        if CutType.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Cut type with this name already exists.")
        return value


class CutTypeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CutType
        fields = ['name', 'status']

    def validate_name(self, value):
        if CutType.objects.filter(name__iexact=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("Cut type with this name already exists.")
        return value


class ProductCutTypeSerializer(serializers.ModelSerializer):
    cut_type = CutTypeSerializer(read_only=True)
    cut_type_id = serializers.PrimaryKeyRelatedField(
        queryset=CutType.objects.all(),
        source='cut_type',
        write_only=True
    )

    class Meta:
        model = ProductCutType
        fields = ['id', 'cut_type', 'cut_type_id']


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


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_primary', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProductListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    subcategory = SubCategorySerializer(read_only=True)
    stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'sku', 'category', 'subcategory', 'price', 'image', 'rating', 'rating_count', 'notes_enabled', 'stock', 'status']

    def get_stock(self, obj):
        try:
            return float(obj.inventory.stock)
        except Inventory.DoesNotExist:
            return 0
        

class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    subcategory = SubCategorySerializer(read_only=True)
    cut_types = ProductCutTypeSerializer(many=True, read_only=True)
    packaging_types = ProductPackagingTypeSerializer(many=True, read_only=True)
    inventory = InventorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'category', 'subcategory', 'price', 'description',
            'image', 'images', 'rating', 'rating_count', 'notes_enabled', 'cut_types',
            'packaging_types', 'inventory', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'sku', 'rating', 'rating_count', 'created_at', 'updated_at']


class ProductCreateSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(write_only=True)
    subcategory_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    cut_type_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    packaging_type_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    initial_stock = serializers.DecimalField(max_digits=10, decimal_places=2, write_only=True, required=False, default=0)
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Product
        fields = [
            'name', 'category_id', 'subcategory_id', 'price', 'description', 'image',
            'notes_enabled', 'cut_type_ids', 'packaging_type_ids', 'initial_stock', 'status'
        ]

    def validate_category_id(self, value):
        from apps.categories.models import Category
        if not Category.objects.filter(pk=value, status=True).exists():
            raise serializers.ValidationError("Category not found or inactive.")
        return value

    def validate_subcategory_id(self, value):
        if value is None:
            return value
        from apps.categories.models import SubCategory
        if not SubCategory.objects.filter(pk=value, status=True).exists():
            raise serializers.ValidationError("SubCategory not found or inactive.")
        return value

    def validate_cut_type_ids(self, value):
        for cid in value:
            if not CutType.objects.filter(pk=cid, status=True).exists():
                raise serializers.ValidationError(f"Cut type {cid} not found or inactive.")
        return value

    def validate_packaging_type_ids(self, value):
        from apps.categories.models import PackagingType
        for pid in value:
            if not PackagingType.objects.filter(pk=pid, status=True).exists():
                raise serializers.ValidationError(f"Packaging type {pid} not found or inactive.")
        return value

    def create(self, validated_data):
        from apps.categories.models import Category, SubCategory, PackagingType

        cut_type_ids = validated_data.pop('cut_type_ids', [])
        packaging_type_ids = validated_data.pop('packaging_type_ids', [])
        initial_stock = validated_data.pop('initial_stock', 0)
        category_id = validated_data.pop('category_id')
        subcategory_id = validated_data.pop('subcategory_id', None)

        category = Category.objects.get(pk=category_id)
        subcategory = SubCategory.objects.get(pk=subcategory_id) if subcategory_id else None

        product = Product.objects.create(category=category, subcategory=subcategory, **validated_data)

        for ct_id in cut_type_ids:
            ct = CutType.objects.get(pk=ct_id)
            ProductCutType.objects.create(product=product, cut_type=ct)

        for pt_id in packaging_type_ids:
            pt = PackagingType.objects.get(pk=pt_id)
            ProductPackagingType.objects.create(product=product, packaging_type=pt)

        Inventory.objects.create(product=product, stock=initial_stock)
        return product


class ProductUpdateSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(write_only=True, required=False)
    subcategory_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Product
        fields = ['name', 'category_id', 'subcategory_id', 'price', 'description', 'image', 'notes_enabled', 'status']

    def validate_category_id(self, value):
        from apps.categories.models import Category
        if not Category.objects.filter(pk=value, status=True).exists():
            raise serializers.ValidationError("Category not found or inactive.")
        return value

    def update(self, instance, validated_data):
        from apps.categories.models import Category, SubCategory
        category_id = validated_data.pop('category_id', None)
        subcategory_id = validated_data.pop('subcategory_id', None)
        if category_id:
            instance.category = Category.objects.get(pk=category_id)
        if subcategory_id is not None:
            instance.subcategory = SubCategory.objects.get(pk=subcategory_id) if subcategory_id else None
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
