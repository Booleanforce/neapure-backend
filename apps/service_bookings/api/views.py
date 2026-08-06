from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from shared.responses.api_response import ApiResponse

from apps.service_bookings.models import ServiceBooking
from apps.service_bookings.api.serializers import (
    ServiceBookingCreateSerializer, 
    ServiceBookingListSerializer, 
    ServiceBookingDetailSerializer
)
from apps.service_bookings.services.booking_service import BookingService
from apps.service_bookings.selectors.booking_selector import BookingSelector
from apps.service_bookings.filters import BookingFilter
from apps.service_bookings.permissions import CanCreateBooking, CanViewBookings, CanManageBookings

User = get_user_model()

class ServiceBookingViewSet(viewsets.ModelViewSet):
    queryset = ServiceBooking.objects.filter(is_deleted=False)
    filterset_class = BookingFilter
    search_fields = ["customer_name", "phone", "booking_id"]
    
    def get_permissions(self):
        if self.action == "create":
            return [CanCreateBooking()]
        elif self.action in ["list", "retrieve", "stats", "add_note"]:
            return [CanViewBookings()]
        return [CanManageBookings()]
        
    def get_serializer_class(self):
        if self.action == "create":
            return ServiceBookingCreateSerializer
        if self.action == "list":
            return ServiceBookingListSerializer
        return ServiceBookingDetailSerializer

    @extend_schema(tags=["Service Bookings"])
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        booking = BookingService.create_booking(serializer.validated_data)
        
        return Response({
            "message": "Thank you! Your service request has been submitted successfully. Our support team will contact you shortly.",
            "booking_id": booking.booking_id
        }, status=status.HTTP_201_CREATED)

    @extend_schema(tags=["Service Bookings"])
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.soft_delete()
        return ApiResponse.success(message="Booking soft-deleted successfully.", status=200)

    @extend_schema(tags=["Service Bookings"])
    @action(detail=True, methods=["post"])
    def add_note(self, request, pk=None):
        booking = self.get_object()
        note_text = request.data.get("note")
        if not note_text:
            return Response({"error": "Note text is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        BookingService.add_note(booking, request.user, note_text)
        return Response({"status": "Note added"}, status=status.HTTP_200_OK)

    @extend_schema(tags=["Service Bookings"])
    @action(detail=True, methods=["post"])
    def update_status(self, request, pk=None):
        booking = self.get_object()
        new_status = request.data.get("status")
        if not new_status:
            return Response({"error": "Status is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        BookingService.update_status(booking, new_status, request.user)
        return Response({"status": "Status updated"}, status=status.HTTP_200_OK)

    @extend_schema(tags=["Service Bookings"])
    @action(detail=True, methods=["post"])
    def assign_technician(self, request, pk=None):
        booking = self.get_object()
        tech_id = request.data.get("technician_id")
        if not tech_id:
            return Response({"error": "technician_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            technician = User.objects.get(id=tech_id)
            BookingService.assign_technician(booking, technician, request.user)
            return Response({"status": "Technician assigned"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(tags=["Service Bookings"])
    @action(detail=False, methods=["get"])
    def stats(self, request):
        stats = BookingSelector.get_dashboard_stats()
        return Response(stats, status=status.HTTP_200_OK)

    @extend_schema(tags=["Service Bookings"])
    @action(detail=False, methods=["get"])
    def export(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        return BookingService.export_bookings_csv(queryset)
