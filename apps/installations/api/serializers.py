from rest_framework import serializers
from apps.installations.models import InstallationRequest

class InstallationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstallationRequest
        fields = ("id", "registered_product", "dealer", "customer", "status", "admin_notes", "created_at", "updated_at")
        read_only_fields = ("status", "dealer", "admin_notes")
