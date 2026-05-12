from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from apps.core.utils.mixins import BaseResponseMixin
from .models import Product, CutType, ProductCutType, ProductPackagingType, Inventory, ProductImage
from .serializers import (
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateSerializer,
    ProductUpdateSerializer,
    InventorySerializer,
    InventoryUpdateSerializer,
    AdminInventorySerializer,
    CutTypeSerializer,
    CutTypeCreateSerializer,
    CutTypeUpdateSerializer,
    ProductCutTypeSerializer,
    ProductPackagingTypeSerializer,
    ProductImageSerializer,
)

# ─────────────────────────── PUBLIC / MOBILE VIEWS ───────────────────────────

class ProductListView(BaseResponseMixin, APIView):
    """
    GET /api/products/                         → all active products
    GET /api/products/?category_id=<id>        → filter by category
    GET /api/products/?search=<q>              → search by name
    """
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            products = Product.objects.filter(status=True).select_related('category', 'inventory')
            category_id = request.query_params.get('category_id')
            search = request.query_params.get('search')

            if category_id:
                products = products.filter(category_id=category_id)
            if search:
                products = products.filter(name__icontains=search)

            serializer = ProductListSerializer(products, many=True, context={'request': request})
            return self.success_response(data=serializer.data)
        except Exception as exc:
            return self.handle_exception(exc)


class ProductDetailView(BaseResponseMixin, APIView):
    """
    GET /api/products/<pk>/
    """
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            try:
                product = Product.objects.select_related(
                    'category', 'inventory'
                ).prefetch_related(
                    'cut_types__cut_type', 'packaging_types__packaging_type'
                ).get(pk=pk, status=True)
            except Product.DoesNotExist:
                return self.not_found_response("Product not found")

            serializer = ProductDetailSerializer(product, context={'request': request})
            return self.success_response(data=serializer.data)
        except Exception as exc:
            return self.handle_exception(exc)


# ─────────────────────────── ADMIN VIEWS ───────────────────────────

