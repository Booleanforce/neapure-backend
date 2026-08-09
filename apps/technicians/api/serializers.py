from rest_framework import serializers

from apps.accounts.models import User
from apps.technicians.models import (
    TechnicianProfile,
    TechnicianJob,
)


class TechnicianProfileSerializer(
    serializers.ModelSerializer
):
    profile_photo = serializers.SerializerMethodField()

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

    def get_profile_photo(self, obj):
        if not obj.profile_photo:
            return None

        request = self.context.get("request")

        url = obj.profile_photo.url

        if request:
            return request.build_absolute_uri(url)

        return url

class TechnicianSerializer(
    serializers.ModelSerializer
):
    technician_profile = TechnicianProfileSerializer(
        required=False
    )

    class Meta:
        model = User

        fields = [
            "id",
            "email",
            "full_name",
            "phone",
            "role",
            "is_active",
            "created_at",
            "technician_profile",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "role",
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