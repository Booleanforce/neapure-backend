from django.db import transaction

from apps.products.models import Product, ProductImage


class ProductService:

    @staticmethod
    @transaction.atomic
    def create_product(data, images=None):

        product = Product.objects.create(**data)

        if images:
            for image_data in images:
                ProductImage.objects.create(
                    product=product,
                    **image_data,
                )

        return product

    @staticmethod
    @transaction.atomic
    def update_product(product, data):

        for field, value in data.items():
            setattr(product, field, value)

        product.save()

        return product

    @staticmethod
    def soft_delete_product(product):

        product.soft_delete()

    @staticmethod
    @transaction.atomic
    def set_primary_image(product, image):

        image.is_primary = True
        image.save()
