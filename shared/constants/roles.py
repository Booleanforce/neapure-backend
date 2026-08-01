from django.db import models


class UserRole(models.TextChoices):

    SUPER_ADMIN = (
        "SUPER_ADMIN",
        "Super Admin",
    )

    OPERATIONS_ADMIN = (
        "OPERATIONS_ADMIN",
        "Operations Admin",
    )

    TECHNICIAN = (
        "TECHNICIAN",
        "Technician",
    )

    DEALER = (
        "DEALER",
        "Dealer",
    )

    CUSTOMER = (
        "CUSTOMER",
        "Customer",
    )