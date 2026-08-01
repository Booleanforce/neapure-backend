from rest_framework.permissions import BasePermission

from shared.constants.roles import UserRole


class UserObjectPermission(BasePermission):

    def has_object_permission(self, request, view, obj):

        if request.user.role == UserRole.SUPER_ADMIN:
            return True

        if request.user.role == UserRole.OPERATIONS_ADMIN:

            return obj.role != UserRole.SUPER_ADMIN

        return obj.id == request.user.id