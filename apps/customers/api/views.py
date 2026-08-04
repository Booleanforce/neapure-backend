from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.accounts.models import User
from shared.constants.roles import UserRole
from apps.customers.models import CustomerProfile, CustomerAddress, CustomerNote, CustomerHistory
from apps.customers.api.serializers import (
    CustomerSerializer,
    CustomerAddressSerializer,
    CustomerNoteSerializer
)
from apps.accounts.permissions import IsAdminUser, IsDealer, IsCustomer
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
        queryset = User.objects.filter(role=UserRole.CUSTOMER).select_related("customer_profile").prefetch_related("addresses", "notes", "history_logs")
        
        if user.role == UserRole.CUSTOMER:
            return queryset.filter(id=user.id)
        elif user.role == UserRole.DEALER:
            return queryset.filter(customer_profile__registered_by=user)
        
        return queryset

    def get_permissions(self):
        if self.action in ["list", "create"]:
            # Admin & Dealer driven CRM - Customers do not list or create
            permission_classes = [IsAuthenticated, IsAdminUser | IsDealer]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        # Admin-driven customer registration
        data = request.data.copy()
        data["role"] = UserRole.CUSTOMER
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        # Inject password from request data since it's not in the serializer fields
        validated_data = serializer.validated_data.copy()
        validated_data["password"] = request.data.get("password", "")
        
        # Prevent unique constraint violation on firebase_uid
        import uuid
        if not validated_data.get("firebase_uid"):
            validated_data["firebase_uid"] = f"pending_{uuid.uuid4()}"
        
        user = AccountService.create_user(validated_data)
        
        # Log History
        CustomerHistory.objects.create(
            customer=user,
            event_type="Registration",
            description=f"Customer registered by {request.user.email}.",
            performed_by=request.user
        )
        
        # Link customer to the dealer or admin who registered them
        profile = user.customer_profile
        profile.registered_by = request.user
        profile.save(update_fields=["registered_by"])

        return Response(CustomerSerializer(user).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # User update
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Profile update
        profile = instance.customer_profile
        profile_data = request.data.get("customer_profile", {})
        
        if profile_data:
            if "alternate_phone" in profile_data:
                profile.alternate_phone = profile_data["alternate_phone"]
            
            if "status" in profile_data and request.user.role in [UserRole.SUPER_ADMIN, UserRole.OPERATIONS_ADMIN]:
                old_status = profile.status
                new_status = profile_data["status"]
                
                if old_status != new_status:
                    profile.status = new_status
                    CustomerHistory.objects.create(
                        customer=instance,
                        event_type="Status Change",
                        description=f"Status changed from {old_status} to {new_status}.",
                        performed_by=request.user
                    )
                    
            profile.save()

        return Response(self.get_serializer(instance).data)

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