class AdminProductListView(BaseResponseMixin, APIView):
    """
    GET /api/admin/products/   → all products with pagination
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            products = Product.objects.select_related('category', 'inventory').all()
            category_id = request.query_params.get('category_id')
            search = request.query_params.get('search')
            status = request.query_params.get('status')

            if category_id:
                products = products.filter(category_id=category_id)
            if search:
                products = products.filter(name__icontains=search)
            if status is not None:
                products = products.filter(status=status.lower() == 'true')

            # Simple pagination
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 10))
            start = (page - 1) * page_size
            end = start + page_size
            total = products.count()
            products_page = products[start:end]

            serializer = ProductListSerializer(products_page, many=True, context={'request': request})
            return self.success_response(data={
                'results': serializer.data,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size,
            })
        except Exception as exc:
            return self.handle_exception(exc)


class AdminProductCreateView(BaseResponseMixin, APIView):
    """
    POST /api/admin/products/create/
    Body: name, category_id, price, description, image,
          cut_types (list of strings), packaging_type_ids (list of ints),
          initial_stock
    """
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        try:
            serializer = ProductCreateSerializer(data=request.data, context={'request': request})
            if not serializer.is_valid():
                return self.error_response(
                    message="Validation failed",
                    error_code="VALIDATION_ERROR",
                    errors=serializer.errors
                )
            product = serializer.save()
            return self.created_response(
                data=ProductDetailSerializer(product, context={'request': request}).data,
                message="Product created successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class AdminProductDetailView(BaseResponseMixin, APIView):
    """
    GET    /api/admin/products/<pk>/
    PATCH  /api/admin/products/<pk>/update/
    DELETE /api/admin/products/<pk>/delete/
    """
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self, pk):
        try:
            return Product.objects.select_related('category', 'inventory').prefetch_related(
                'cut_types', 'packaging_types__packaging_type'
            ).get(pk=pk)
        except Product.DoesNotExist:
            return None

    def get(self, request, pk):
        try:
            product = self.get_object(pk)
            if not product:
                return self.not_found_response("Product not found")
            return self.success_response(
                data=ProductDetailSerializer(product, context={'request': request}).data
            )
        except Exception as exc:
            return self.handle_exception(exc)

    def patch(self, request, pk):
        try:
            product = self.get_object(pk)
            if not product:
                return self.not_found_response("Product not found")
            serializer = ProductUpdateSerializer(product, data=request.data, partial=True, context={'request': request})
            if not serializer.is_valid():
                return self.error_response(
                    message="Validation failed",
                    error_code="VALIDATION_ERROR",
                    errors=serializer.errors
                )
            product = serializer.save()
            return self.updated_response(
                data=ProductDetailSerializer(product, context={'request': request}).data,
                message="Product updated successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)

    def delete(self, request, pk):
        try:
            product = self.get_object(pk)
            if not product:
                return self.not_found_response("Product not found")
            product.delete()
            return self.deleted_response("Product deleted successfully")
        except Exception as exc:
            return self.handle_exception(exc)


class AdminProductToggleStatusView(BaseResponseMixin, APIView):
    """
    PATCH /api/admin/products/<pk>/toggle-status/
    """
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        try:
            try:
                product = Product.objects.get(pk=pk)
            except Product.DoesNotExist:
                return self.not_found_response("Product not found")

            product.status = not product.status
            product.save()
            status_label = "activated" if product.status else "deactivated"
            return self.success_response(
                data=ProductListSerializer(product, context={'request': request}).data,
                message=f"Product {status_label} successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


# ─────────────────────── CUT TYPE MANAGEMENT ───────────────────────

class ProductCutTypeView(BaseResponseMixin, APIView):
    """
    GET    /api/admin/products/<pk>/cut-types/
    POST   /api/admin/products/<pk>/cut-types/   → link a global cut type to a product
    DELETE /api/admin/products/<pk>/cut-types/<ct_id>/
    """
    permission_classes = [IsAdminUser]

    def get_product(self, pk):
        try:
            return Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return None

    def get(self, request, pk):
        try:
            product = self.get_product(pk)
            if not product:
                return self.not_found_response("Product not found")
            serializer = ProductCutTypeSerializer(product.cut_types.all(), many=True)
            return self.success_response(data=serializer.data)
        except Exception as exc:
            return self.handle_exception(exc)

    def post(self, request, pk):
        try:
            product = self.get_product(pk)
            if not product:
                return self.not_found_response("Product not found")

            cut_type_id = request.data.get('cut_type_id')
            if not cut_type_id:
                return self.bad_request_response("Cut type id is required")

            try:
                cut_type = CutType.objects.get(pk=cut_type_id, status=True)
            except CutType.DoesNotExist:
                return self.not_found_response("Cut type not found or inactive")

            if ProductCutType.objects.filter(product=product, cut_type=cut_type).exists():
                return self.bad_request_response("Cut type already linked to this product")

            pct = ProductCutType.objects.create(product=product, cut_type=cut_type)
            return self.created_response(
                data=ProductCutTypeSerializer(pct).data,
                message="Cut type linked to product successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)

    def delete(self, request, pk, ct_id):
        try:
            product = self.get_product(pk)
            if not product:
                return self.not_found_response("Product not found")
            try:
                pct = ProductCutType.objects.get(pk=ct_id, product=product)
            except ProductCutType.DoesNotExist:
                return self.not_found_response("Cut type link not found")
            pct.delete()
            return self.deleted_response("Cut type removed from product successfully")
        except Exception as exc:
            return self.handle_exception(exc)


class CutTypeListView(BaseResponseMixin, APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            qs = CutType.objects.filter(status=True)
            return self.success_response(data=CutTypeSerializer(qs, many=True).data)
        except Exception as exc:
            return self.handle_exception(exc)


class AdminCutTypeListView(BaseResponseMixin, APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            qs = CutType.objects.all()
            return self.success_response(data=CutTypeSerializer(qs, many=True).data)
        except Exception as exc:
            return self.handle_exception(exc)


class CutTypeCreateView(BaseResponseMixin, APIView):
    """
    POST /api/admin/cut-types/create/
    """
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            serializer = CutTypeCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return self.error_response(
                    message="Validation failed",
                    error_code="VALIDATION_ERROR",
                    errors=serializer.errors
                )
            cut_type = serializer.save()
            return self.created_response(
                data=CutTypeSerializer(cut_type).data,
                message="Cut type created successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class CutTypeDetailView(BaseResponseMixin, APIView):
    """
    GET    /api/admin/cut-types/<pk>/
    PATCH  /api/admin/cut-types/<pk>/
    DELETE /api/admin/cut-types/<pk>/
    """
    permission_classes = [IsAdminUser]

    def get_object(self, pk):
        try:
            return CutType.objects.get(pk=pk)
        except CutType.DoesNotExist:
            return None

    def get(self, request, pk):
        try:
            cut_type = self.get_object(pk)
            if not cut_type:
                return self.not_found_response("Cut type not found")
            return self.success_response(data=CutTypeSerializer(cut_type).data)
        except Exception as exc:
            return self.handle_exception(exc)

    def patch(self, request, pk):
        try:
            cut_type = self.get_object(pk)
            if not cut_type:
                return self.not_found_response("Cut type not found")
            serializer = CutTypeUpdateSerializer(cut_type, data=request.data, partial=True)
            if not serializer.is_valid():
                return self.error_response(
                    message="Validation failed",
                    error_code="VALIDATION_ERROR",
                    errors=serializer.errors
                )
            cut_type = serializer.save()
            return self.updated_response(
                data=CutTypeSerializer(cut_type).data,
                message="Cut type updated successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)

    def delete(self, request, pk):
        try:
            cut_type = self.get_object(pk)
            if not cut_type:
                return self.not_found_response("Cut type not found")
            cut_type.delete()
            return self.deleted_response("Cut type deleted successfully")
        except Exception as exc:
            return self.handle_exception(exc)


class CutTypeToggleStatusView(BaseResponseMixin, APIView):
    """
    PATCH /api/admin/cut-types/<pk>/toggle-status/
    """
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        try:
            try:
                cut_type = CutType.objects.get(pk=pk)
            except CutType.DoesNotExist:
                return self.not_found_response("Cut type not found")

            cut_type.status = not cut_type.status
            cut_type.save()
            status_label = "activated" if cut_type.status else "deactivated"
            return self.success_response(
                data=CutTypeSerializer(cut_type).data,
                message=f"Cut type {status_label} successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


# ─────────────────────── INVENTORY VIEWS ───────────────────────

class AdminInventoryListView(BaseResponseMixin, APIView):
    """
    GET /api/admin/inventory/   → all products with inventory data
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            inventories = Inventory.objects.select_related(
                'product', 'product__category'
            ).all()

            search = request.query_params.get('search')
            if search:
                inventories = inventories.filter(product__name__icontains=search)

            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 10))
            start = (page - 1) * page_size
            end = start + page_size
            total = inventories.count()

            serializer = AdminInventorySerializer(
                inventories[start:end], many=True, context={'request': request}
            )
            return self.success_response(data={
                'results': serializer.data,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size,
            })
        except Exception as exc:
            return self.handle_exception(exc)


