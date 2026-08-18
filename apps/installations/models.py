from django.db import models
from shared.mixins.base import BaseModel
from shared.mixins.soft_delete import SoftDeleteModel
from apps.accounts.models import User
from apps.products.models import RegisteredProduct

class InstallationStatus(models.TextChoices):
    PENDING_APPROVAL = "PENDING_APPROVAL", "Pending Approval"
    APPROVED = "APPROVED", "Approved"
    DISAPPROVED = "DISAPPROVED", "Disapproved"
    SCHEDULED = "SCHEDULED", "Scheduled"
    ASSIGNED = "ASSIGNED", "Assigned"
    ACCEPTED = "ACCEPTED", "Accepted"
    REJECTED = "REJECTED", "Rejected"
    RESCHEDULED = "RESCHEDULED", "Rescheduled"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"

class InstallationRequest(SoftDeleteModel, BaseModel):
    registered_product = models.ForeignKey(RegisteredProduct, on_delete=models.CASCADE, related_name="installation_requests")
    dealer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="submitted_installations")
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="installation_requests")
    status = models.CharField(max_length=20, choices=InstallationStatus.choices, default=InstallationStatus.PENDING_APPROVAL)
    admin_notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "installation_requests"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Install Req {self.id} - {self.status}"

class ReplacementKitRequest(SoftDeleteModel, BaseModel):
    registered_product = models.ForeignKey(RegisteredProduct, on_delete=models.CASCADE, related_name="replacement_kit_requests")
    dealer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="submitted_kit_requests")
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="replacement_kit_requests")
    description = models.TextField(help_text="Reason for replacement kit.")
    status = models.CharField(max_length=20, choices=InstallationStatus.choices, default=InstallationStatus.PENDING_APPROVAL)
    admin_notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "replacement_kit_requests"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Kit Req {self.id} - {self.status}"

class InstallationHistory(BaseModel):
    installation = models.ForeignKey(
        InstallationRequest,
        on_delete=models.CASCADE,
        related_name="history_logs"
    )
    event_type = models.CharField(max_length=100)
    description = models.TextField()
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="performed_installations"
    )

    class Meta:
        db_table = "installation_history"
        ordering = ["-created_at"]
        verbose_name_plural = "Installation histories"

    def __str__(self):
        return f"History for Req {self.installation.id} - {self.event_type}"

class PhotoType(models.TextChoices):
    BEFORE = "BEFORE", "Before Installation"
    AFTER = "AFTER", "After Installation"

class InstallationPhoto(BaseModel):
    installation = models.ForeignKey(
        InstallationRequest,
        on_delete=models.CASCADE,
        related_name="photos"
    )
    photo_type = models.CharField(
        max_length=20,
        choices=PhotoType.choices
    )
    photo = models.ImageField(upload_to="installations/photos/")
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_installation_photos"
    )

    class Meta:
        db_table = "installation_photos"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.photo_type} Photo for Req {self.installation.id}"

class InstallationChecklist(BaseModel):
    installation = models.OneToOneField(
        InstallationRequest,
        on_delete=models.CASCADE,
        related_name="checklist"
    )
    data = models.JSONField(default=dict)
    submitted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="submitted_checklists"
    )

    class Meta:
        db_table = "installation_checklists"

    def __str__(self):
        return f"Checklist for Req {self.installation.id}"

class InstallationSignature(BaseModel):
    installation = models.OneToOneField(
        InstallationRequest,
        on_delete=models.CASCADE,
        related_name="signature"
    )
    signature_image = models.ImageField(upload_to="installations/signatures/")
    collected_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="collected_signatures"
    )

    class Meta:
        db_table = "installation_signatures"

    def __str__(self):
        return f"Signature for Req {self.installation.id}"
