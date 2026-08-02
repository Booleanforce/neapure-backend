import datetime

from django.utils import timezone
from django.shortcuts import get_object_or_404

from apps.product_registrations.models import ProductRegistration
from apps.product_registrations.constants import WarrantyStatus


class RegistrationSelector:

    @staticmethod
    def get_registrations():

        return ProductRegistration.objects.filter(
            is_deleted=False,
        ).select_related(
            "product",
            "customer",
            "dealer",
            "assigned_technician",
        ).prefetch_related(
            "timeline",
        )

    @staticmethod
    def get_by_serial_number(serial_number):

        return ProductRegistration.objects.filter(
            serial_number=serial_number,
            is_deleted=False,
        ).first()

    @staticmethod
    def get_by_id(registration_id):

        return get_object_or_404(
            ProductRegistration.objects.filter(is_deleted=False),
            id=registration_id,
        )

    @staticmethod
    def get_expiring_warranties(days=90):

        today = timezone.now().date()
        target_date = today + datetime.timedelta(days=days)

        return ProductRegistration.objects.filter(
            is_deleted=False,
            warranty_status=WarrantyStatus.ACTIVE,
            warranty_end_date__lte=target_date,
            warranty_end_date__gte=today,
        )

    @staticmethod
    def get_customer_products(customer):

        return ProductRegistration.objects.filter(
            customer=customer,
            is_deleted=False,
        ).select_related("product")

    @staticmethod
    def get_dealer_registrations(dealer):

        return ProductRegistration.objects.filter(
            dealer=dealer,
            is_deleted=False,
        ).select_related("product", "customer")

    @staticmethod
    def get_technician_jobs(technician):

        return ProductRegistration.objects.filter(
            assigned_technician=technician,
            is_deleted=False,
        ).select_related("product", "customer")
