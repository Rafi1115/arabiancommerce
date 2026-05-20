from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    subtitle = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='categories/images/', null=True, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name if self.name else "Untitled Category"

    @property
    def item_count(self):
        return self.products.filter(status=True).count()
    


class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100, blank=True, null=True)
    icon = models.ImageField(upload_to='subcategories/icons/', null=True, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'SubCategories'
        ordering = ['name']

    def __str__(self):
        return self.name if self.name else "Untitled SubCategory"

    @property
    def item_count(self):
        return self.products.filter(status=True).count()


class PackagingType(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name if self.name else "Untitled Packaging Type"
