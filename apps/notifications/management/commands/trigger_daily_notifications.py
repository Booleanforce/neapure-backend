from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.products.models import RegisteredProduct
from apps.notifications.services import NotificationService
from shared.constants.notifications import EventType, NotificationPriority, NotificationType

class Command(BaseCommand):
    help = 'Triggers daily notifications for Warranty Expiry, Service Reminder, and Filter Replacement.'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        self.stdout.write(f"Running daily notifications check for {today}...")

        # 1. Warranty Expiry (e.g., exactly 30 days before warranty_end_date)
        thirty_days_from_now = today + timedelta(days=30)
        expiring_warranties = RegisteredProduct.objects.filter(
            warranty_end_date=thirty_days_from_now,
            is_deleted=False
        )

        for rp in expiring_warranties:
            NotificationService.send(
                recipient=rp.customer,
                title="Warranty Expiring Soon",
                message=f"The warranty for your {rp.product.name} (Serial: {rp.serial_number}) will expire in 30 days.",
                event_type=EventType.WARRANTY_EXPIRY,
                priority=NotificationPriority.HIGH,
                channels=[NotificationType.IN_APP, NotificationType.EMAIL, NotificationType.PUSH]
            )
            self.stdout.write(f"Triggered WARRANTY_EXPIRY for {rp.customer.email}")

        # 2. Filter Replacement (e.g., exactly 180 days after purchase)
        six_months_ago = today - timedelta(days=180)
        filter_replacements = RegisteredProduct.objects.filter(
            purchase_date=six_months_ago,
            is_deleted=False
        )

        for rp in filter_replacements:
            NotificationService.send(
                recipient=rp.customer,
                title="Filter Replacement Reminder",
                message=f"It has been 6 months since you purchased your {rp.product.name}. It is time to replace your water filter.",
                event_type=EventType.FILTER_REPLACEMENT,
                priority=NotificationPriority.NORMAL,
                channels=[NotificationType.IN_APP, NotificationType.EMAIL, NotificationType.SMS]
            )
            self.stdout.write(f"Triggered FILTER_REPLACEMENT for {rp.customer.email}")

        # 3. Service Reminder (e.g., exactly 365 days after purchase)
        one_year_ago = today - timedelta(days=365)
        service_reminders = RegisteredProduct.objects.filter(
            purchase_date=one_year_ago,
            is_deleted=False
        )

        for rp in service_reminders:
            NotificationService.send(
                recipient=rp.customer,
                title="Annual Service Reminder",
                message=f"It's been a year since you purchased your {rp.product.name}. Please schedule your annual maintenance service.",
                event_type=EventType.SERVICE_REMINDER,
                priority=NotificationPriority.NORMAL,
                channels=[NotificationType.IN_APP, NotificationType.EMAIL]
            )
            self.stdout.write(f"Triggered SERVICE_REMINDER for {rp.customer.email}")

        self.stdout.write(self.style.SUCCESS("Daily notifications check completed successfully."))
