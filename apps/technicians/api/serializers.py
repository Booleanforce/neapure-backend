from rest_framework import serializers

from apps.accounts.models import User
from apps.technicians.models import (
    TechnicianProfile,
    TechnicianJob,
)


class TechnicianProfileSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = TechnicianProfile

        fields = [
            "id",
            "region",
            "skills",
            "status",
            "profile_photo",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class TechnicianSerializer(
    serializers.ModelSerializer
):
    technician_profile = (
        TechnicianProfileSerializer(
            required=False
        )
    )

    class Meta:
        model = User

        fields = [
            "id",
            "email",
            "full_name",
            "phone",
            "role",
            "language",
            "is_active",
            "created_at",
            "technician_profile",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "role",
            "is_active",
        ]


class TechnicianJobSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = TechnicianJob

        fields = "__all__"

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class TechnicianPerformanceSerializer(
    serializers.Serializer
):
    technician_id = serializers.UUIDField()

    full_name = serializers.CharField()

    email = serializers.EmailField()

    status = serializers.CharField()

    total_jobs = serializers.IntegerField()

    completed_jobs = serializers.IntegerField()

    pending_jobs = serializers.IntegerField()

    cancelled_jobs = serializers.IntegerField()

    average_rating = serializers.FloatField(
        allow_null=True
    )