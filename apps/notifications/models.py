from django.db import models
from shared.mixins.base import BaseModel
from apps.accounts.models import User

class Notification(BaseModel):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    
    # Generic relation or simple text for link (simpler)
    link = models.CharField(max_length=255, blank=True, null=True)
    event_type = models.CharField(max_length=50, default="SYSTEM")
    notification_type = models.CharField(max_length=50, default="SYSTEM")
    priority = models.CharField(max_length=20, default="NORMAL")
    metadata = models.JSONField(blank=True, null=True)
    read_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recipient.email} - {self.title}"
