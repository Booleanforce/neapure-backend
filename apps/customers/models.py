from django.db import models
from shared.mixins.base import BaseModel
from shared.mixins.soft_delete import SoftDeleteModel
from apps.accounts.models import User

class CustomerStatus(models.TextChoices):
    NEW = "NEW", "New"
    ACTIVE = "ACTIVE", "Active"
    PENDING = "PENDING", "Pending"
    INACTIVE = "INACTIVE", "Inactive"

class CustomerProfile(SoftDeleteModel, BaseModel):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="customer_profile"
    )
    registered_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="registered_customers"
    )
    alternate_phone = models.CharField(max_length=20, blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=CustomerStatus.choices,
        default=CustomerStatus.NEW
    )

    class Meta:
        db_table = "customer_profiles"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - Profile"


class CustomerAddress(BaseModel):
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="addresses"
    )
    country = models.CharField(max_length=100, default="Bangladesh")
    division_state = models.CharField(max_length=100, blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    area = models.CharField(max_length=100, blank=True, default="")
    postal_code = models.CharField(max_length=20, blank=True, default="")
    full_address = models.TextField(blank=True, default="")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = "customer_addresses"
        ordering = ["-created_at"]
        verbose_name_plural = "Customer addresses"

    def __str__(self):
        return f"{self.customer.email} - {self.area}, {self.city}"

    def save(self, *args, **kwargs):
        if self.is_default:
            CustomerAddress.objects.filter(customer=self.customer).update(is_default=False)
        super().save(*args, **kwargs)


class CustomerNote(BaseModel):
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notes"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="authored_notes"
    )
    text = models.TextField()

    class Meta:
        db_table = "customer_notes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Note on {self.customer.email} by {self.author.email if self.author else 'System'}"


class CustomerHistory(BaseModel):
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="history_logs"
    )
    event_type = models.CharField(max_length=100)
    description = models.TextField()
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="performed_actions"
    )

    class Meta:
        db_table = "customer_history"
        ordering = ["-created_at"]
        verbose_name_plural = "Customer histories"

    def __str__(self):
        return f"{self.customer.email} - {self.event_type}"
