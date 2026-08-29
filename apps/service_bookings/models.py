import uuid
import random
import string
from django.db import models
from django.conf import settings

from shared.mixins.uuid import UUIDMixin
from shared.mixins.timestamp import TimeStampMixin
from shared.mixins.soft_delete import SoftDeleteModel
from shared.validators.phone_validator import validate_phone

from apps.products.models import Product
from apps.service_bookings.constants import ServiceType, BookingStatus


def generate_booking_id():
    # SB-XXXXXXXX (8 alphanumeric chars)
    chars = string.ascii_uppercase + string.digits
    random_str = "".join(random.choices(chars, k=8))
    return f"SB-{random_str}"


class ServiceBooking(UUIDMixin, TimeStampMixin, SoftDeleteModel):
    booking_id = models.CharField(max_length=20, unique=True, blank=True)
    customer_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, validators=[validate_phone])
    email = models.EmailField(blank=True)
    
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    product_category = models.CharField(max_length=100)
    product_model_text = models.CharField(max_length=255)
    
    service_type = models.CharField(max_length=30, choices=ServiceType.choices)
    
    division = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    full_address = models.TextField()
    
    preferred_date = models.DateField()
    preferred_time = models.CharField(max_length=255)
    
    description = models.TextField(blank=True)
    
    attachment = models.ImageField(
        upload_to="service_bookings/attachments/",
        null=True,
        blank=True
    )
    
    status = models.CharField(
        max_length=30,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING
    )
    
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_service_bookings"
    )

    class Meta:
        db_table = "service_bookings"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["booking_id"]),
            models.Index(fields=["status"]),
            models.Index(fields=["phone"]),
        ]

    def __str__(self):
        return f"{self.booking_id} - {self.customer_name}"

    def save(self, *args, **kwargs):
        if not self.booking_id:
            # Generate a unique booking ID
            while True:
                bid = generate_booking_id()
                if not ServiceBooking.objects.filter(booking_id=bid).exists():
                    self.booking_id = bid
                    break
        super().save(*args, **kwargs)


class ServiceBookingNote(UUIDMixin, TimeStampMixin):
    booking = models.ForeignKey(
        ServiceBooking,
        on_delete=models.CASCADE,
        related_name="notes"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    note = models.TextField()

    class Meta:
        db_table = "service_booking_notes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Note by {self.author} for {self.booking.booking_id}"


class ServiceStatusHistory(UUIDMixin, TimeStampMixin):
    booking = models.ForeignKey(
        ServiceBooking,
        on_delete=models.CASCADE,
        related_name="status_history"
    )
    old_status = models.CharField(max_length=30, blank=True)
    new_status = models.CharField(max_length=30)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    class Meta:
        db_table = "service_status_history"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.booking.booking_id}: {self.old_status} -> {self.new_status}"
