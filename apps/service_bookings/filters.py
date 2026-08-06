import django_filters
from apps.service_bookings.models import ServiceBooking

class BookingFilter(django_filters.FilterSet):
    class Meta:
        model = ServiceBooking
        fields = {
            "status": ["exact"],
            "service_type": ["exact"],
            "assigned_to": ["exact"],
            "division": ["exact"],
            "district": ["exact"],
        }
