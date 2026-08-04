from rest_framework import viewsets, status
<<<<<<< HEAD
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from shared.constants.roles import UserRole
from apps.products.models import Product, RegisteredProduct
from apps.products.api.serializers import ProductSerializer, RegisteredProductSerializer

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public catalog of products. Dealers and customers can view them.
    """
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "sku"]
    ordering_fields = ["name"]
    ordering = ["name"]

class RegisteredProductViewSet(viewsets.ModelViewSet):
    """
    API for registering and viewing owned products.
    """
    serializer_class = RegisteredProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["serial_number", "customer__email", "product__name"]
    ordering_fields = ["purchase_date", "created_at"]
    ordering = ["-purchase_date"]
    filterset_fields = ["product"]

    def get_queryset(self):
        user = self.request.user
        queryset = RegisteredProduct.objects.select_related("product", "customer", "dealer")
        
        if user.role == UserRole.CUSTOMER:
            return queryset.filter(customer=user)
        elif user.role == UserRole.DEALER:
            return queryset.filter(dealer=user)
        
        # Admin gets everything
        return queryset

    def create(self, request, *args, **kwargs):
        # Only Dealers or Admins can register a product
        if request.user.role == UserRole.CUSTOMER:
            return Response({"error": "Customers cannot register products directly."}, status=status.HTTP_403_FORBIDDEN)
            
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        dealer = request.user if request.user.role == UserRole.DEALER else None
        
        serializer.save(dealer=dealer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
=======
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser

from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.products.models import ProductImage
from apps.products.api.serializers import (
    CategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateUpdateSerializer,
    ProductImageSerializer,
    ProductImageUploadRequestSerializer,
)
from apps.products.selectors.product_selector import ProductSelector
from apps.products.services.product_service import ProductService
from apps.products.filters import ProductFilter
from apps.products.permissions import IsAdminOrReadOnly

from shared.responses.api_response import ApiResponse


@extend_schema_view(
    list=extend_schema(
        tags=["Categories"],
        description="List all product categories with pagination.",
    ),
    retrieve=extend_schema(
        tags=["Categories"],
        description="Retrieve a single category by its slug.",
    ),
    create=extend_schema(
        tags=["Categories"],
        description="Create a new product category. Admin only.",
    ),
    update=extend_schema(
        tags=["Categories"],
        description="Fully update a category by slug. Admin only.",
    ),
    partial_update=extend_schema(
        tags=["Categories"],
        description="Partially update a category by slug. Admin only.",
    ),
    destroy=extend_schema(
        tags=["Categories"],
        description="Delete a category by slug. Admin only.",
    ),
)
class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing product categories.

    Read access is available to all authenticated users.
    Write operations require Super Admin or Operations Admin role.
    """

    queryset = ProductSelector.get_categories()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"

    def retrieve(self, request, *args, **kwargs):

        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return ApiResponse.success(
            data=serializer.data,
            message="Category retrieved successfully.",
        )

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return ApiResponse.success(
            data=serializer.data,
            message="Category created successfully.",
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):

        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return ApiResponse.success(
            data=serializer.data,
            message="Category updated successfully.",
        )

    def partial_update(self, request, *args, **kwargs):

        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return ApiResponse.success(
            data=serializer.data,
            message="Category updated successfully.",
        )

    def destroy(self, request, *args, **kwargs):

        instance = self.get_object()
        instance.delete()

        return ApiResponse.success(
            message="Category deleted successfully.",
        )


