from rest_framework import serializers
from apps.notifications.models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id", "recipient", "title", "message", 
            "notification_type", "event_type", "priority", 
            "is_read", "read_at", "link", "metadata", 
            "created_at", "updated_at"
        ]
        read_only_fields = [
            "id", "recipient", "title", "message", 
            "notification_type", "event_type", "priority", 
            "is_read", "read_at", "link", "metadata", 
            "created_at", "updated_at"
        ]
