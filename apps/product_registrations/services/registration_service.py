import io

import qrcode
from dateutil.relativedelta import relativedelta
from django.db import transaction
from django.core.files.base import ContentFile
from django.utils import timezone
from django.conf import settings

from apps.product_registrations.models import ProductRegistration, ProductTimelineEvent
from apps.product_registrations.constants import (
    InstallationStatus,
    WarrantyStatus,
    TimelineEventType,
)


class RegistrationService:

    @staticmethod
    def _generate_qr_code(registration):
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr_data = f"{settings.FRONTEND_URL}/verify/{registration.id}"
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        
        file_name = f"qr_{registration.serial_number}_{registration.id}.png"
        
        registration.qr_code_data = qr_data
        registration.qr_code_image.save(file_name, ContentFile(buffer.getvalue()), save=False)

    @staticmethod
    @transaction.atomic
    def register_product(
        product,
        serial_number,
        customer,
        dealer=None,
        installation_address="",
        gps_latitude=None,
        gps_longitude=None,
        registered_by=None,
    ):

        registration = ProductRegistration(
            product=product,
            serial_number=serial_number,
            customer=customer,
            dealer=dealer,
            installation_address=installation_address,
            gps_latitude=gps_latitude,
            gps_longitude=gps_longitude,
        )

        registration.save()

        # Generate QR code after save (needs ID)
        RegistrationService._generate_qr_code(registration)
        registration.save(update_fields=["qr_code_data", "qr_code_image"])

        ProductTimelineEvent.objects.create(
            registration=registration,
            event_type=TimelineEventType.REGISTERED,
            created_by=registered_by,
        )

        return registration

    @staticmethod
    @transaction.atomic
    def activate_warranty(registration, actor=None):

        registration.warranty_status = WarrantyStatus.ACTIVE
        start_date = timezone.now().date()
        registration.warranty_start_date = start_date
        registration.warranty_end_date = start_date + relativedelta(
            months=registration.product.warranty_duration_months
        )
        registration.save(
            update_fields=["warranty_status", "warranty_start_date", "warranty_end_date"]
        )

        ProductTimelineEvent.objects.create(
            registration=registration,
            event_type=TimelineEventType.WARRANTY_ACTIVATED,
            created_by=actor,
        )

        return registration

    @staticmethod
    @transaction.atomic
    def assign_technician(registration, technician, actor=None):

        registration.assigned_technician = technician
        registration.save(update_fields=["assigned_technician"])

        ProductTimelineEvent.objects.create(
            registration=registration,
            event_type=TimelineEventType.TECHNICIAN_ASSIGNED,
            created_by=actor,
        )

        return registration

    @staticmethod
    @transaction.atomic
    def update_installation_status(registration, status, actor=None, note=""):

        registration.installation_status = status
        registration.save(update_fields=["installation_status"])

        event_mapping = {
            InstallationStatus.SCHEDULED: TimelineEventType.INSTALLATION_SCHEDULED,
            InstallationStatus.COMPLETED: TimelineEventType.INSTALLED,
        }

        event_type = event_mapping.get(status, TimelineEventType.NOTE)
        description = note if event_type != TimelineEventType.NOTE else f"Installation status updated to {status}. {note}".strip()

        ProductTimelineEvent.objects.create(
            registration=registration,
            event_type=event_type,
            description=description,
            created_by=actor,
        )

        return registration

    @staticmethod
    @transaction.atomic
    def regenerate_qr_code(registration, actor=None):

        RegistrationService._generate_qr_code(registration)
        registration.save(update_fields=["qr_code_data", "qr_code_image"])

        ProductTimelineEvent.objects.create(
            registration=registration,
            event_type=TimelineEventType.NOTE,
            description="QR code regenerated",
            created_by=actor,
        )

        return registration

    @staticmethod
    @transaction.atomic
    def transfer_warranty(registration, new_customer, actor=None):

        registration.customer = new_customer
        registration.warranty_status = WarrantyStatus.TRANSFERRED
        registration.save(update_fields=["customer", "warranty_status"])

        ProductTimelineEvent.objects.create(
            registration=registration,
            event_type=TimelineEventType.WARRANTY_TRANSFERRED,
            created_by=actor,
        )

        return registration
