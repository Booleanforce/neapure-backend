from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers

from apps.accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    """Read/update serializer for the authenticated user's own profile."""

    photo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "full_name",
            "phone",
            "location",
            "photo",
            "role",
            "language",
            "firebase_uid",
        )
        read_only_fields = (
            "id",
            "email",         # change via a verified email-change flow, not here
            "role",          # role changes go through an admin endpoint
            "firebase_uid",  # set only by the auth flow, never client-editable
        )

    def get_photo(self, obj):
        if obj.photo and hasattr(obj.photo, "url"):
            return obj.photo.url
        return None


class AvatarUploadSerializer(serializers.ModelSerializer):
    """Dedicated serializer for the photo upload endpoint."""

    class Meta:
        model = User
        fields = ("photo",)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate_new_password(self, value):
        validate_password(value, user=self.context["request"].user)
        return value

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    class Meta:
        model = User
        fields = (
            "email",
            "password",
            "full_name",
            "phone",
        )
        # role intentionally excluded — new accounts always default to
        # UserRole.CUSTOMER at the model level; clients can never set it here

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Email already exists."
            )
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(
            password=password,
            **validated_data,
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()

    password = serializers.CharField(
        write_only=True
    )

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(
            email=email,
            password=password,
        )

        if user is None:
            raise serializers.ValidationError(
                "Invalid email or password."
            )

        if not user.is_active:
            raise serializers.ValidationError(
                "User account is disabled."
            )

        attrs["user"] = user
        return attrs