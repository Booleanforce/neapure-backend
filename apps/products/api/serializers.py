from rest_framework import serializers

from apps.products.models import (
    Category,
    Product,
    ProductImage,
    RegisteredProduct,
)
from apps.accounts.api.serializers import UserSerializer
from apps.products.constants import ProductType


# ============================================================================
# Product Serializer
# ============================================================================

class ProductSerializer(serializers.ModelSerializer):
    """
    Basic product serializer.

    Used for product information inside RegisteredProductSerializer.
    """

    class Meta:
        model = Product

        fields = (
            "id",
            "name",
            "sku",
            "price",
            "product_type",
            "status",
            "is_featured",
            "created_at",
            "updated_at",
        )


# ============================================================================
# Registered Product Serializer
# ============================================================================

class RegisteredProductSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(
        source="product",
        read_only=True,
    )

    customer_details = UserSerializer(
        source="customer",
        read_only=True,
    )

    class Meta:
        model = RegisteredProduct

        fields = (
            "id",
            "product",
            "product_details",
            "customer",
            "customer_details",
            "dealer",
            "serial_number",
            "purchase_date",
            "warranty_end_date",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "dealer",
        )


# ============================================================================
# Category Serializer
# ============================================================================

class CategorySerializer(serializers.ModelSerializer):
    """
    Full serializer for product categories.

    Fields:
    - id
    - name
    - slug
    - description
    - created_at
    - updated_at
    """

    class Meta:
        model = Category

        fields = (
            "id",
            "name",
            "slug",
            "description",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "slug",
            "created_at",
            "updated_at",
        )


# ============================================================================
# Product Image Serializer
# ============================================================================

class ProductImageSerializer(serializers.ModelSerializer):
    """
    Serializer for product images.
    """

    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage

        fields = (
            "id",
            "image",
            "image_url",
            "alt_text",
            "is_primary",
            "order",
            "created_at",
        )

        read_only_fields = (
            "id",
            "image_url",
            "created_at",
        )

    def get_image_url(self, obj):
        if not obj.image:
            return None

        if not hasattr(obj.image, "url"):
            return None

        request = self.context.get("request")

        if request:
            return request.build_absolute_uri(
                obj.image.url
            )

        return obj.image.url


# ============================================================================
# Product List Serializer
# ============================================================================

class ProductListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for product list views.

    Includes:
    - category_name
    - primary_image

    Does not include heavy product JSON fields.
    """

    category_name = serializers.SerializerMethodField()

    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Product

        fields = (
            "id",
            "name",
            "slug",
            "sku",
            "price",
            "product_type",
            "status",
            "is_featured",
            "category_name",
            "primary_image",
            "created_at",
        )

        read_only_fields = (
            "id",
            "category_name",
            "primary_image",
            "created_at",
        )

    def get_category_name(self, obj):
        """
        Return the product category name.
        """

        if obj.category:
            return obj.category.name

        return None

    def get_primary_image(self, obj):
        """
        Return the complete URL of the primary product image.

        Example:

        http://127.0.0.1:8000/media/products/images/product.jpg
        """

        primary = (
            obj.images
            .filter(is_primary=True)
            .first()
        )

        if not primary:
            return None

        if not primary.image:
            return None

        if not hasattr(primary.image, "url"):
            return None

        request = self.context.get("request")

        if request:
            return request.build_absolute_uri(
                primary.image.url
            )

        return primary.image.url


# ============================================================================
# Product Detail Serializer
# ============================================================================

class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for product detail views.

    Includes:
    - nested category
    - primary image
    - all product images
    - complete product information
    """

    category = CategorySerializer(
        read_only=True
    )

    images = ProductImageSerializer(
        many=True,
        read_only=True,
    )

    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Product

        fields = (
            "id",
            "name",
            "slug",
            "sku",
            "price",
            "product_type",
            "perfect_for",
            "short_description",
            "key_features",
            "technical_specs",
            "package_includes",
            "warranty_duration_months",
            "recommended_replacement_months",
            "status",
            "is_featured",
            "category",
            "primary_image",
            "images",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "primary_image",
            "images",
            "created_at",
            "updated_at",
        )

    def get_primary_image(self, obj):
        primary = (
            obj.images
            .filter(is_primary=True)
            .first()
        )

        if not primary or not primary.image:
            return None

        if not hasattr(primary.image, "url"):
            return None

        request = self.context.get("request")

        if request:
            return request.build_absolute_uri(
                primary.image.url
            )

        return primary.image.url

# ============================================================================
# Product Create / Update Serializer
# ============================================================================

class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Write-focused serializer for creating and updating products.

    Accepts:
    - category_id

    Validates:
    - positive price
    - unique SKU
    - replacement period for FILTER products
    """

    category_id = serializers.PrimaryKeyRelatedField(
        source="category",
        queryset=Category.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Product

        fields = (
            "category_id",
            "product_type",
            "name",
            "slug",
            "sku",
            "price",
            "perfect_for",
            "short_description",
            "key_features",
            "technical_specs",
            "package_includes",
            "warranty_duration_months",
            "recommended_replacement_months",
            "status",
            "is_featured",
        )

        extra_kwargs = {
            "slug": {
                "required": False,
            },
        }

    def validate_price(self, value):
        """
        Price must be greater than zero.
        """

        if value <= 0:
            raise serializers.ValidationError(
                "Price must be greater than 0."
            )

        return value

    def validate_sku(self, value):
        """
        SKU must be unique.

        During update, exclude the current product.
        """

        qs = Product.objects.filter(
            sku=value
        )

        if self.instance:
            qs = qs.exclude(
                pk=self.instance.pk
            )

        if qs.exists():
            raise serializers.ValidationError(
                "A product with this SKU already exists."
            )

        return value

    def validate(self, attrs):
        """
        Validate FILTER replacement period.

        During partial updates, use the existing product
        values for fields that were not submitted.
        """

        product_type = attrs.get(
            "product_type"
        )

        recommended = attrs.get(
            "recommended_replacement_months"
        )

        # --------------------------------------------------------------
        # Partial update
        # --------------------------------------------------------------

        if self.instance:

            if product_type is None:
                product_type = (
                    self.instance.product_type
                )

            if (
                "recommended_replacement_months"
                not in attrs
            ):
                recommended = (
                    self.instance
                    .recommended_replacement_months
                )

        # --------------------------------------------------------------
        # FILTER validation
        # --------------------------------------------------------------

        if (
            product_type == ProductType.FILTER
            and recommended is None
        ):
            raise serializers.ValidationError(
                {
                    "recommended_replacement_months":
                        "This field is required for FILTER type products.",
                }
            )

        return attrs


# ============================================================================
# Product Image Upload Request Serializer
# ============================================================================

class ProductImageUploadRequestSerializer(
    serializers.Serializer
):
    """
    Schema-only serializer for the upload_image endpoint.
    """

    image = serializers.ImageField(
        required=True
    )

    alt_text = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    is_primary = serializers.BooleanField(
        required=False,
        default=False,
    )