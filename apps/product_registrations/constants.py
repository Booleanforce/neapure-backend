from django.db import models


class InstallationStatus(models.TextChoices):

    PENDING = (
        "PENDING",
        "Pending",
    )

    SCHEDULED = (
        "SCHEDULED",
        "Scheduled",
    )

    IN_PROGRESS = (
        "IN_PROGRESS",
        "In Progress",
    )

    COMPLETED = (
        "COMPLETED",
        "Completed",
    )

    CANCELLED = (
        "CANCELLED",
        "Cancelled",
    )


class WarrantyStatus(models.TextChoices):

    NOT_ACTIVATED = (
        "NOT_ACTIVATED",
        "Not Activated",
    )

    ACTIVE = (
        "ACTIVE",
        "Active",
    )

    EXPIRING_SOON = (
        "EXPIRING_SOON",
        "Expiring Soon",
    )

    EXPIRED = (
        "EXPIRED",
        "Expired",
    )

    TRANSFERRED = (
        "TRANSFERRED",
        "Transferred",
    )


class TimelineEventType(models.TextChoices):

    REGISTERED = (
        "REGISTERED",
        "Registered",
    )

    INSTALLATION_SCHEDULED = (
        "INSTALLATION_SCHEDULED",
        "Installation Scheduled",
    )

    TECHNICIAN_ASSIGNED = (
        "TECHNICIAN_ASSIGNED",
        "Technician Assigned",
    )

    INSTALLED = (
        "INSTALLED",
        "Installed",
    )

    WARRANTY_ACTIVATED = (
        "WARRANTY_ACTIVATED",
        "Warranty Activated",
    )

    SERVICE_BOOKED = (
        "SERVICE_BOOKED",
        "Service Booked",
    )

    FILTER_REPLACED = (
        "FILTER_REPLACED",
        "Filter Replaced",
    )

    WARRANTY_EXPIRED = (
        "WARRANTY_EXPIRED",
        "Warranty Expired",
    )

    WARRANTY_TRANSFERRED = (
        "WARRANTY_TRANSFERRED",
        "Warranty Transferred",
    )

    NOTE = (
        "NOTE",
        "Note",
    )
