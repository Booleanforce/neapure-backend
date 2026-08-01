from django.contrib.auth import authenticate

from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken


class AuthService:

    @staticmethod
    def generate_tokens(user):

        refresh = RefreshToken.for_user(user)

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }

    @staticmethod
    def login(email, password):

        user = authenticate(
            email=email,
            password=password,
        )

        if user is None:
            raise AuthenticationFailed(
                "Invalid email or password."
            )

        tokens = AuthService.generate_tokens(user)

        return {
            "user": user,
            **tokens,
        }

    @staticmethod
    def logout(refresh_token):

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            raise AuthenticationFailed(
                "Invalid refresh token."
            )