from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
import uuid

from shared.mixins.base import BaseModel

from .managers import UserManager

from shared.constants.roles import UserRole


class User(
    AbstractBaseUser,
    PermissionsMixin,
    BaseModel,
):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

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
        default=""
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