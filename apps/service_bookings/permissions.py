from rest_framework.permissions import BasePermission
from shared.constants.roles import UserRole

class CanCreateBooking(BasePermission):
    def has_permission(self, request, view):
        return True

class CanViewBookings(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in [UserRole.SUPER_ADMIN, UserRole.OPERATIONS_ADMIN]

class CanManageBookings(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in [UserRole.SUPER_ADMIN, UserRole.OPERATIONS_ADMIN]
