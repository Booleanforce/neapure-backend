from django.contrib import admin

from .models import ProductRegistration, ProductTimelineEvent


class ProductTimelineEventInline(admin.TabularInline):

    model = ProductTimelineEvent
    extra = 0
    readonly_fields = ("event_type", "description", "created_by", "created_at")

    def has_add_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ProductRegistration)
class ProductRegistrationAdmin(admin.ModelAdmin):

    list_display = (
        "serial_number",
        "customer",
        "installation_status",
        "warranty_status",
    )

    list_filter = (
        "installation_status",
        "warranty_status",
    )

    search_fields = (
        "serial_number",
        "customer__email",
        "customer__full_name",
    )

    inlines = [ProductTimelineEventInline]
