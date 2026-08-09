from rest_framework import serializers
from apps.installations.models import InstallationRequest, ReplacementKitRequest

class InstallationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstallationRequest
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "status", "admin_notes", "dealer"]

class ReplacementKitRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReplacementKitRequest
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "status", "admin_notes", "dealer"]