@extend_schema_view(
    list=extend_schema(
        tags=["Products"],
        description=(
            "List all products with pagination. "
            "Supports filtering by category (slug), category_id (UUID), "
            "product_type, status, is_featured, min_price, max_price. "
            "Supports search on name, sku, and short_description."
        ),
    ),
    retrieve=extend_schema(
        tags=["Products"],
        description=(
            "Retrieve full product details by slug, including nested "
            "category object and all product images."
        ),
    ),
    create=extend_schema(
        tags=["Products"],
        description="Create a new product. Admin only.",
    ),
    update=extend_schema(
        tags=["Products"],
        description="Fully update a product by slug. Admin only.",
    ),
    partial_update=extend_schema(
        tags=["Products"],
        description="Partially update a product by slug. Admin only.",
    ),
    destroy=extend_schema(
        tags=["Products"],
        description=(
            "Soft-delete a product by slug. Admin only. "
            "The product is marked as deleted but not removed from the database."
        ),
    ),
)
class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing products.

    Read access (list, retrieve, featured) is available to all
    authenticated users. Write operations (create, update, delete,
    upload_image) require Super Admin or Operations Admin role.

    Products are soft-deleted — destroy marks is_deleted=True
    rather than removing the record.
    """

    permission_classes = [IsAdminOrReadOnly]
    filterset_class = ProductFilter
    search_fields = ["name", "sku", "short_description"]
    lookup_field = "slug"

    def get_queryset(self):

        return ProductSelector.get_products()

    def get_serializer_class(self):

        if self.action in ("list", "featured"):
            return ProductListSerializer

        if self.action == "retrieve":
            return ProductDetailSerializer

        return ProductCreateUpdateSerializer

    # list() is NOT overridden — CustomPagination already
    # wraps the response in ApiResponse.success().

    def retrieve(self, request, *args, **kwargs):

        instance = self.get_object()
        serializer = ProductDetailSerializer(instance)

        return ApiResponse.success(
            data=serializer.data,
            message="Product retrieved successfully.",
        )

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = ProductService.create_product(
            serializer.validated_data,
        )

        return ApiResponse.success(
            data=ProductDetailSerializer(product).data,
            message="Product created successfully.",
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):

        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        product = ProductService.update_product(
            instance,
            serializer.validated_data,
        )

        return ApiResponse.success(
            data=ProductDetailSerializer(product).data,
            message="Product updated successfully.",
        )

    def partial_update(self, request, *args, **kwargs):

        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        product = ProductService.update_product(
            instance,
            serializer.validated_data,
        )

        return ApiResponse.success(
            data=ProductDetailSerializer(product).data,
            message="Product updated successfully.",
        )

    def destroy(self, request, *args, **kwargs):

        instance = self.get_object()

        ProductService.soft_delete_product(instance)

        return ApiResponse.success(
            message="Product deleted successfully.",
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Products"],
        description=(
            "Upload an image for a product. Accepts multipart form data "
            "with 'image' (file, required), 'alt_text' (string, optional), "
            "and 'is_primary' (boolean, optional — defaults to false). "
            "Setting is_primary=true automatically unsets primary on other images."
        ),
        request=ProductImageUploadRequestSerializer,
    )
    @action(
        detail=True,
        methods=["post"],
        parser_classes=[MultiPartParser, FormParser],
    )
    def upload_image(self, request, slug=None):
        """Upload an image for a specific product."""

        product = self.get_object()

        image_file = request.FILES.get("image")

        if not image_file:
            return ApiResponse.error(
                message="No image file provided.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        alt_text = request.data.get("alt_text", "")

        is_primary = str(
            request.data.get("is_primary", "false")
        ).lower() in ("true", "1")

        ProductImage.objects.create(
            product=product,
            image=image_file,
            alt_text=alt_text,
            is_primary=is_primary,
        )

        serializer = ProductDetailSerializer(product)

        return ApiResponse.success(
            data=serializer.data,
            message="Image uploaded successfully.",
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        tags=["Products"],
        description=(
            "List featured products (is_featured=True, status=ACTIVE). "
            "Paginated with the same pagination as the main product list."
        ),
    )
    @action(
        detail=False,
        methods=["get"],
    )
    def featured(self, request):
        """Retrieve all featured products."""

        queryset = ProductSelector.get_featured_products()

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = ProductListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ProductListSerializer(queryset, many=True)

        return ApiResponse.success(
            data=serializer.data,
            message="Featured products retrieved successfully.",
        )
>>>>>>> origin/syed
