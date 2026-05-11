from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from apps.core.utils.mixins import BaseResponseMixin
from .models import Banner
from .serializers import BannerSerializer, BannerCreateSerializer


class BannerListView(BaseResponseMixin, APIView):
    """
    GET /api/banners/        → public, active banners only
    GET /api/admin/banners/  → admin, all banners
    """

    def get_permissions(self):
        if self.request.path.startswith('/api/admin/'):
            return [IsAdminUser()]
        return [AllowAny()]

    def get(self, request):
        try:
            if request.path.startswith('/api/admin/'):
                banners = Banner.objects.all()
            else:
                banners = Banner.objects.filter(is_active=True)
            serializer = BannerSerializer(banners, many=True, context={'request': request})
            return self.success_response(data=serializer.data)
        except Exception as exc:
            return self.handle_exception(exc)


class BannerCreateView(BaseResponseMixin, APIView):
    """
    POST /api/admin/banners/create/
    """
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        try:
            serializer = BannerCreateSerializer(data=request.data, context={'request': request})
            if not serializer.is_valid():
                return self.error_response(
                    message="Validation failed",
                    error_code="VALIDATION_ERROR",
                    errors=serializer.errors
                )
            banner = serializer.save()
            return self.created_response(
                data=BannerSerializer(banner, context={'request': request}).data,
                message="Banner created successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class BannerDetailView(BaseResponseMixin, APIView):
    """
    PATCH  /api/admin/banners/<pk>/update/
    DELETE /api/admin/banners/<pk>/delete/
    """
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self, pk):
        try:
            return Banner.objects.get(pk=pk)
        except Banner.DoesNotExist:
            return None

    def patch(self, request, pk):
        try:
            banner = self.get_object(pk)
            if not banner:
                return self.not_found_response("Banner not found")
            serializer = BannerCreateSerializer(
                banner, data=request.data, partial=True, context={'request': request}
            )
            if not serializer.is_valid():
                return self.error_response(
                    message="Validation failed",
                    error_code="VALIDATION_ERROR",
                    errors=serializer.errors
                )
            banner = serializer.save()
            return self.updated_response(
                data=BannerSerializer(banner, context={'request': request}).data,
                message="Banner updated successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)

    def delete(self, request, pk):
        try:
            banner = self.get_object(pk)
            if not banner:
                return self.not_found_response("Banner not found")
            banner.delete()
            return self.deleted_response("Banner deleted successfully")
        except Exception as exc:
            return self.handle_exception(exc)