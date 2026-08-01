from django.db import models

from .uuid import UUIDMixin


class BaseModel(
    UUIDMixin,
    models.Model,
):
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        abstract = True