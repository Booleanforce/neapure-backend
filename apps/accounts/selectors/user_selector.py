from django.db.models import Count

from apps.accounts.models import User

from shared.constants.roles import UserRole


class UserSelector:

    @staticmethod
    def get_users(current_user):

        if current_user.role == UserRole.SUPER_ADMIN:
            return User.objects.all()

        if current_user.role == UserRole.OPERATIONS_ADMIN:
            return User.objects.exclude(
                role=UserRole.SUPER_ADMIN
            )

        return User.objects.filter(
            id=current_user.id
        )

    @staticmethod
    def statistics():

        return {

            "total_users": User.objects.count(),

            "active_users": User.objects.filter(
                is_active=True
            ).count(),

            "inactive_users": User.objects.filter(
                is_active=False
            ).count(),

            "roles": User.objects.values(
                "role"
            ).annotate(
                total=Count("id")
            ),

        }