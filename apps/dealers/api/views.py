from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.accounts.models import User
from shared.constants.roles import UserRole
from apps.dealers.models import DealerProfile
from apps.dealers.api.serializers import DealerSerializer
from apps.accounts.permissions import IsSuperAdmin, IsDealer
from apps.accounts.services.account_service import AccountService

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.accounts.models import User
from shared.constants.roles import UserRole

from apps.dealers.api.serializers import DealerSerializer

from apps.accounts.permissions import IsAdminUser
from apps.accounts.services.account_service import AccountService


class AdminDealerViewSet(viewsets.ModelViewSet):
    """
    API for Admins to manage Dealers.
    Dealers cannot access this endpoint.
    """

    serializer_class = DealerSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["email", "full_name", "phone", "dealer_profile__company_name"]
    ordering_fields = ["created_at", "email", "full_name"]
    ordering = ["-created_at"]

    filterset_fields = [
        "dealer_profile__status",
        "is_active",
    ]

    def get_queryset(self):
        return (
            User.objects
            .filter(role=UserRole.DEALER)
            .select_related("dealer_profile")
        )

    # ---------------------------------------------------------
    # CREATE
    # ---------------------------------------------------------

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data["role"] = UserRole.DEALER
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        # Inject password from request data since it's not in the serializer fields
        validated_data = serializer.validated_data.copy()
        validated_data["password"] = request.data.get("password", "")
        validated_data["role"] = UserRole.DEALER
        
        # Prevent unique constraint violation on firebase_uid
        import uuid
        if not validated_data.get("firebase_uid"):
            validated_data["firebase_uid"] = f"pending_{uuid.uuid4()}"
        
        # Pop nested profile data so User.objects.create_user doesn't fail
        validated_data.pop("dealer_profile", None)
        
        user = AccountService.create_user(validated_data)

        data = request.data.copy()

        # Force dealer role
        data["role"] = UserRole.DEALER

        # Password is required when creating a dealer
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

        # Validate user data
        serializer = self.get_serializer(
            data=data
        )

        serializer.is_valid(
            raise_exception=True
        )

        # Create User
        user = AccountService.create_user(
            serializer.validated_data
        )

        # -----------------------------------------------------
        # Dealer Profile
        # -----------------------------------------------------

        profile_data = request.data.get(
            "dealer_profile",
            {}
        )

        if isinstance(profile_data, dict):

            profile = user.dealer_profile

            profile.company_name = (
                profile_data.get(
                    "company_name",
                    ""
                )
            )

            profile.contact_person = (
                profile_data.get(
                    "contact_person",
                    ""
                )
            )

            profile.trade_license = (
                profile_data.get(
                    "trade_license",
                    ""
                )
            )

            profile.status = (
                profile_data.get(
                    "status",
                    profile.status
                )
            )

            profile.save()

        return Response(
            self.get_serializer(user).data,
            status=status.HTTP_201_CREATED,
        )

    # ---------------------------------------------------------
    # UPDATE
    # ---------------------------------------------------------

    def update(
        self,
        request,
        *args,
        **kwargs
    ):
        partial = kwargs.pop(
            "partial",
            False
        )

        instance = self.get_object()

        # -----------------------------------------------------
        # User data
        # -----------------------------------------------------

        user_data = request.data.copy()

        # Never change dealer role
        user_data.pop(
            "role",
            None
        )

        # Password is optional during update
        password = user_data.get(
            "password"
        )

        if not password:
            user_data.pop(
                "password",
                None
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

        # -----------------------------------------------------
        # Dealer Profile
        # -----------------------------------------------------

        profile_data = request.data.get(
            "dealer_profile",
            {}
        )

        if isinstance(profile_data, dict):

            profile = instance.dealer_profile

            if "company_name" in profile_data:
                profile.company_name = (
                    profile_data[
                        "company_name"
                    ]
                )

            if "contact_person" in profile_data:
                profile.contact_person = (
                    profile_data[
                        "contact_person"
                    ]
                )

            if "trade_license" in profile_data:
                profile.trade_license = (
                    profile_data[
                        "trade_license"
                    ]
                )

            if "status" in profile_data:
                profile.status = (
                    profile_data[
                        "status"
                    ]
                )

            profile.save()

        return Response(
            self.get_serializer(
                instance
            ).data
        )

    # ---------------------------------------------------------
    # DELETE
    # ---------------------------------------------------------

    def destroy(
        self,
        request,
        *args,
        **kwargs
    ):
        instance = self.get_object()

        try:
            # Delete/soft-delete dealer profile
            if hasattr(
                instance,
                "dealer_profile"
            ):
                instance.dealer_profile.delete()

            # Delete/soft-delete user
            instance.delete()

            return Response(
                status=status.HTTP_204_NO_CONTENT
            )

        except Exception as error:

            return Response(
                {
                    "detail":
                        f"Failed to delete dealer: {error}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

from rest_framework import generics
from apps.accounts.permissions import IsDealer

class DealerMeView(generics.RetrieveUpdateAPIView):
    """
    API for Dealers to view and update their own profile.
    """
    serializer_class = DealerSerializer
    permission_classes = [IsAuthenticated, IsDealer]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # User update
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Profile update
        profile = instance.dealer_profile
        profile_data = request.data.get("dealer_profile", {})
        if profile_data:
            # Dealers cannot change their own status, only profile details
            if "company_name" in profile_data:
                profile.company_name = profile_data["company_name"]
            if "contact_person" in profile_data:
                profile.contact_person = profile_data["contact_person"]
            if "trade_license" in profile_data:
                profile.trade_license = profile_data["trade_license"]
            profile.save()

        return Response(self.get_serializer(instance).data)
