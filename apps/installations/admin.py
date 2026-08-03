from django.contrib import admin
from apps.installations.models import InstallationRequest

@admin.register(InstallationRequest)
class InstallationRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "dealer", "customer", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("dealer__email", "customer__email", "registered_product__serial_number")
    readonly_fields = ("dealer", "customer", "registered_product", "created_at", "updated_at")
    
    # We allow the admin to change status and add admin_notes
    fields = ("registered_product", "dealer", "customer", "status", "admin_notes", "created_at", "updated_at")
