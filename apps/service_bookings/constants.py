from django.db import models
from django.utils.translation import gettext_lazy as _

class ServiceType(models.TextChoices):
    INSTALLATION = "INSTALLATION", _("Installation")
    REPAIR = "REPAIR", _("Repair")
    MAINTENANCE = "MAINTENANCE", _("Maintenance")
    FILTER_REPLACEMENT = "FILTER_REPLACEMENT", _("Filter Replacement")
    WATER_QUALITY_CHECK = "WATER_QUALITY_CHECK", _("Water Quality Check")
    GENERAL_SERVICE = "GENERAL_SERVICE", _("General Service")


class BookingStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    CONTACTED = "CONTACTED", _("Contacted")
    SCHEDULED = "SCHEDULED", _("Scheduled")
    IN_PROGRESS = "IN_PROGRESS", _("In Progress")
    COMPLETED = "COMPLETED", _("Completed")
    CANCELLED = "CANCELLED", _("Cancelled")
