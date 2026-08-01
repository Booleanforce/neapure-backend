from django.contrib import admin
from apps.products.models import Product, RegisteredProduct

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "is_active", "created_at")
    search_fields = ("name", "sku")
    list_filter = ("is_active",)

@admin.register(RegisteredProduct)
class RegisteredProductAdmin(admin.ModelAdmin):
    list_display = ("serial_number", "product", "customer", "dealer", "purchase_date")
    search_fields = ("serial_number", "customer__email", "dealer__email")
    list_filter = ("product", "purchase_date")
