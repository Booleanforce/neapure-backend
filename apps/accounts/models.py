from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from shared.mixins.base import BaseModel
from shared.mixins.uuid import UUIDMixin
from shared.mixins.soft_delete import SoftDeleteModel

from .managers import UserManager

from shared.constants.roles import UserRole


class User(
    AbstractBaseUser,
    PermissionsMixin,
    SoftDeleteModel,
    BaseModel,
):

    email = models.EmailField(
        unique=True
    )

    full_name = models.CharField(
        max_length=255,
        blank=True,
        default=""
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        default=""
    )

    photo = models.ImageField(
        upload_to="users/profile/",
        blank=True,
        null=True,
        default="",
    )

    firebase_uid = models.CharField(
        max_length=255,
        unique=True,
        blank=True,
        null=True,
)

    role = models.CharField(
        max_length=30,
        choices=UserRole.choices,
        default=UserRole.CUSTOMER,
    )

    is_staff = models.BooleanField(
        default=False
    )

    is_active = models.BooleanField(
        default=True
    )

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:

        db_table = "users"

        ordering = ["-created_at"]

    def __str__(self):

        return self.email