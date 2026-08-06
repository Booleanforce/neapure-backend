import csv
from django.db import transaction
from django.core.exceptions import ValidationError
from django.http import HttpResponse

from apps.service_bookings.models import ServiceBooking, ServiceBookingNote, ServiceStatusHistory
from shared.constants.roles import UserRole

class BookingService:

    @staticmethod
    @transaction.atomic
    def create_booking(data):
        booking = ServiceBooking.objects.create(**data)
        
        ServiceStatusHistory.objects.create(
            booking=booking,
            old_status="",
            new_status=booking.status,
            changed_by=None
        )
        return booking

    @staticmethod
    @transaction.atomic
    def update_status(booking, new_status, actor):
        old_status = booking.status
        if old_status != new_status:
            booking.status = new_status
            booking.save(update_fields=["status", "updated_at"])
            
            ServiceStatusHistory.objects.create(
                booking=booking,
                old_status=old_status,
                new_status=new_status,
                changed_by=actor
            )
        return booking

    @staticmethod
    @transaction.atomic
    def assign_technician(booking, technician, actor):
        if technician.role != UserRole.TECHNICIAN:
            raise ValidationError("Assigned user must be a TECHNICIAN.")
            
        booking.assigned_to = technician
        booking.save(update_fields=["assigned_to", "updated_at"])
        return booking

    @staticmethod
    def add_note(booking, author, note_text):
        return ServiceBookingNote.objects.create(
            booking=booking,
            author=author,
            note=note_text
        )

    @staticmethod
    def export_bookings_csv(queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="service_bookings.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            "Booking ID", "Customer Name", "Phone", "Product", "Service Type",
            "Preferred Date", "Status", "Assigned Technician", "Created Date"
        ])
        
        for b in queryset:
            product_name = b.product.name if b.product else b.product_model_text
            tech_name = b.assigned_to.email if b.assigned_to else "Unassigned"
            
            writer.writerow([
                b.booking_id,
                b.customer_name,
                b.phone,
                product_name,
                b.service_type,
                b.preferred_date.strftime("%Y-%m-%d") if b.preferred_date else "",
                b.status,
                tech_name,
                b.created_at.strftime("%Y-%m-%d %H:%M:%S")
            ])
            
        return response
