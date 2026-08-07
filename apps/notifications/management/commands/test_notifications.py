from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.notifications.services import NotificationService
from shared.constants.notifications import EventType, NotificationPriority, NotificationType

User = get_user_model()

class Command(BaseCommand):
    help = 'Tests the NotificationService by sending dummy notifications.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Setting up test data...")
        
        # Get or create a dummy user to receive the notifications
        import uuid
        # Target the exact user that the frontend is currently authenticated as
        test_user = User.objects.filter(email="admin@neapure.com").first()
        if not test_user:
            # Fallback
            test_user = User.objects.filter(is_superuser=True).first()
            
        if not test_user:
            self.stdout.write(self.style.ERROR("Could not find an admin user to send notifications to!"))
            return
            
        self.stdout.write(f"Using admin user: {test_user.email}")

        self.stdout.write("--- Dispatching Notifications ---")

        # 1. Test In-App Notification (High Priority)
        NotificationService.send(
            recipient=test_user,
            title="System Alert: High Priority",
            message="This is a test IN_APP notification with HIGH priority.",
            event_type=EventType.GENERAL,
            priority=NotificationPriority.HIGH,
            channels=[NotificationType.IN_APP]
        )
        self.stdout.write(self.style.SUCCESS("[OK] Sent IN_APP notification"))

        # 2. Test Email Notification
        NotificationService.send(
            recipient=test_user,
            title="Welcome to NeaPure!",
            message="This is a test EMAIL notification routed through Django's send_mail.",
            event_type=EventType.GENERAL,
            priority=NotificationPriority.NORMAL,
            channels=[NotificationType.EMAIL]
        )
        self.stdout.write(self.style.SUCCESS("[OK] Sent EMAIL notification"))

        # 3. Test Multi-channel (In-App + Simulated SMS)
        NotificationService.send(
            recipient=test_user,
            title="Technician On The Way",
            message="Your technician is arriving in 15 minutes. (Simulated SMS & In-App)",
            event_type=EventType.TECHNICIAN_ON_THE_WAY,
            priority=NotificationPriority.HIGH,
            channels=[NotificationType.IN_APP, NotificationType.SMS]
        )
        self.stdout.write(self.style.SUCCESS("[OK] Sent IN_APP + SMS notification"))

        # Verify database creation
        from apps.notifications.models import Notification
        count = Notification.objects.filter(recipient=test_user).count()
        
        self.stdout.write("\n--- Test Results ---")
        self.stdout.write(self.style.SUCCESS(f"Successfully verified! User {test_user.email} now has {count} notifications in the database."))
        self.stdout.write("You can log in to the Django Admin and look at the Notifications table to see them!")
