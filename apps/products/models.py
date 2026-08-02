from decimal import Decimal

from django.db import models, transaction
from django.core.validators import MinValueValidator
from django.utils.text import slugify

from shared.mixins.uuid import UUIDMixin
from shared.mixins.timestamp import TimeStampMixin
from shared.mixins.soft_delete import SoftDeleteModel

from .constants import ProductType, ProductStatus


class Category(UUIDMixin, TimeStampMixin):

    name = models.CharField(
        max_length=255,
        unique=True,
    )

    slug = models.SlugField(
        max_length=255,
        unique=True,
    )

    description = models.TextField(
        blank=True,
        default="",
    )

    class Meta:

        db_table = "categories"

        ordering = ["name"]

        verbose_name_plural = "categories"

    def __str__(self):

        return self.name

    def save(self, *args, **kwargs):

        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)


class Product(UUIDMixin, TimeStampMixin, SoftDeleteModel):

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )

    product_type = models.CharField(
        max_length=30,
        choices=ProductType.choices,
    )

    name = models.CharField(
        max_length=255,
    )

    slug = models.SlugField(
        max_length=255,
        unique=True,
    )

    sku = models.CharField(
        max_length=50,
        unique=True,
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    perfect_for = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    short_description = models.TextField(
        blank=True,
        default="",
    )

    key_features = models.JSONField(
        default=list,
    )

    technical_specs = models.JSONField(
        default=dict,
    )

    package_includes = models.JSONField(
        default=list,
    )

    warranty_duration_months = models.PositiveIntegerField(
        default=12,
    )

    recommended_replacement_months = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=ProductStatus.choices,
        default=ProductStatus.ACTIVE,
    )

    is_featured = models.BooleanField(
        default=False,
    )

    class Meta:

        db_table = "products"

        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["sku"]),
        ]

    def __str__(self):

        return self.name

    def save(self, *args, **kwargs):

        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)


class ProductImage(UUIDMixin, TimeStampMixin):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
    )

    image = models.ImageField(
        upload_to="products/images/",
    )

    alt_text = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    is_primary = models.BooleanField(
        default=False,
    )

    order = models.PositiveIntegerField(
        default=0,
    )

    class Meta:

        db_table = "product_images"

        ordering = ["order", "-created_at"]

    def __str__(self):

        return f"{self.product.name} - Image {self.order}"

    def save(self, *args, **kwargs):

        if self.is_primary:
            with transaction.atomic():
                ProductImage.objects.filter(
                    product=self.product,
                    is_primary=True,
                ).exclude(
                    pk=self.pk,
                ).update(
                    is_primary=False,
                )
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)
