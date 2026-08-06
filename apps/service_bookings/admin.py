from django.contrib import admin
from apps.service_bookings.models import ServiceBooking, ServiceBookingNote, ServiceStatusHistory

class ServiceBookingNoteInline(admin.TabularInline):
    model = ServiceBookingNote
    extra = 0
    readonly_fields = ("author", "created_at")

class ServiceStatusHistoryInline(admin.TabularInline):
    model = ServiceStatusHistory
    extra = 0
    readonly_fields = ("old_status", "new_status", "changed_by", "created_at")
    can_delete = False

@admin.register(ServiceBooking)
class ServiceBookingAdmin(admin.ModelAdmin):
    list_display = ("booking_id", "customer_name", "phone", "service_type", "status", "assigned_to", "created_at")
    list_filter = ("status", "service_type", "division")
    search_fields = ("booking_id", "customer_name", "phone", "product_model_text")
    inlines = [ServiceBookingNoteInline, ServiceStatusHistoryInline]
    readonly_fields = ("booking_id", "created_at", "updated_at")
