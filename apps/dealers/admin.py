from django.contrib import admin
from apps.dealers.models import DealerProfile
from apps.customers.models import CustomerProfile
from apps.products.models import RegisteredProduct
from apps.installations.models import InstallationRequest

class DealerProfileInline(admin.StackedInline):
    model = DealerProfile
    can_delete = False
    verbose_name_plural = "Dealer Profile"
    readonly_fields = ("total_customers_registered",)

    def total_customers_registered(self, instance):
        if instance and instance.user:
            count = instance.user.registered_customers.count()
            return f"{count} Customers"
        return "0 Customers"
    
    total_customers_registered.short_description = "Total Customers Registered"

class RegisteredCustomerInline(admin.TabularInline):
    model = CustomerProfile
    fk_name = "registered_by"
    can_delete = False
    extra = 0
    verbose_name = "Registered Customer"
    verbose_name_plural = "Customers Registered by this Dealer"
    fields = ("user", "status", "created_at")
    readonly_fields = ("user", "status", "created_at")

    def has_add_permission(self, request, obj=None):
        return False

class RegisteredProductInline(admin.TabularInline):
    model = RegisteredProduct
    fk_name = "dealer"
    can_delete = False
    extra = 0
    verbose_name = "Product Sold"
    verbose_name_plural = "Products Sold by this Dealer"
    fields = ("product", "customer", "serial_number", "purchase_date")
    readonly_fields = ("product", "customer", "serial_number", "purchase_date")

    def has_add_permission(self, request, obj=None):
        return False

class InstallationRequestInline(admin.TabularInline):
    model = InstallationRequest
    fk_name = "dealer"
    can_delete = False
    extra = 0
    verbose_name = "Installation Request"
    verbose_name_plural = "Installation Requests Submitted by this Dealer"
    fields = ("registered_product", "customer", "status", "created_at")
    readonly_fields = ("registered_product", "customer", "status", "created_at")

    def has_add_permission(self, request, obj=None):
        return False
