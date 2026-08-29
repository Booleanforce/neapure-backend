from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from apps.accounts.models import User
from shared.constants.roles import UserRole
from apps.customers.models import CustomerProfile, CustomerAddress, CustomerNote, CustomerHistory
from apps.customers.api.serializers import (
    CustomerSerializer,
    CustomerAddressSerializer,
    CustomerNoteSerializer
)
from apps.accounts.permissions import IsSuperAdmin, IsDealer, IsCustomer
from apps.accounts.services.account_service import AccountService

class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["email", "full_name", "phone", "customer_profile__alternate_phone"]
    ordering_fields = ["created_at", "email", "full_name"]
    ordering = ["-created_at"]
    filterset_fields = ["customer_profile__status", "addresses__city", "is_active"]

    def get_queryset(self):
        user = self.request.user
        queryset = User.objects.filter(role=UserRole.CUSTOMER, is_deleted=False).select_related("customer_profile").prefetch_related("addresses", "notes", "history_logs")
        
        if user.role == UserRole.CUSTOMER:
            return queryset.filter(id=user.id)
        elif user.role == UserRole.DEALER:
            return queryset.filter(customer_profile__registered_by=user)
        
        return queryset

    def get_permissions(self):
        if self.action in ["list", "create"]:
            # Admin & Dealer driven CRM - Customers do not list or create
            permission_classes = [IsAuthenticated, IsSuperAdmin | IsDealer]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data["role"] = UserRole.CUSTOMER

        profile_data = data.pop("customer_profile", {})
        addresses = data.pop("addresses", [])

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        user = AccountService.create_user(serializer.validated_data)

        profile, _ = CustomerProfile.objects.get_or_create(user=user)

        profile.alternate_phone = profile_data.get(
            "alternate_phone",
            ""
        )

        profile.status = profile_data.get(
            "status",
            "NEW"
        )

        profile.registered_by = request.user

        profile.save()

        valid_keys = [f.name for f in CustomerAddress._meta.get_fields()]
        for address in addresses:
            if "address_line_1" in address:
                address["full_address"] = address.pop("address_line_1")
            if "state" in address:
                address["division_state"] = address.pop("state")
            
            clean_address = {k: v for k, v in address.items() if k in valid_keys}
            CustomerAddress.objects.create(
                customer=user,
                **clean_address,
            )

        CustomerHistory.objects.create(
            customer=user,
            event_type="Registration",
            description=f"Customer registered by {request.user.email}.",
            performed_by=request.user,
        )

        return Response(
            CustomerSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)

        instance = self.get_object()

        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
        )

        serializer.is_valid(raise_exception=True)

        old_status = None
        new_status = None

        # Existing status
        if hasattr(instance, "customer_profile"):
            old_status = instance.customer_profile.status

        profile_data = request.data.get("customer_profile", {})

        if profile_data:
            new_status = profile_data.get("status")

        # Serializer updates:
        # - User
        # - CustomerProfile
        # - CustomerAddress
        serializer.save()

        # Create history if status changed
        if (
            old_status
            and new_status
            and old_status != new_status
        ):
            CustomerHistory.objects.create(
                customer=instance,
                event_type="Status Change",
                description=f"Status changed from {old_status} to {new_status}.",
                performed_by=request.user,
            )
        addresses = request.data.get("addresses", [])

        if addresses:

            address_data = addresses[0]

            address, created = CustomerAddress.objects.get_or_create(
                customer=instance,
                is_default=True,
                defaults=address_data,
            )

            if not created:

                for key, value in address_data.items():
                    setattr(address, key, value)

                address.save()

        return Response(
            self.get_serializer(instance).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def address(self, request, pk=None):
        customer = self.get_object()
        
        if request.user.role == UserRole.CUSTOMER and request.user != customer:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        serializer = CustomerAddressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(customer=customer)
        
        CustomerHistory.objects.create(
            customer=customer,
            event_type="Address Added",
            description=f"New address added in {serializer.validated_data.get('city')}.",
            performed_by=request.user
        )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def notes(self, request, pk=None):
        customer = self.get_object()
        
        if request.user.role == UserRole.CUSTOMER:
            return Response({"error": "Customers cannot add notes"}, status=status.HTTP_403_FORBIDDEN)

        serializer = CustomerNoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(customer=customer, author=request.user)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    


    def destroy(self, request, *args, **kwargs):
        customer = self.get_object()

        CustomerHistory.objects.create(
            customer=customer,
            event_type="Deleted",
            description=f"Customer deleted by {request.user.email}.",
            performed_by=request.user,
        )

        customer.is_deleted = True
        customer.deleted_at = timezone.now()
        customer.is_active = False

        customer.save(
            update_fields=[
                "is_deleted",
                "deleted_at",
                "is_active",
            ]
        )

        return Response(
            {"message": "Customer deleted successfully."},
            status=status.HTTP_200_OK,
        )