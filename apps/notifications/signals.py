from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from apps.installations.models import InstallationRequest, ReplacementKitRequest
from apps.technicians.models import TechnicianJob, JobStatus
from apps.accounts.models import User
from shared.constants.roles import UserRole
from shared.constants.notifications import EventType, NotificationPriority, NotificationType
from apps.notifications.services import NotificationService

@receiver(pre_save, sender=InstallationRequest)
def track_installation_request_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = InstallationRequest.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except InstallationRequest.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(post_save, sender=InstallationRequest)
def notify_on_installation_request_changes(sender, instance, created, **kwargs):
    if created:
        operations_admins = User.objects.filter(role=UserRole.OPERATIONS_ADMIN, is_active=True)
        for admin in operations_admins:
            NotificationService.send(
                recipient=admin,
                title="New Installation Request",
                message=f"A new installation request (ID: {instance.id}) has been submitted by {instance.dealer.full_name if instance.dealer else 'a customer'}.",
                event_type=EventType.GENERAL,
                priority=NotificationPriority.NORMAL,
                channels=[NotificationType.IN_APP, NotificationType.EMAIL],
                link=f"/admin/installations/requests/{instance.id}"
            )
    else:
        # Check if we should notify about status changes using _old_status
        old_status = getattr(instance, "_old_status", None)
        if old_status and old_status != instance.status:
            from apps.installations.models import InstallationStatus
            if instance.status == InstallationStatus.APPROVED:
                if instance.dealer:
                    NotificationService.send(
                        recipient=instance.dealer,
                        title="Installation Request Approved",
                        message=f"Your installation request for customer {instance.customer.full_name} has been approved.",
                        event_type=EventType.GENERAL,
                        priority=NotificationPriority.NORMAL,
                        channels=[NotificationType.IN_APP],
                        link=f"/dealer/installations/{instance.id}"
                    )
            elif instance.status == InstallationStatus.DISAPPROVED:
                if instance.dealer:
                    NotificationService.send(
                        recipient=instance.dealer,
                        title="Installation Request Disapproved",
                        message=f"Your installation request for customer {instance.customer.full_name} was disapproved.",
                        event_type=EventType.GENERAL,
                        priority=NotificationPriority.HIGH,
                        channels=[NotificationType.IN_APP],
                        link=f"/dealer/installations/{instance.id}"
                    )

@receiver(post_save, sender=ReplacementKitRequest)
def notify_on_replacement_kit(sender, instance, created, **kwargs):
    if created:
        operations_admins = User.objects.filter(role=UserRole.OPERATIONS_ADMIN, is_active=True)
        for admin in operations_admins:
            NotificationService.send(
                recipient=admin,
                title="New Replacement Kit Request",
                message=f"A new replacement kit request (ID: {instance.id}) has been submitted by {instance.dealer.full_name if instance.dealer else 'a customer'}.",
                event_type=EventType.GENERAL,
                priority=NotificationPriority.NORMAL,
                channels=[NotificationType.IN_APP, NotificationType.EMAIL],
                link=f"/admin/installations/kits/{instance.id}"
            )
    else:
        # Assuming COMPLETED means the kit is shipped/fulfilled
        from apps.installations.models import InstallationStatus
        if instance.status == InstallationStatus.COMPLETED:
            NotificationService.send(
                recipient=instance.customer,
                title="Replacement Kit Shipped",
                message="Your replacement kit has been shipped and is on its way.",
                event_type=EventType.REPLACEMENT_KIT_SHIPPED,
                priority=NotificationPriority.NORMAL,
                channels=[NotificationType.IN_APP, NotificationType.EMAIL, NotificationType.SMS],
                link=f"/customer/kits/{instance.id}"
            )

@receiver(post_save, sender=TechnicianJob)
def notify_on_technician_job_changes(sender, instance, created, **kwargs):
    # Only act if status changed (for a proper implementation we would track pre_save, 
    # but for simplicity we rely on the current state after save, typically created or status update)
    if created:
        # Installation Assigned
        NotificationService.send(
            recipient=instance.technician,
            title="New Job Assigned",
            message=f"You have been assigned a new {instance.job_type.lower()} job.",
            event_type=EventType.INSTALLATION_ASSIGNED,
            priority=NotificationPriority.HIGH,
            channels=[NotificationType.IN_APP, NotificationType.PUSH]
        )
        NotificationService.send(
            recipient=instance.customer,
            title="Technician Assigned",
            message=f"A technician has been assigned to your {instance.job_type.lower()} request.",
            event_type=EventType.INSTALLATION_ASSIGNED,
            priority=NotificationPriority.NORMAL,
            channels=[NotificationType.IN_APP, NotificationType.EMAIL]
        )
    else:
        # This simple check assumes this signal runs whenever status is updated.
        if instance.status == JobStatus.IN_PROGRESS:
            NotificationService.send(
                recipient=instance.customer,
                title="Technician On The Way",
                message="Your technician is currently on the way.",
                event_type=EventType.TECHNICIAN_ON_THE_WAY,
                priority=NotificationPriority.HIGH,
                channels=[NotificationType.IN_APP, NotificationType.PUSH, NotificationType.SMS]
            )
        elif instance.status == JobStatus.COMPLETED:
            NotificationService.send(
                recipient=instance.customer,
                title="Job Completed",
                message="Your job has been marked as completed successfully.",
                event_type=EventType.INSTALLATION_COMPLETED,
                priority=NotificationPriority.NORMAL,
                channels=[NotificationType.IN_APP, NotificationType.EMAIL]
            )
            if instance.dealer:
                NotificationService.send(
                    recipient=instance.dealer,
                    title="Customer Job Completed",
                    message=f"A job for your customer {instance.customer.full_name} has been completed.",
                    event_type=EventType.INSTALLATION_COMPLETED,
                    priority=NotificationPriority.NORMAL,
                    channels=[NotificationType.IN_APP]
                )

# -------------------------------------------------------------------------
# PAYMENT NOTIFICATIONS
# Note: The Payment module currently does not exist. 
# Once the Payment model is built, uncomment and hook this up!
# -------------------------------------------------------------------------
# @receiver(post_save, sender='payments.Payment')
# def notify_on_payment_success(sender, instance, created, **kwargs):
#     if instance.status == "SUCCESS":
#         NotificationService.send(
#             recipient=instance.customer,
#             title="Payment Successful",
#             message=f"Your payment of {instance.amount} has been received successfully.",
#             event_type=EventType.PAYMENT_SUCCESS,
#             priority=NotificationPriority.HIGH,
#             channels=[NotificationType.IN_APP, NotificationType.EMAIL, NotificationType.SMS]
#         )
