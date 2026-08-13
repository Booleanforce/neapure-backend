from django.contrib import admin
from apps.installations.models import (
    InstallationRequest,
    InstallationHistory,
    InstallationPhoto,
    InstallationChecklist,
    InstallationSignature,
    ReplacementKitRequest
)

class InstallationHistoryInline(admin.TabularInline):
    model = InstallationHistory
    extra = 0
    readonly_fields = ["event_type", "description", "performed_by", "created_at"]
    can_delete = False

class InstallationPhotoInline(admin.TabularInline):
    model = InstallationPhoto
    extra = 0
    readonly_fields = ["photo_type", "photo", "uploaded_by", "created_at"]
    can_delete = False

@admin.register(InstallationRequest)
class InstallationRequestAdmin(admin.ModelAdmin):
    list_display = ["id", "registered_product", "dealer", "customer", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["dealer__email", "customer__email", "registered_product__serial_number"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [InstallationHistoryInline, InstallationPhotoInline]

@admin.register(InstallationChecklist)
class InstallationChecklistAdmin(admin.ModelAdmin):
    list_display = ["id", "installation", "submitted_by", "created_at"]

@admin.register(InstallationSignature)
class InstallationSignatureAdmin(admin.ModelAdmin):
    list_display = ["id", "installation", "collected_by", "created_at"]

@admin.register(ReplacementKitRequest)
class ReplacementKitRequestAdmin(admin.ModelAdmin):
    list_display = ["id", "registered_product", "dealer", "customer", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["dealer__email", "customer__email", "registered_product__serial_number"]
