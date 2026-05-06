from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from apps.core.utils.mixins import BaseResponseMixin
from .models import Category, PackagingType
from .serializers import (
    CategorySerializer,
    CategoryCreateSerializer,
    CategoryUpdateSerializer,
    PackagingTypeSerializer,
    PackagingTypeCreateSerializer,
    PackagingTypeUpdateSerializer,
)


# ─────────────────────────── CATEGORY VIEWS ───────────────────────────

class CategoryListView(BaseResponseMixin, APIView):
    """
    GET  /api/categories/          → public, list all active categories
    GET  /api/admin/categories/    → admin, list all (active + inactive)
    """

    def get_permissions(self):
        if self.request.path.startswith('/api/admin/'):
            return [IsAdminUser()]
        return [AllowAny()]

    def get(self, request):
        try:
            if request.path.startswith('/api/admin/'):
                categories = Category.objects.all()
            else:
                categories = Category.objects.filter(status=True)

            serializer = CategorySerializer(categories, many=True, context={'request': request})
            return self.success_response(data=serializer.data)
        except Exception as exc:
            return self.handle_exception(exc)


class CategoryCreateView(BaseResponseMixin, APIView):
    """
    POST /api/admin/categories/create/  → admin only
    """
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        try:
            serializer = CategoryCreateSerializer(data=request.data, context={'request': request})
            if not serializer.is_valid():
                return self.error_response(
                    message="Validation failed",
                    error_code="VALIDATION_ERROR",
                    errors=serializer.errors
                )
            category = serializer.save()
            return self.created_response(
                data=CategorySerializer(category, context={'request': request}).data,
                message="Category created successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class CategoryDetailView(BaseResponseMixin, APIView):
    """
    GET    /api/admin/categories/<pk>/        → admin
    PATCH  /api/admin/categories/<pk>/update/ → admin
    DELETE /api/admin/categories/<pk>/delete/ → admin
    """
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self, pk):
        try:
            return Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return None

    def get(self, request, pk):
        try:
            category = self.get_object(pk)
            if not category:
                return self.not_found_response("Category not found")
            serializer = CategorySerializer(category, context={'request': request})
            return self.success_response(data=serializer.data)
        except Exception as exc:
            return self.handle_exception(exc)

    def patch(self, request, pk):
        try:
            category = self.get_object(pk)
            if not category:
                return self.not_found_response("Category not found")
            serializer = CategoryUpdateSerializer(
                category, data=request.data, partial=True, context={'request': request}
            )
            if not serializer.is_valid():
                return self.error_response(
                    message="Validation failed",
                    error_code="VALIDATION_ERROR",
                    errors=serializer.errors
                )
            category = serializer.save()
            return self.updated_response(
                data=CategorySerializer(category, context={'request': request}).data,
                message="Category updated successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)

    def delete(self, request, pk):
        try:
            category = self.get_object(pk)
            if not category:
                return self.not_found_response("Category not found")
            category.delete()
            return self.deleted_response("Category deleted successfully")
        except Exception as exc:
            return self.handle_exception(exc)


class CategoryToggleStatusView(BaseResponseMixin, APIView):
    """
    PATCH /api/admin/categories/<pk>/toggle-status/
    """
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        try:
            try:
                category = Category.objects.get(pk=pk)
            except Category.DoesNotExist:
                return self.not_found_response("Category not found")

            category.status = not category.status
            category.save()
            status_label = "activated" if category.status else "deactivated"
            return self.success_response(
                data=CategorySerializer(category, context={'request': request}).data,
                message=f"Category {status_label} successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


# ─────────────────────────── PACKAGING TYPE VIEWS ───────────────────────────

class PackagingTypeListView(BaseResponseMixin, APIView):
    """
    GET /api/packaging-types/       → public
    GET /api/admin/packaging-types/ → admin (all)
    """

    def get_permissions(self):
        if self.request.path.startswith('/api/admin/'):
            return [IsAdminUser()]
        return [AllowAny()]

    def get(self, request):
        try:
            if request.path.startswith('/api/admin/'):
                packaging_types = PackagingType.objects.all()
            else:
                packaging_types = PackagingType.objects.filter(status=True)

            serializer = PackagingTypeSerializer(packaging_types, many=True)
            return self.success_response(data=serializer.data)
        except Exception as exc:
            return self.handle_exception(exc)


class PackagingTypeCreateView(BaseResponseMixin, APIView):
    """
    POST /api/admin/packaging-types/create/
    """
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            serializer = PackagingTypeCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return self.error_response(
                    message="Validation failed",
                    error_code="VALIDATION_ERROR",
                    errors=serializer.errors
                )
            packaging_type = serializer.save()
            return self.created_response(
                data=PackagingTypeSerializer(packaging_type).data,
                message="Packaging type created successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class PackagingTypeDetailView(BaseResponseMixin, APIView):
    """
    GET    /api/admin/packaging-types/<pk>/
    PATCH  /api/admin/packaging-types/<pk>/update/
    DELETE /api/admin/packaging-types/<pk>/delete/
    """
    permission_classes = [IsAdminUser]

    def get_object(self, pk):
        try:
            return PackagingType.objects.get(pk=pk)
        except PackagingType.DoesNotExist:
            return None

    def get(self, request, pk):
        try:
            pt = self.get_object(pk)
            if not pt:
                return self.not_found_response("Packaging type not found")
            return self.success_response(data=PackagingTypeSerializer(pt).data)
        except Exception as exc:
            return self.handle_exception(exc)

    def patch(self, request, pk):
        try:
            pt = self.get_object(pk)
            if not pt:
                return self.not_found_response("Packaging type not found")
            serializer = PackagingTypeUpdateSerializer(pt, data=request.data, partial=True)
            if not serializer.is_valid():
                return self.error_response(
                    message="Validation failed",
                    error_code="VALIDATION_ERROR",
                    errors=serializer.errors
                )
            pt = serializer.save()
            return self.updated_response(
                data=PackagingTypeSerializer(pt).data,
                message="Packaging type updated successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)

    def delete(self, request, pk):
        try:
            pt = self.get_object(pk)
            if not pt:
                return self.not_found_response("Packaging type not found")
            pt.delete()
            return self.deleted_response("Packaging type deleted successfully")
        except Exception as exc:
            return self.handle_exception(exc)


class PackagingTypeToggleStatusView(BaseResponseMixin, APIView):
    """
    PATCH /api/admin/packaging-types/<pk>/toggle-status/
    """
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        try:
            try:
                pt = PackagingType.objects.get(pk=pk)
            except PackagingType.DoesNotExist:
                return self.not_found_response("Packaging type not found")

            pt.status = not pt.status
            pt.save()
            status_label = "activated" if pt.status else "deactivated"
            return self.success_response(
                data=PackagingTypeSerializer(pt).data,
                message=f"Packaging type {status_label} successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)
