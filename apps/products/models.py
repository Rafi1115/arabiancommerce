from django.db import models
from apps.categories.models import Category, PackagingType, SubCategory


class CutType(models.Model):
    name = models.CharField(max_length=100)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ProductCutType(models.Model):
    """Per-product cut type linked to global CutType"""
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='cut_types')
    cut_type = models.ForeignKey(CutType, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('product', 'cut_type')

    def __str__(self):
        return f"{self.product.name} - {self.cut_type.name}"


class ProductPackagingType(models.Model):
    """Per-product packaging options linked to global PackagingType"""
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='packaging_types')
    packaging_type = models.ForeignKey(PackagingType, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('product', 'packaging_type')

    def __str__(self):
        return f"{self.product.name} - {self.packaging_type.name}"


class Product(models.Model):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=50, unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')  # optional
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    rating_count = models.PositiveIntegerField(default=0)
    notes_enabled = models.BooleanField(default=False)  # client controls per-product note
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.sku:
            prefix = self.name[:3].upper() if self.name else 'PRD'
            import random
            self.sku = f"{prefix}-{random.randint(100, 999)}"
        super().save(*args, **kwargs)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - image {self.pk}"

    def save(self, *args, **kwargs):
        # if this is set as primary, unset others
        if self.is_primary:
            ProductImage.objects.filter(product=self.product, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class Inventory(models.Model):
    """Tracks stock levels for a product"""
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='inventory')
    stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)       # total stock in kg
    reserved = models.DecimalField(max_digits=10, decimal_places=2, default=0)    # reserved for pending orders
    preorder = models.DecimalField(max_digits=10, decimal_places=2, default=0)    # pre-ordered qty
    in_transit = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # in transit
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Inventories'

    def __str__(self):
        return f"Inventory: {self.product.name}"

    @property
    def available_stock(self):
        return self.stock - self.reserved


class InventoryLog(models.Model):
    """Audit trail for inventory changes"""
    ACTION_CHOICES = [
        ('add', 'Stock Added'),
        ('remove', 'Stock Removed'),
        ('reserve', 'Stock Reserved'),
        ('release', 'Reservation Released'),
    ]

    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.inventory.product.name} - {self.action} {self.quantity}"
