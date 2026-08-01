from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from firebase_admin import auth

from .firebase import initialize_firebase
from .models import User


class FirebaseAuthentication(BaseAuthentication):

    def authenticate(self, request):

        initialize_firebase()

        authorization = request.headers.get("Authorization")

        if not authorization:
            return None

        if not authorization.startswith("Bearer "):
            raise AuthenticationFailed("Invalid Authorization Header")

        id_token = authorization.split(" ")[1]

        try:

            decoded_token = auth.verify_id_token(id_token)

        except Exception:
            raise AuthenticationFailed("Invalid Firebase Token")

        firebase_uid = decoded_token["uid"]

        email = decoded_token.get("email")

        name = decoded_token.get("name", "")

        user, created = User.objects.get_or_create(

            firebase_uid=firebase_uid,

            defaults={

                "email": email,

                "full_name": name,

                "is_verified": True,

            }

        )

        return (user, None)