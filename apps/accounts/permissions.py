from rest_framework.permissions import BasePermission

from shared.constants.roles import UserRole


class IsSuperAdmin(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == UserRole.SUPER_ADMIN
        )


class IsOperationsAdmin(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == UserRole.OPERATIONS_ADMIN
        )


class IsAdminUser(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in [
                UserRole.SUPER_ADMIN,
                UserRole.OPERATIONS_ADMIN,
            ]
        )


class IsDealer(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == UserRole.DEALER
        )


class IsTechnician(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == UserRole.TECHNICIAN
        )


class IsCustomer(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == UserRole.CUSTOMER
        )