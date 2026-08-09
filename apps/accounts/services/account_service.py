from apps.accounts.models import User


class AccountService:

    @staticmethod
    def create_user(validated_data):
        """
        Create a user account.

        firebase_uid is handled separately because the current
        UserManager.create_user() does not accept it directly.
        """

        password = validated_data.pop("password", None)

        # Remove firebase_uid before passing data to UserManager
        firebase_uid = validated_data.pop("firebase_uid", None)

        # Create user using the existing UserManager
        user = User.objects.create_user(
            password=password,
            **validated_data,
        )

        # Set Firebase UID after user creation
        if firebase_uid:
            user.firebase_uid = firebase_uid
            user.save(update_fields=["firebase_uid"])

        return user

    @staticmethod
    def update_user(user, validated_data):

        for field, value in validated_data.items():
            setattr(user, field, value)

        user.save()

        return user

    @staticmethod
    def delete_user(user):
        user.delete()