import django_filters

from .models import ProductRegistration


class RegistrationFilter(django_filters.FilterSet):

    installation_status = django_filters.CharFilter(
        field_name="installation_status",
        lookup_expr="exact",
    )

    warranty_status = django_filters.CharFilter(
        field_name="warranty_status",
        lookup_expr="exact",
    )

    customer = django_filters.UUIDFilter(
        field_name="customer__id",
        lookup_expr="exact",
    )

    dealer = django_filters.UUIDFilter(
        field_name="dealer__id",
        lookup_expr="exact",
    )

    technician = django_filters.UUIDFilter(
        field_name="assigned_technician__id",
        lookup_expr="exact",
    )

    serial_number = django_filters.CharFilter(
        field_name="serial_number",
        lookup_expr="exact",
    )

    class Meta:

        model = ProductRegistration

        fields = [
            "installation_status",
            "warranty_status",
            "customer",
            "dealer",
            "technician",
            "serial_number",
        ]
