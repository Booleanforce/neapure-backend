from rest_framework import serializers
from django.contrib.auth import get_user_model

from apps.products.models import Product
from apps.products.api.serializers import ProductDetailSerializer
from apps.product_registrations.models import ProductRegistration, ProductTimelineEvent
from apps.product_registrations.services.registration_service import RegistrationService
from shared.constants.roles import UserRole

User = get_user_model()


class UserMiniSerializer(serializers.ModelSerializer):
    """Mini serializer for embedded user data."""

    class Meta:
        model = User
        fields = ("id", "email", "full_name", "phone", "role")
        read_only_fields = fields


class ProductTimelineEventSerializer(serializers.ModelSerializer):
    """Serializer for the timeline of a product registration."""

    created_by = UserMiniSerializer(read_only=True)

    class Meta:
        model = ProductTimelineEvent
        fields = ("id", "event_type", "description", "created_by", "created_at")


class ProductRegistrationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing registrations."""

    product_name = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()
    qr_code_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductRegistration
        fields = (
            "id",
            "serial_number",
            "product_name",
            "customer_name",
            "installation_status",
            "warranty_status",
            "warranty_start_date",
            "warranty_end_date",
            "qr_code_url",
            "created_at",
        )

    def get_product_name(self, obj):
        return obj.product.name

    def get_customer_name(self, obj):
        return obj.customer.full_name if obj.customer else None

    def get_qr_code_url(self, obj):
        if obj.qr_code_image and hasattr(obj.qr_code_image, "url"):
            return obj.qr_code_image.url
        return None


class ProductRegistrationDetailSerializer(serializers.ModelSerializer):
    """Full serializer for retrieve endpoints."""

    product = ProductDetailSerializer(read_only=True)
    customer = UserMiniSerializer(read_only=True)
    dealer = UserMiniSerializer(read_only=True)
    assigned_technician = UserMiniSerializer(read_only=True)
    qr_code_url = serializers.SerializerMethodField()
    timeline = ProductTimelineEventSerializer(many=True, read_only=True)

    class Meta:
        model = ProductRegistration
        fields = (
            "id",
            "product",
            "serial_number",
            "customer",
            "dealer",
            "assigned_technician",
            "qr_code_image",
            "qr_code_url",
            "qr_code_data",
            "installation_status",
            "warranty_status",
            "warranty_start_date",
            "warranty_end_date",
            "installation_address",
            "gps_latitude",
            "gps_longitude",
            "timeline",
            "created_at",
            "updated_at",
        )

    def get_qr_code_url(self, obj):
        if obj.qr_code_image and hasattr(obj.qr_code_image, "url"):
            return obj.qr_code_image.url
        return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get("request")
        if request and request.user.role == UserRole.TECHNICIAN:
            if "product" in representation and "price" in representation["product"]:
                del representation["product"]["price"]
        return representation


class ProductRegistrationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new product registration."""

    product_id = serializers.PrimaryKeyRelatedField(
        source="product",
        queryset=Product.objects.all(),
    )
    customer_id = serializers.SlugRelatedField(
        source="customer",
        slug_field="firebase_uid",
        queryset=User.objects.all(),
    )
    dealer_id = serializers.SlugRelatedField(
        source="dealer",
        slug_field="firebase_uid",
        queryset=User.objects.all(),
        required=False,
    )

    class Meta:
        model = ProductRegistration
        fields = (
            "product_id",
            "customer_id",
            "dealer_id",
            "serial_number",
            "installation_address",
            "gps_latitude",
            "gps_longitude",
        )

    def validate_serial_number(self, value):
        if ProductRegistration.objects.filter(serial_number=value).exists():
            raise serializers.ValidationError("This serial number is already registered.")
        return value

    def validate_customer_id(self, value):
        if value.role != UserRole.CUSTOMER:
            raise serializers.ValidationError("Selected user must have the CUSTOMER role.")
        return value

    def validate_dealer_id(self, value):
        if value.role != UserRole.DEALER:
            raise serializers.ValidationError("Selected user must have the DEALER role.")
        return value

    def create(self, validated_data):
        request = self.context.get("request")
        
        dealer = validated_data.get("dealer")
        if not dealer and request and request.user.role == UserRole.DEALER:
            dealer = request.user

        return RegistrationService.register_product(
            product=validated_data["product"],
            serial_number=validated_data["serial_number"],
            customer=validated_data["customer"],
            dealer=dealer,
            installation_address=validated_data.get("installation_address", ""),
            gps_latitude=validated_data.get("gps_latitude"),
            gps_longitude=validated_data.get("gps_longitude"),
            registered_by=request.user if request else None,
        )


class ProductRegistrationAdminEditSerializer(serializers.ModelSerializer):
    """Minimal serializer strictly for generic update endpoints."""

    class Meta:
        model = ProductRegistration
        fields = (
            "installation_address",
            "gps_latitude",
            "gps_longitude",
        )


class QRVerifySerializer(serializers.ModelSerializer):
    """Serializer for the public QR code verification endpoint."""
    
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_image = serializers.SerializerMethodField()
    customer_name = serializers.CharField(source="customer.full_name", read_only=True)
    assigned_technician = UserMiniSerializer(read_only=True)

    class Meta:
        model = ProductRegistration
        fields = (
            "product_name",
            "product_sku",
            "product_image",
            "customer_name",
            "installation_status",
            "installation_address",
            "warranty_status",
            "warranty_start_date",
            "warranty_end_date",
            "assigned_technician",
        )

    def get_product_image(self, obj):
        primary_image = obj.product.images.filter(is_primary=True).first()
        if primary_image and primary_image.image and hasattr(primary_image.image, "url"):
            return primary_image.image.url
        return None
