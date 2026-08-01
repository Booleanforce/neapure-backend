from django.db import models


class UserStatus(models.TextChoices):

    ACTIVE = (
        "ACTIVE",
        "Active",
    )

    INACTIVE = (
        "INACTIVE",
        "Inactive",
    )

    BLOCKED = (
        "BLOCKED",
        "Blocked",
    )

    SUSPENDED = (
        "SUSPENDED",
        "Suspended",
    )