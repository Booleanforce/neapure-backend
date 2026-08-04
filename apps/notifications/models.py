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

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recipient.email} - {self.title}"
