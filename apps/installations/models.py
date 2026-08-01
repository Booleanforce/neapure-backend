from django.db import models
from shared.mixins.base import BaseModel
from shared.mixins.soft_delete import SoftDeleteModel
from apps.accounts.models import User
from apps.products.models import RegisteredProduct

class InstallationStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    COMPLETED = "COMPLETED", "Completed"

class InstallationRequest(SoftDeleteModel, BaseModel):
    registered_product = models.ForeignKey(RegisteredProduct, on_delete=models.CASCADE, related_name="installation_requests")
    dealer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="submitted_installations")
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="installation_requests")
    status = models.CharField(max_length=20, choices=InstallationStatus.choices, default=InstallationStatus.PENDING)
    admin_notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "installation_requests"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Install Req {self.id} - {self.status}"
