from rest_framework.permissions import BasePermission

from shared.constants.roles import UserRole


class CanRegisterProduct(BasePermission):
    """
    Allows create only if request.user.role in 
    [DEALER, OPERATIONS_ADMIN, SUPER_ADMIN].
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return request.user.role in [
            UserRole.DEALER,
            UserRole.OPERATIONS_ADMIN,
            UserRole.SUPER_ADMIN,
        ]


class CanManageWarranty(BasePermission):
    """
    Allows operations only if role in [OPERATIONS_ADMIN, SUPER_ADMIN].
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return request.user.role in [
            UserRole.OPERATIONS_ADMIN,
            UserRole.SUPER_ADMIN,
        ]


class CanRegenerateQR(BasePermission):
    """
    Allows regenerate_qr_code only if role in [OPERATIONS_ADMIN, SUPER_ADMIN].
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return request.user.role in [
            UserRole.OPERATIONS_ADMIN,
            UserRole.SUPER_ADMIN,
        ]


class CanAssignTechnician(BasePermission):
    """
    Allows technician assignment only if role in [OPERATIONS_ADMIN, SUPER_ADMIN].
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return request.user.role in [
            UserRole.OPERATIONS_ADMIN,
            UserRole.SUPER_ADMIN,
        ]


class CanUpdateInstallationStatus(BasePermission):
    """
    Allows installation status update only if role in [OPERATIONS_ADMIN, SUPER_ADMIN].
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return request.user.role in [
            UserRole.OPERATIONS_ADMIN,
            UserRole.SUPER_ADMIN,
        ]
