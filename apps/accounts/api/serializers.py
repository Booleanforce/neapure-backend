from django.contrib.auth import authenticate

from rest_framework import serializers

from apps.accounts.models import User


class UserSerializer(serializers.ModelSerializer):

    photo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "full_name",
            "phone",
            "photo",
            "role",
            "firebase_uid",
            "is_active",
            "created_at",
        )

    def get_photo(self, obj):
        if obj.photo and hasattr(obj.photo, "url"):
            return obj.photo.url
        return None


class UserProfileUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            "full_name",
            "phone",
            "photo",
        )


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
            "photo",
            "role",
        )
        extra_kwargs = {
            "role": {
                "required": False,
            }
        }

    def validate_email(self, value):

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Email already exists."
            )

        return value


class PasswordSetupSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        from django.utils.http import urlsafe_base64_decode
        from django.utils.encoding import force_str
        from django.contrib.auth.tokens import PasswordResetTokenGenerator
        from apps.accounts.models import User

        try:
            uid = force_str(urlsafe_base64_decode(attrs.get("uid")))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("Invalid user identifier.")

        if not PasswordResetTokenGenerator().check_token(user, attrs.get("token")):
            raise serializers.ValidationError("Invalid or expired setup token.")

        attrs["user"] = user
        return attrs


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