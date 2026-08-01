from apps.accounts.models import User


class AccountService:

    @staticmethod
    def create_user(validated_data):

        password = validated_data.pop("password")

        return User.objects.create_user(
            password=password,
            **validated_data,
        )

    @staticmethod
    def update_user(user, validated_data):

        for field, value in validated_data.items():
            setattr(user, field, value)

        user.save()

        return user

    @staticmethod
    def delete_user(user):
        user.delete()