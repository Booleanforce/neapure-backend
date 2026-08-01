from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from shared.constants.roles import UserRole
from apps.installations.models import InstallationRequest, InstallationStatus
from apps.installations.api.serializers import InstallationRequestSerializer
from apps.accounts.permissions import IsAdminUser

class InstallationRequestViewSet(viewsets.ModelViewSet):
    """
    API for Dealers to request installations, and Admins to approve them.
    """
    serializer_class = InstallationRequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["registered_product__serial_number", "customer__email"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]
    filterset_fields = ["status"]

    def get_queryset(self):
        user = self.request.user
        queryset = InstallationRequest.objects.select_related("registered_product", "dealer", "customer")
        
        if user.role == UserRole.DEALER:
            return queryset.filter(dealer=user)
        elif user.role == UserRole.CUSTOMER:
            return queryset.filter(customer=user)
            
        return queryset

    def create(self, request, *args, **kwargs):
        # Customers cannot request directly
        if request.user.role == UserRole.CUSTOMER:
            return Response({"error": "Customers cannot request installations directly."}, status=status.HTTP_403_FORBIDDEN)
            
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        dealer = request.user if request.user.role == UserRole.DEALER else None
        
        # We explicitly don't pass status, so it defaults to PENDING
        serializer.save(dealer=dealer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        # Dealers cannot update an existing request, they can only create
        if request.user.role == UserRole.DEALER:
            return Response({"error": "Dealers cannot modify installation requests."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=["patch"], permission_classes=[IsAuthenticated, IsAdminUser])
    def approve(self, request, pk=None):
        instance = self.get_object()
        instance.status = InstallationStatus.APPROVED
        
        admin_notes = request.data.get("admin_notes", "")
        if admin_notes:
            instance.admin_notes = admin_notes
            
        instance.save(update_fields=["status", "admin_notes"])
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=["patch"], permission_classes=[IsAuthenticated, IsAdminUser])
    def reject(self, request, pk=None):
        instance = self.get_object()
        instance.status = InstallationStatus.REJECTED
        
        admin_notes = request.data.get("admin_notes", "")
        if admin_notes:
            instance.admin_notes = admin_notes
            
        instance.save(update_fields=["status", "admin_notes"])
        return Response(self.get_serializer(instance).data)