class AdminInventoryUpdateView(BaseResponseMixin, APIView):
    """
    PATCH /api/admin/inventory/<product_pk>/   → update stock levels
    """
    permission_classes = [IsAdminUser]

    def patch(self, request, product_pk):
        try:
            try:
                inventory = Inventory.objects.get(product_id=product_pk)
            except Inventory.DoesNotExist:
                return self.not_found_response("Inventory not found for this product")

            serializer = InventoryUpdateSerializer(inventory, data=request.data, partial=True)
            if not serializer.is_valid():
                return self.error_response(
                    message="Validation failed",
                    error_code="VALIDATION_ERROR",
                    errors=serializer.errors
                )
            inventory = serializer.save()
            return self.updated_response(
                data=AdminInventorySerializer(inventory, context={'request': request}).data,
                message="Inventory updated successfully"
            )
        except Exception as exc:
            return self.handle_exception(exc)


class ProductImageView(BaseResponseMixin, APIView):
    """
    GET    /api/admin/products/<pk>/images/          → list all images
    POST   /api/admin/products/<pk>/images/          → upload multiple images
    DELETE /api/admin/products/<pk>/images/<img_id>/ → delete one image
    PATCH  /api/admin/products/<pk>/images/<img_id>/ → set as primary
    """
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def get_product(self, pk):
        try:
            return Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return None

    def get(self, request, pk):
        product = self.get_product(pk)
        if not product:
            return self.not_found_response("Product not found")
        images = product.images.all()
        return self.success_response(data=ProductImageSerializer(images, many=True, context={'request': request}).data)

    def post(self, request, pk):
        product = self.get_product(pk)
        if not product:
            return self.not_found_response("Product not found")

        files = request.FILES.getlist('images')  # multiple files
        if not files:
            return self.error_response(message="No images provided.", error_code="VALIDATION_ERROR")

        created = []
        for file in files:
            img = ProductImage.objects.create(product=product, image=file)
            created.append(img)

        return self.created_response(
            data=ProductImageSerializer(created, many=True, context={'request': request}).data,
            message=f"{len(created)} image(s) uploaded successfully"
        )

    def delete(self, request, pk, img_id):
        product = self.get_product(pk)
        if not product:
            return self.not_found_response("Product not found")
        try:
            img = ProductImage.objects.get(pk=img_id, product=product)
        except ProductImage.DoesNotExist:
            return self.not_found_response("Image not found")
        img.image.delete(save=False)  # delete file from storage too
        img.delete()
        return self.deleted_response("Image deleted successfully")

    def patch(self, request, pk, img_id):
        product = self.get_product(pk)
        if not product:
            return self.not_found_response("Product not found")
        try:
            img = ProductImage.objects.get(pk=img_id, product=product)
        except ProductImage.DoesNotExist:
            return self.not_found_response("Image not found")
        img.is_primary = True
        img.save()  # triggers unset of others via save()
        return self.success_response(
            data=ProductImageSerializer(img, context={'request': request}).data,
            message="Primary image updated"
        )
