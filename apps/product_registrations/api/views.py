from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers

from apps.product_registrations.models import ProductRegistration
from apps.product_registrations.api.serializers import (
    ProductRegistrationListSerializer,
    ProductRegistrationDetailSerializer,
    ProductRegistrationCreateSerializer,
    ProductRegistrationAdminEditSerializer,
    QRVerifySerializer,
)
from apps.product_registrations.selectors.registration_selector import RegistrationSelector
from apps.product_registrations.services.registration_service import RegistrationService
from apps.product_registrations.filters import RegistrationFilter
from apps.product_registrations.permissions import (
    CanRegisterProduct,
    CanManageWarranty,
    CanRegenerateQR,
    CanAssignTechnician,
    CanUpdateInstallationStatus,
)
from apps.product_registrations.constants import InstallationStatus

from shared.responses.api_response import ApiResponse
from shared.constants.roles import UserRole


@extend_schema_view(
    list=extend_schema(
        tags=["Product Registrations"],
        description="List all registrations scoped to user role. Admin sees all.",
    ),
    retrieve=extend_schema(
        tags=["Product Registrations"],
        description="Retrieve full registration details.",
    ),
    create=extend_schema(
        tags=["Product Registrations"],
        description="Register a new product (DEALER, OPERATIONS_ADMIN, SUPER_ADMIN).",
    ),
    update=extend_schema(
        tags=["Product Registrations"],
        description="Update address/gps (OPERATIONS_ADMIN, SUPER_ADMIN).",
    ),
    partial_update=extend_schema(
        tags=["Product Registrations"],
        description="Partially update address/gps (OPERATIONS_ADMIN, SUPER_ADMIN).",
    ),
    destroy=extend_schema(
        tags=["Product Registrations"],
        description="Soft delete a registration (OPERATIONS_ADMIN, SUPER_ADMIN).",
    ),
)
class ProductRegistrationViewSet(viewsets.ModelViewSet):
    
    filterset_class = RegistrationFilter

    def get_queryset(self):
        user = self.request.user
        
        if user.role == UserRole.CUSTOMER:
            return RegistrationSelector.get_customer_products(user)
        elif user.role == UserRole.DEALER:
            return RegistrationSelector.get_dealer_registrations(user)
        elif user.role == UserRole.TECHNICIAN:
            return RegistrationSelector.get_technician_jobs(user)
        else:
            return RegistrationSelector.get_registrations()

    def get_serializer_class(self):
        if self.action == "list":
            return ProductRegistrationListSerializer
        elif self.action == "retrieve":
            return ProductRegistrationDetailSerializer
        elif self.action == "create":
            return ProductRegistrationCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return ProductRegistrationAdminEditSerializer
        return ProductRegistrationListSerializer

    def get_permissions(self):
        if self.action == "create":
            return [CanRegisterProduct()]
        elif self.action in ["update", "partial_update", "destroy"]:
            # Need to use CanManageWarranty or similar logic for admins
            # Reusing CanRegenerateQR since it maps to the exact admin roles needed
            return [CanRegenerateQR()]
        return super().get_permissions()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return ApiResponse.success(
            data=serializer.data,
            message="Registration retrieved successfully.",
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        registration = serializer.save()
        return ApiResponse.success(
            data=ProductRegistrationDetailSerializer(
                registration, context={"request": request}
            ).data,
            message="Product registered successfully.",
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return ApiResponse.success(
            data=ProductRegistrationDetailSerializer(
                instance, context={"request": request}
            ).data,
            message="Registration updated successfully.",
        )

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return ApiResponse.success(
            data=ProductRegistrationDetailSerializer(
                instance, context={"request": request}
            ).data,
            message="Registration updated successfully.",
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.get_serializer().Meta.model.objects.filter(pk=instance.pk).update(
            is_deleted=True,
            deleted_at=timezone.now(),
            updated_at=timezone.now()
        )
        return ApiResponse.success(
            message="Registration soft-deleted.",
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Product Registrations"],
        request=None,
        description="Activate warranty and start tracking duration.",
    )
    @action(detail=True, methods=["post"], permission_classes=[CanManageWarranty])
    def activate_warranty(self, request, pk=None):
        registration = self.get_object()
        registration = RegistrationService.activate_warranty(
            registration, actor=request.user
        )
        return ApiResponse.success(
            data=ProductRegistrationDetailSerializer(
                registration, context={"request": request}
            ).data,
            message="Warranty activated successfully.",
        )

    @extend_schema(
        tags=["Product Registrations"],
        request=inline_serializer(
            name="AssignTechnicianRequest",
            fields={"technician_id": serializers.UUIDField()},
        ),
        description="Assign a technician.",
    )
    @action(detail=True, methods=["post"], permission_classes=[CanAssignTechnician])
    def assign_technician(self, request, pk=None):
        registration = self.get_object()
        technician_id = request.data.get("technician_id")
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            technician = User.objects.get(id=technician_id)
            if technician.role != UserRole.TECHNICIAN:
                return ApiResponse.error(
                    message="User must have the TECHNICIAN role.",
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except User.DoesNotExist:
            return ApiResponse.error(
                message="Technician not found.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        registration = RegistrationService.assign_technician(
            registration, technician, actor=request.user
        )
        return ApiResponse.success(
            data=ProductRegistrationDetailSerializer(
                registration, context={"request": request}
            ).data,
            message="Technician assigned successfully.",
        )

    @extend_schema(
        tags=["Product Registrations"],
        request=None,
        description="Regenerate QR code image and data.",
    )
    @action(detail=True, methods=["post"], permission_classes=[CanRegenerateQR])
    def regenerate_qr_code(self, request, pk=None):
        registration = self.get_object()
        registration = RegistrationService.regenerate_qr_code(
            registration, actor=request.user
        )
        return ApiResponse.success(
            data=ProductRegistrationDetailSerializer(
                registration, context={"request": request}
            ).data,
            message="QR code regenerated.",
        )

    @extend_schema(
        tags=["Product Registrations"],
        request=inline_serializer(
            name="TransferWarrantyRequest",
            fields={"new_customer_id": serializers.UUIDField()},
        ),
        description="Transfer warranty to a new customer.",
    )
    @action(detail=True, methods=["post"], permission_classes=[CanManageWarranty])
    def transfer_warranty(self, request, pk=None):
        registration = self.get_object()
        new_customer_id = request.data.get("new_customer_id")
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            new_customer = User.objects.get(id=new_customer_id)
            if new_customer.role != UserRole.CUSTOMER:
                return ApiResponse.error(
                    message="Target user must have the CUSTOMER role.",
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except User.DoesNotExist:
            return ApiResponse.error(
                message="Customer not found.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        registration = RegistrationService.transfer_warranty(
            registration, new_customer, actor=request.user
        )
        return ApiResponse.success(
            data=ProductRegistrationDetailSerializer(
                registration, context={"request": request}
            ).data,
            message="Warranty transferred successfully.",
        )

    @extend_schema(
        tags=["Product Registrations"],
        request=inline_serializer(
            name="UpdateInstallationStatusRequest",
            fields={
                "status": serializers.ChoiceField(choices=InstallationStatus.choices),
                "note": serializers.CharField(required=False, allow_blank=True),
            },
        ),
        description="Update installation status (e.g. SCHEDULED, COMPLETED).",
    )
    @action(detail=True, methods=["post"], permission_classes=[CanUpdateInstallationStatus])
    def update_installation_status(self, request, pk=None):
        registration = self.get_object()
        new_status = request.data.get("status")
        note = request.data.get("note", "")

        if new_status not in InstallationStatus.values:
            return ApiResponse.error(
                message=f"Invalid status. Must be one of {InstallationStatus.values}.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        registration = RegistrationService.update_installation_status(
            registration, new_status, actor=request.user, note=note
        )
        return ApiResponse.success(
            data=ProductRegistrationDetailSerializer(
                registration, context={"request": request}
            ).data,
            message="Installation status updated.",
        )

    @extend_schema(
        tags=["Product Registrations"],
        responses={200: QRVerifySerializer},
        description="Public view for scanning a QR code to verify registration.",
    )
    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def verify_qr(self, request, pk=None):
        registration = self.get_object()
        serializer = QRVerifySerializer(registration)
        return ApiResponse.success(
            data=serializer.data,
            message="QR verification successful.",
        )
