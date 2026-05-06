from django.db import models


class Banner(models.Model):
    headline = models.CharField(max_length=255, blank=True, null=True)
    tagline = models.TextField(blank=True, null=True)
    call_to_action = models.CharField(max_length=100, blank=True, null=True)
    image = models.ImageField(upload_to='banners/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.headline if self.headline else "Untitled Banner"
