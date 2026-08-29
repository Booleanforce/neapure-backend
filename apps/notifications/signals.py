from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.installations.models import InstallationRequest, ReplacementKitRequest
from apps.notifications.models import Notification
from apps.accounts.models import User
from shared.constants.roles import UserRole

@receiver(post_save, sender=InstallationRequest)
def notify_operations_admin_on_installation(sender, instance, created, **kwargs):
    if created:
        operations_admins = User.objects.filter(role=UserRole.OPERATIONS_ADMIN, is_active=True)
        for admin in operations_admins:
            Notification.objects.create(
                recipient=admin,
                title="New Installation Request",
                message=f"A new installation request (ID: {instance.id}) has been submitted by {instance.dealer.full_name if instance.dealer else 'a customer'}.",
                link=f"/admin/installations/requests/{instance.id}", event_type="SYSTEM", notification_type="SYSTEM"
            )

@receiver(post_save, sender=ReplacementKitRequest)
def notify_operations_admin_on_replacement_kit(sender, instance, created, **kwargs):
    if created:
        operations_admins = User.objects.filter(role=UserRole.OPERATIONS_ADMIN, is_active=True)
        for admin in operations_admins:
            Notification.objects.create(
                recipient=admin,
                title="New Replacement Kit Request",
                message=f"A new replacement kit request (ID: {instance.id}) has been submitted by {instance.dealer.full_name if instance.dealer else 'a customer'}.",
                link=f"/admin/installations/kits/{instance.id}", event_type="SYSTEM", notification_type="SYSTEM"
            )
