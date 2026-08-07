from django.contrib import admin
from apps.notifications.models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "recipient", 
        "title", 
        "notification_type", 
        "event_type", 
        "priority", 
        "is_read", 
        "created_at"
    )
    list_filter = ("is_read", "notification_type", "event_type", "priority", "created_at")
    search_fields = ("recipient__email", "recipient__full_name", "title", "message")
    readonly_fields = (
        "recipient", 
        "title", 
        "message", 
        "notification_type", 
        "event_type", 
        "priority", 
        "is_read", 
        "read_at", 
        "link", 
        "metadata", 
        "created_at", 
        "updated_at"
    )

    def has_add_permission(self, request):
        # Admin should not manually create notifications
        return False

    def has_change_permission(self, request, obj=None):
        # Admin should not alter historical notifications
        return False
