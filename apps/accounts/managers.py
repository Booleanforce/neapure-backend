from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):

    def create_user(
        self,
        email,
        full_name="",
        phone="",
        photo=None,
        role="CUSTOMER",
        password=None,
        **extra_fields
    ):

        if not email:
            raise ValueError("Email is required.")

        email = self.normalize_email(email)

        extra_fields.setdefault("language", "en")
        extra_fields.setdefault("location", "Unknown")

        user = self.model(
            email=email,
            full_name=full_name,
            phone=phone,
            photo=photo,
            role=role,
            **extra_fields
        )

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)

        return user

    def create_superuser(
        self,
        email,
        password,
        **extra_fields
    ):

        extra_fields.setdefault(
            "is_staff",
            True
        )

        extra_fields.setdefault(
            "is_superuser",
            True
        )

        extra_fields.setdefault(
            "is_active",
            True
        )

        return self.create_user(
            email,
            password=password,
            **extra_fields
        )
