from django.contrib import admin

from .models import Category, Product, ProductImage

# @admin.register(RegisteredProduct)
# class RegisteredProductAdmin(admin.ModelAdmin):
#     list_display = ("serial_number", "product", "customer", "dealer", "purchase_date")
#     search_fields = ("serial_number", "customer__email", "dealer__email")
#     list_filter = ("product", "purchase_date")



class ProductImageInline(admin.TabularInline):

    model = ProductImage
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "slug",
        "created_at",
    )

    search_fields = (
        "name",
    )

    prepopulated_fields = {
        "slug": ("name",),
    }


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "sku",
        "product_type",
        "price",
        "status",
        "is_featured",
        "created_at",
    )

    search_fields = (
        "name",
        "sku",
    )

    list_filter = (
        "product_type",
        "status",
    )

    inlines = [ProductImageInline]


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):

    list_display = (
        "product",
        "alt_text",
        "is_primary",
        "order",
        "created_at",
    )

    search_fields = (
        "product__name",
        "alt_text",
    )

