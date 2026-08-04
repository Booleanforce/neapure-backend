from rest_framework import serializers
from apps.products.models import Product, RegisteredProduct
from apps.accounts.api.serializers import UserSerializer

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ("id", "name", "sku", "description", "is_active", "created_at", "updated_at")

class RegisteredProductSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source="product", read_only=True)
    customer_details = UserSerializer(source="customer", read_only=True)
    
    class Meta:
        model = RegisteredProduct
        fields = (
            "id", "product", "product_details", "customer", "customer_details",
            "dealer", "serial_number", "purchase_date", "warranty_end_date",
            "created_at", "updated_at"
        )
        read_only_fields = ("dealer",)
# 

from apps.products.models import Category, Product, ProductImage

from apps.products.constants import ProductType


class CategorySerializer(serializers.ModelSerializer):
    """
    Full serializer for product categories.

    Fields: id, name, slug (auto-generated from name), description,
    created_at, updated_at.
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


class ProductImageSerializer(serializers.ModelSerializer):
    """
    Serializer for product images.

    Returns both the raw image field and a resolved image_url
    (Cloudinary URL in production).
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

    def get_image_url(self, obj):

        if obj.image and hasattr(obj.image, "url"):
            return obj.image.url

        return None


class ProductListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for product list views.

    Includes category_name and primary_image URL for card/grid displays.
    Does NOT include nested objects or heavy JSON fields.
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

    def get_category_name(self, obj):

        if obj.category:
            return obj.category.name

        return None

    def get_primary_image(self, obj):

        primary = obj.images.filter(is_primary=True).first()

        if primary and primary.image and hasattr(primary.image, "url"):
            return primary.image.url

        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for product detail views.

    Includes nested category object and all product images.
    """

    category = CategorySerializer(read_only=True)

    images = ProductImageSerializer(many=True, read_only=True)

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
            "images",
            "created_at",
            "updated_at",
        )


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Write-focused serializer for creating and updating products.

    Accepts category_id (UUID) to set the category FK.
    Validates: SKU uniqueness, positive price, and
    recommended_replacement_months required for FILTER type.
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
            "slug": {"required": False},
        }

    def validate_price(self, value):

        if value <= 0:
            raise serializers.ValidationError(
                "Price must be greater than 0."
            )

        return value

    def validate_sku(self, value):

        qs = Product.objects.filter(sku=value)

        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError(
                "A product with this SKU already exists."
            )

        return value

    def validate(self, attrs):

        product_type = attrs.get("product_type")
        recommended = attrs.get("recommended_replacement_months")

        # On partial update, fall back to instance values
        # for fields not included in the request.
        if self.instance:
            if product_type is None:
                product_type = self.instance.product_type

            if "recommended_replacement_months" not in attrs:
                recommended = self.instance.recommended_replacement_months

        if (
            product_type == ProductType.FILTER
            and recommended is None
        ):
            raise serializers.ValidationError({
                "recommended_replacement_months":
                    "This field is required for FILTER type products.",
            })

        return attrs


class ProductImageUploadRequestSerializer(serializers.Serializer):
    """
    Schema-only serializer for the upload_image endpoint.
    """
    image = serializers.ImageField(required=True)
    alt_text = serializers.CharField(required=False, allow_blank=True)
    is_primary = serializers.BooleanField(required=False, default=False)

