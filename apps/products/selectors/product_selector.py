from django.shortcuts import get_object_or_404

from apps.products.models import Product, Category

from apps.products.constants import ProductStatus


class ProductSelector:

    @staticmethod
    def get_products():

        return Product.objects.filter(
            is_deleted=False,
        ).select_related("category")

    @staticmethod
    def get_product_by_slug(slug):

        return get_object_or_404(
            Product.objects.filter(is_deleted=False),
            slug=slug,
        )

    @staticmethod
    def get_featured_products():

        return Product.objects.filter(
            is_featured=True,
            status=ProductStatus.ACTIVE,
            is_deleted=False,
        ).select_related("category")

    @staticmethod
    def get_categories():

        return Category.objects.all()
