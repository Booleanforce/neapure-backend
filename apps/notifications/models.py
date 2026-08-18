from django.db import models
from shared.mixins.base import BaseModel
from apps.accounts.models import User
from shared.constants.notifications import NotificationType, EventType, NotificationPriority

class Notification(BaseModel):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    
    # Generic relation or simple text for link (simpler)
    link = models.CharField(max_length=255, blank=True, null=True)
    
    notification_type = models.CharField(
        max_length=50, 
        choices=NotificationType.choices,
        default=NotificationType.IN_APP
    )
    event_type = models.CharField(
        max_length=50,
        choices=EventType.choices,
        default=EventType.GENERAL
    )
    priority = models.CharField(
        max_length=20,
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL
    )
    
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(blank=True, null=True)
    
    # Generic relation or simple text for link (simpler)
    link = models.CharField(max_length=255, blank=True, null=True)
    
    # Metadata for additional context (e.g., Action URL, related entity ID)
    metadata = models.JSONField(blank=True, null=True, default=dict)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recipient.email} - {self.title}"
