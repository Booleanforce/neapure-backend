from django.shortcuts import get_object_or_404
from django.utils import timezone
from apps.service_bookings.models import ServiceBooking
from apps.service_bookings.constants import BookingStatus

class BookingSelector:
    
    @staticmethod
    def get_bookings(filters=None):
        qs = ServiceBooking.objects.filter(is_deleted=False)
        if filters:
            pass # Filters will be applied by DRF FilterSet
        return qs
        
    @staticmethod
    def get_by_booking_id(booking_id):
        return get_object_or_404(
            ServiceBooking.objects.filter(is_deleted=False),
            booking_id=booking_id
        )
        
    @staticmethod
    def get_dashboard_stats():
        qs = ServiceBooking.objects.filter(is_deleted=False)
        today = timezone.now().date()
        
        return {
            "total": qs.count(),
            "pending": qs.filter(status=BookingStatus.PENDING).count(),
            "completed": qs.filter(status=BookingStatus.COMPLETED).count(),
            "today": qs.filter(created_at__date=today).count(),
        }
