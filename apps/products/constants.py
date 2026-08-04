from django.db import models


class ProductType(models.TextChoices):

    PURIFIER = (
        "PURIFIER",
        "Purifier",
    )

    FILTER = (
        "FILTER",
        "Filter",
    )

    REPLACEMENT_KIT = (
        "REPLACEMENT_KIT",
        "Replacement Kit",
    )


class ProductStatus(models.TextChoices):

    ACTIVE = (
        "ACTIVE",
        "Active",
    )

    INACTIVE = (
        "INACTIVE",
        "Inactive",
    )

    DRAFT = (
        "DRAFT",
        "Draft",
    )

    OUT_OF_STOCK = (
        "OUT_OF_STOCK",
        "Out of Stock",
    )
