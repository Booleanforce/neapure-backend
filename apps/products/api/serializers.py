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
