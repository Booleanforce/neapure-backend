import logging
from django.core.mail import send_mail
from django.conf import settings
from apps.notifications.models import Notification
from shared.constants.notifications import NotificationType, EventType, NotificationPriority

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Centralized service for dispatching notifications across multiple channels.
    """

    @classmethod
    def send(
        cls,
        recipient,
        title,
        message,
        event_type=EventType.GENERAL,
        priority=NotificationPriority.NORMAL,
        channels=None,
        link=None,
        metadata=None,
    ):
        if channels is None:
            channels = [NotificationType.IN_APP]
        
        if metadata is None:
            metadata = {}

        created_notifications = []

        for channel in channels:
            if channel == NotificationType.IN_APP:
                notification = cls._create_in_app_notification(
                    recipient=recipient,
                    title=title,
                    message=message,
                    event_type=event_type,
                    priority=priority,
                    link=link,
                    metadata=metadata
                )
                created_notifications.append(notification)
            
            elif channel == NotificationType.EMAIL:
                cls._send_email_notification(recipient, title, message)
            
            elif channel == NotificationType.PUSH:
                cls._send_push_notification(recipient, title, message, metadata)
            
            elif channel == NotificationType.SMS:
                cls._send_sms_notification(recipient, title, message)
            
            else:
                logger.warning(f"Unsupported notification channel: {channel}")

        return created_notifications

    @staticmethod
    def _create_in_app_notification(recipient, title, message, event_type, priority, link, metadata):
        return Notification.objects.create(
            recipient=recipient,
            title=title,
            message=message,
            notification_type=NotificationType.IN_APP,
            event_type=event_type,
            priority=priority,
            link=link,
            metadata=metadata
        )

    @staticmethod
    def _send_email_notification(recipient, title, message):
        if not recipient.email:
            logger.warning(f"Cannot send email to user {recipient.id}: No email address.")
            return

        try:
            send_mail(
                subject=title,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=True,
            )
            logger.info(f"Email sent successfully to {recipient.email}")
        except Exception as e:
            logger.error(f"Failed to send email to {recipient.email}: {str(e)}")

    @staticmethod
    def _send_push_notification(recipient, title, message, metadata):
        # Placeholder for Firebase Cloud Messaging (FCM) integration
        # e.g., using firebase-admin SDK
        logger.info(f"[PUSH NOTIFICATION SIMULATED] To: {recipient.id} | Title: {title}")

    @staticmethod
    def _send_sms_notification(recipient, title, message):
        # Placeholder for SMS gateway integration (e.g., Twilio, AWS SNS)
        phone = getattr(recipient, "phone", None)
        if not phone:
            logger.warning(f"Cannot send SMS to user {recipient.id}: No phone number.")
            return
        logger.info(f"[SMS NOTIFICATION SIMULATED] To: {phone} | Message: {message}")
