from rest_framework.permissions import BasePermission, SAFE_METHODS

from shared.constants.roles import UserRole


class IsAdminOrReadOnly(BasePermission):
    """
    Public product catalog.

    Anyone can:
        - GET
        - HEAD
        - OPTIONS

    Only admin users can:
        - POST
        - PUT
        - PATCH
        - DELETE
    """

    def has_permission(self, request, view):

        # -----------------------------------------------------
        # PUBLIC READ ACCESS
        # -----------------------------------------------------

        if request.method in SAFE_METHODS:
            return True

        # -----------------------------------------------------
        # WRITE ACCESS REQUIRES LOGIN
        # -----------------------------------------------------

        if not request.user or not request.user.is_authenticated:
            return False

        # -----------------------------------------------------
        # ADMIN ACCESS
        # -----------------------------------------------------

        return request.user.role in (
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_ADMIN,
        )