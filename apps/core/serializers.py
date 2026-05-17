from rest_framework import serializers
from .models import Document, FAQ

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["id", "title", "slug", "content", "updated_at"]


class FAQSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = FAQ
        fields = ["id", "question", "answer", "category", "category_display", "sort_order"]
