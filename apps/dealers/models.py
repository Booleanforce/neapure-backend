from django.db import models
from shared.mixins.base import BaseModel
from shared.mixins.soft_delete import SoftDeleteModel
from apps.accounts.models import User

class DealerStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    BLOCKED = "BLOCKED", "Blocked"

class DealerProfile(SoftDeleteModel, BaseModel):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="dealer_profile"
    )
    company_name = models.CharField(max_length=255, blank=True, default="")
    contact_person = models.CharField(max_length=255, blank=True, default="")
    trade_license = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=DealerStatus.choices,
        default=DealerStatus.ACTIVE
    )

    class Meta:
        db_table = "dealer_profiles"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - Dealer"
