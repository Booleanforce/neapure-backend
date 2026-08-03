from rest_framework import serializers
from apps.customers.models import CustomerProfile, CustomerAddress, CustomerNote, CustomerHistory
from apps.accounts.api.serializers import UserSerializer

class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = ("alternate_phone", "status")

class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerAddress
        fields = (
            "id",
            "country",
            "division_state",
            "city",
            "area",
            "postal_code",
            "full_address",
            "latitude",
            "longitude",
            "is_default",
            "created_at",
        )

class CustomerNoteSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.full_name", read_only=True)
    author_email = serializers.CharField(source="author.email", read_only=True)

    class Meta:
        model = CustomerNote
        fields = ("id", "author_name", "author_email", "text", "created_at")

class CustomerHistorySerializer(serializers.ModelSerializer):
    performed_by_name = serializers.CharField(source="performed_by.full_name", read_only=True)

    class Meta:
        model = CustomerHistory
        fields = ("id", "event_type", "description", "performed_by_name", "created_at")

class CustomerSerializer(UserSerializer):
    customer_profile = CustomerProfileSerializer(read_only=True)
    addresses = CustomerAddressSerializer(many=True, read_only=True)
    notes = CustomerNoteSerializer(many=True, read_only=True)
    history_logs = CustomerHistorySerializer(many=True, read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            "customer_profile",
            "addresses",
            "notes",
            "history_logs"
        )
