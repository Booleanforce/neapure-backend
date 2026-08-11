from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "full_name",
        "role",
        "is_active",
        "is_staff",
    )

    search_fields = (
        "email",
        "full_name",
    )

    list_filter = (
        "role",
        "is_active",
        "is_staff",
    )

    def save_model(self, request, obj, form, change):
        is_new = not change
        super().save_model(request, obj, form, change)
        if is_new:
            from apps.accounts.services.account_service import AccountService
            AccountService._send_welcome_email(obj)