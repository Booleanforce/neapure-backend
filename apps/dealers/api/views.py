from django.db import transaction

from rest_framework import (
    viewsets,
    status,
    generics,
)
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import models, transaction
from django_filters.rest_framework import (
    DjangoFilterBackend,
)
from rest_framework.filters import (
    SearchFilter,
    OrderingFilter,
)

from apps.accounts.models import User
from apps.accounts.permissions import (
    IsSuperAdmin,
    IsDealer,
)
from apps.accounts.services.account_service import (
    AccountService,
)

from shared.constants.roles import UserRole

from apps.dealers.models import DealerProfile
from apps.dealers.api.serializers import (
    DealerSerializer,
)


class AdminDealerViewSet(viewsets.ModelViewSet):
    """
    API for Super Admins to manage Dealers.
    """

    serializer_class = DealerSerializer

    permission_classes = [
        IsAuthenticated,
        IsSuperAdmin,
    ]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    search_fields = [
        "email",
        "full_name",
        "phone",
        "dealer_profile__company_name",
    ]

    ordering_fields = [
        "created_at",
        "email",
        "full_name",
    ]

    ordering = [
        "-created_at",
    ]

    filterset_fields = [
        "dealer_profile__status",
        "is_active",
    ]

    def get_queryset(self):
        return (
            User.objects
            .filter(
                role=UserRole.DEALER,
                is_deleted=False,
            )
            .select_related(
                "dealer_profile"
            )
        )

    @transaction.atomic
    def create(
        self,
        request,
        *args,
        **kwargs,
    ):
        data = request.data.copy()

        password = data.get("password")

        if not password:
            return Response(
                {
                    "password": [
                        "Password is required."
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data["role"] = UserRole.DEALER

        if not data.get("firebase_uid"):
            import uuid

            data["firebase_uid"] = (
                f"pending_{uuid.uuid4()}"
            )

        profile_data = data.get(
            "dealer_profile",
            {},
        )

        if not isinstance(
            profile_data,
            dict,
        ):
            profile_data = {}

        serializer = self.get_serializer(
            data=data
        )

        serializer.is_valid(
            raise_exception=True
        )

        validated_data = (
            serializer.validated_data.copy()
        )

        validated_data.pop(
            "dealer_profile",
            None,
        )

        validated_data["password"] = password
        validated_data["role"] = UserRole.DEALER

        user = (
            AccountService.create_user(
                validated_data
            )
        )

        profile = (
            DealerProfile.objects.create(
                user=user
            )
        )

        if "company_name" in profile_data:
            profile.company_name = (
                profile_data["company_name"]
            )

        if "contact_person" in profile_data:
            profile.contact_person = (
                profile_data["contact_person"]
            )

        if "trade_license" in profile_data:
            profile.trade_license = (
                profile_data["trade_license"]
            )

        if "status" in profile_data:
            profile.status = (
                profile_data["status"]
            )

        profile.save()

        user.refresh_from_db()

        return Response(
            self.get_serializer(user).data,
            status=status.HTTP_201_CREATED,
        )

    @transaction.atomic
    def update(
        self,
        request,
        *args,
        **kwargs,
    ):
        partial = kwargs.pop(
            "partial",
            False,
        )

        instance = self.get_object()

        user_data = request.data.copy()

        user_data.pop(
            "role",
            None,
        )

        user_data.pop(
            "dealer_profile",
            None,
        )

        password = user_data.get(
            "password"
        )

        if not password:
            user_data.pop(
                "password",
                None,
            )

        serializer = self.get_serializer(
            instance,
            data=user_data,
            partial=partial,
        )

        serializer.is_valid(
            raise_exception=True
        )

        self.perform_update(serializer)

        profile_data = request.data.get(
            "dealer_profile",
            {},
        )

        if not isinstance(
            profile_data,
            dict,
        ):
            profile_data = {}

        if profile_data:
            profile, _ = (
                DealerProfile.objects.get_or_create(
                    user=instance
                )
            )

            if "company_name" in profile_data:
                profile.company_name = (
                    profile_data["company_name"]
                )

            if "contact_person" in profile_data:
                profile.contact_person = (
                    profile_data["contact_person"]
                )

            if "trade_license" in profile_data:
                profile.trade_license = (
                    profile_data["trade_license"]
                )

            if "status" in profile_data:
                profile.status = (
                    profile_data["status"]
                )

            profile.save()

        instance.refresh_from_db()

        return Response(
            self.get_serializer(instance).data,
            status=status.HTTP_200_OK,
        )

    def partial_update(
        self,
        request,
        *args,
        **kwargs,
    ):
        kwargs["partial"] = True

        return self.update(
            request,
            *args,
            **kwargs,
        )

    @transaction.atomic
    def destroy(
        self,
        request,
        *args,
        **kwargs,
    ):
        user = self.get_object()

        # Prevent self deletion
        if user.id == request.user.id:
            return Response(
                {
                    "success": False,
                    "detail": "You cannot delete your own account.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_id = str(user.id)
        user_name = user.full_name
        user_email = user.email

        try:
            # IMPORTANT:
            # Bypass SoftDeleteModel.delete() and any custom
            # delete() implementation in BaseModel.
            #
            # This calls Django's actual Model.delete().
            models.Model.delete(user)

            return Response(
                {
                    "success": True,
                    "message": "User permanently deleted.",
                    "id": user_id,
                    "name": user_name,
                    "email": user_email,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as error:
            return Response(
                {
                    "success": False,
                    "detail": f"Failed to permanently delete user: {error}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class DealerMeView(
    generics.RetrieveUpdateAPIView
):
    """
    API for Dealers to view and update
    their own profile.
    """

    serializer_class = DealerSerializer

    permission_classes = [
        IsAuthenticated,
        IsDealer,
    ]

    def get_object(self):
        return self.request.user

    @transaction.atomic
    def update(
        self,
        request,
        *args,
        **kwargs,
    ):
        partial = kwargs.pop(
            "partial",
            False,
        )

        instance = self.get_object()

        user_data = request.data.copy()

        user_data.pop(
            "role",
            None,
        )

        user_data.pop(
            "dealer_profile",
            None,
        )

        user_data.pop(
            "status",
            None,
        )

        serializer = self.get_serializer(
            instance,
            data=user_data,
            partial=partial,
        )

        serializer.is_valid(
            raise_exception=True
        )

        self.perform_update(serializer)

        profile_data = request.data.get(
            "dealer_profile",
            {},
        )

        if not isinstance(
            profile_data,
            dict,
        ):
            profile_data = {}

        if profile_data:
            profile, _ = (
                DealerProfile.objects.get_or_create(
                    user=instance
                )
            )

            if "company_name" in profile_data:
                profile.company_name = (
                    profile_data["company_name"]
                )

            if "contact_person" in profile_data:
                profile.contact_person = (
                    profile_data["contact_person"]
                )

            if "trade_license" in profile_data:
                profile.trade_license = (
                    profile_data["trade_license"]
                )

            profile.save()

        instance.refresh_from_db()

        return Response(
            self.get_serializer(instance).data,
            status=status.HTTP_200_OK,
        )