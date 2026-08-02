from django.db import models
from django.conf import settings

from shared.mixins.uuid import UUIDMixin
from shared.mixins.timestamp import TimeStampMixin
from shared.mixins.soft_delete import SoftDeleteModel

from apps.products.models import Product
from .constants import InstallationStatus, WarrantyStatus, TimelineEventType


class ProductRegistration(UUIDMixin, TimeStampMixin, SoftDeleteModel):

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="registrations",
    )

    serial_number = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
    )

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="owned_products",
    )

    dealer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dealer_registrations",
    )

    assigned_technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_registrations",
    )

    qr_code_image = models.ImageField(
        upload_to="registrations/qrcodes/",
        null=True,
        blank=True,
    )

    qr_code_data = models.CharField(
        max_length=255,
        blank=True,
    )

    installation_status = models.CharField(
        max_length=50,
        choices=InstallationStatus.choices,
        default=InstallationStatus.PENDING,
    )

    warranty_status = models.CharField(
        max_length=50,
        choices=WarrantyStatus.choices,
        default=WarrantyStatus.NOT_ACTIVATED,
    )

    warranty_start_date = models.DateField(
        null=True,
        blank=True,
    )

    warranty_end_date = models.DateField(
        null=True,
        blank=True,
    )

    installation_address = models.TextField(
        blank=True,
    )

    gps_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    gps_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    class Meta:

        db_table = "product_registrations"

        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["customer"]),
            models.Index(fields=["warranty_status"]),
        ]
        # serial_number is inherently indexed via unique=True/db_index=True

    def __str__(self):

        return f"{self.product.name} ({self.serial_number})"


class ProductTimelineEvent(UUIDMixin, TimeStampMixin):

    registration = models.ForeignKey(
        ProductRegistration,
        on_delete=models.CASCADE,
        related_name="timeline",
    )

    event_type = models.CharField(
        max_length=50,
        choices=TimelineEventType.choices,
    )

    description = models.TextField(
        blank=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )

    class Meta:

        db_table = "product_timeline_events"

        ordering = ["created_at"]

    def __str__(self):

        return f"{self.registration.serial_number} - {self.event_type}"
