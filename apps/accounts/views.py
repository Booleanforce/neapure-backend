from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User
from apps.accounts.api.serializers import UserSerializer
from .object_permissions import UserObjectPermission

from .filters import UserFilter
from .permissions import (
    IsAdminUser,
    IsSuperAdmin,
)
from .selectors.user_selector import UserSelector


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    filterset_class = UserFilter

    search_fields = [
        "email",
        "full_name",
        "phone",
    ]

    ordering_fields = [
        "email",
        "full_name",
        "created_at",
    ]

    ordering = [
        "-created_at",
    ]

    def get_queryset(self):
        return UserSelector.get_users(self.request.user)

    def get_serializer_class(self):
        return UserSerializer

    def get_permissions(self):
        """
        SUPER_ADMIN
            - Full Access

        OPERATIONS_ADMIN
            - List
            - Retrieve
            - Update
            - Profile
            - Statistics

        CUSTOMER / DEALER / TECHNICIAN
            - Only Profile
        """

        if self.action in [
            "admin_dashboard",
            "statistics",
        ]:
            permission_classes = [
                IsAuthenticated,
                IsAdminUser,
            ]

        elif self.action == "super_admin_dashboard":
            permission_classes = [
                IsAuthenticated,
                IsSuperAdmin,
            ]

        else:
            permission_classes = [
                IsAuthenticated,
            ]

        return [permission() for permission in permission_classes]

    def get_object(self):

        obj = super().get_object()

        self.check_object_permissions(
            self.request,
            obj,
        )

        return obj

    @action(detail=False, methods=["get"])
    def profile(self, request):
        serializer = self.get_serializer(request.user)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"])
    def statistics(self, request):
        return Response(
            UserSelector.statistics(),
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"])
    def admin_dashboard(self, request):
        return Response(
            {
                "message": "Welcome Admin",
                "user": UserSerializer(request.user).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"])
    def super_admin_dashboard(self, request):
        return Response(
            {
                "message": "Welcome Super Admin",
                "user": UserSerializer(request.user).data,
            },
            status=status.HTTP_200_OK,
        )