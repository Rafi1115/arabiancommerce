from django.db import models

class Document(models.Model):
    """
    Terms & Conditions, Privacy Policy, Refund Policy documents
    """
    TITLE_CHOICES = [
        ("terms-and-conditions", "Terms & Conditions"),
        ("privacy-policy", "Privacy Policy"),
        ("refund-policy", "Refund & Cancellation Policy"),
    ]
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, choices=TITLE_CHOICES)
    content = models.TextField(help_text="Support markdown content for formatting")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["title"]


class FAQ(models.Model):
    """
    Frequently Asked Questions
    """
    CATEGORY_CHOICES = [
        ("general", "General Information"),
        ("orders", "Ordering & Delivery"),
        ("payments", "Payments & Installments (Stripe/Tabby/Tamara)"),
        ("refunds", "Refunds & Cancellations"),
    ]
    question = models.CharField(max_length=255)
    answer = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="general")
    sort_order = models.PositiveIntegerField(default=0, help_text="Order in which question is shown")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.question

    class Meta:
        ordering = ["category", "sort_order", "created_at"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
