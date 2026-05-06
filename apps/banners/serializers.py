from rest_framework import serializers
from .models import Banner


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = ['id', 'headline', 'tagline', 'call_to_action', 'image', 'is_active', 'order', 'created_at']
        read_only_fields = ['id', 'created_at']


class BannerCreateSerializer(serializers.ModelSerializer):
    image = serializers.ImageField()

    class Meta:
        model = Banner
        fields = ['headline', 'tagline', 'call_to_action', 'image', 'is_active', 'order']
