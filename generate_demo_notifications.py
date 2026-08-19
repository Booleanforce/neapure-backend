import os
import django
import random
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.notifications.models import Notification
from shared.constants.notifications import NotificationType, EventType, NotificationPriority

User = get_user_model()

def generate_notifications():
    super_admin = User.objects.filter(role='SUPER_ADMIN').first()
    dealer = User.objects.filter(role='DEALER').first()
    technician = User.objects.filter(role='TECHNICIAN').first()
    
    users = [super_admin, dealer, technician]
    
    for user in users:
        if not user: continue
        
        # Unread high priority
        Notification.objects.create(
            recipient=user,
            title="Urgent Installation Update",
            message="Installation #1024 requires immediate attention due to plumbing issues.",
            event_type=EventType.GENERAL,
            priority=NotificationPriority.HIGH,
            is_read=False,
            link="/admin/installations" if user.role == 'SUPER_ADMIN' else "/dealer/installations"
        )
        
        # Read normal priority
        Notification.objects.create(
            recipient=user,
            title="Installation Approved",
            message="The installation request has been approved successfully.",
            event_type=EventType.GENERAL,
            priority=NotificationPriority.NORMAL,
            is_read=True,
            read_at=timezone.now() - timedelta(hours=1),
            link="/admin/installations" if user.role == 'SUPER_ADMIN' else "/dealer/installations"
        )
        
        # Another unread
        Notification.objects.create(
            recipient=user,
            title="Technician Assigned",
            message="John Doe has been assigned to complete the installation tomorrow.",
            event_type=EventType.INSTALLATION_ASSIGNED,
            priority=NotificationPriority.NORMAL,
            is_read=False,
            link="/admin/installations" if user.role == 'SUPER_ADMIN' else "/dealer/installations"
        )

    print("Demo notifications created successfully!")

if __name__ == '__main__':
    generate_notifications()
