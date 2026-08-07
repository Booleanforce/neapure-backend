from django.db import models

class NotificationType(models.TextChoices):
    IN_APP = "IN_APP", "In-App"
    PUSH = "PUSH", "Push Notification"
    EMAIL = "EMAIL", "Email"
    SMS = "SMS", "SMS"

class EventType(models.TextChoices):
    INSTALLATION_ASSIGNED = "INSTALLATION_ASSIGNED", "Installation Assigned"
    TECHNICIAN_ON_THE_WAY = "TECHNICIAN_ON_THE_WAY", "Technician On The Way"
    INSTALLATION_COMPLETED = "INSTALLATION_COMPLETED", "Installation Completed"
    SERVICE_REMINDER = "SERVICE_REMINDER", "Service Reminder"
    WARRANTY_EXPIRY = "WARRANTY_EXPIRY", "Warranty Expiry"
    FILTER_REPLACEMENT = "FILTER_REPLACEMENT", "Filter Replacement"
    PAYMENT_SUCCESS = "PAYMENT_SUCCESS", "Payment Success"
    REPLACEMENT_KIT_SHIPPED = "REPLACEMENT_KIT_SHIPPED", "Replacement Kit Shipped"
    GENERAL = "GENERAL", "General Notification"

class NotificationPriority(models.TextChoices):
    LOW = "LOW", "Low"
    NORMAL = "NORMAL", "Normal"
    HIGH = "HIGH", "High"
