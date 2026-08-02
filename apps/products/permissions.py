from rest_framework.permissions import BasePermission

from shared.constants.roles import UserRole


class IsAdminOrReadOnly(BasePermission):
    """
    Allow read-only access (GET, HEAD, OPTIONS) to any authenticated user.
    Write operations (POST, PUT, PATCH, DELETE) are restricted to
    Super Admin and Operations Admin roles.
    """

    def has_permission(self, request, view):

        if not request.user.is_authenticated:
            return False

        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True

        return request.user.role in [
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_ADMIN,
        ]
