from rest_framework import serializers
from apps.customers.models import CustomerProfile, CustomerAddress, CustomerNote, CustomerHistory
from apps.accounts.api.serializers import (
    UserSerializer,
    RegisterSerializer,
)

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
    password = serializers.CharField(
        write_only=True,
        required=False,
        min_length=8,
    )

    customer_profile = CustomerProfileSerializer(required=False)

    addresses = CustomerAddressSerializer(
        many=True,
        required=False,
    )

    notes = CustomerNoteSerializer(
        many=True,
        read_only=True,
    )

    history_logs = CustomerHistorySerializer(
        many=True,
        read_only=True,
    )

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            "password",
            "customer_profile",
            "addresses",
            "notes",
            "history_logs",
        )

    def update(self, instance, validated_data):
        profile_data = validated_data.pop(
            "customer_profile",
            None,
        )

        addresses_data = validated_data.pop(
            "addresses",
            None,
        )

        # -----------------------------
        # Update User
        # -----------------------------
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        password = validated_data.pop("password", None)

        if password:
            instance.set_password(password)

        instance.save()

        # -----------------------------
        # Update Customer Profile
        # -----------------------------
        if profile_data:
            profile, _ = CustomerProfile.objects.get_or_create(
                user=instance
            )

            for attr, value in profile_data.items():
                setattr(profile, attr, value)

            profile.save()

        # -----------------------------
        # Update Address
        # -----------------------------
        if addresses_data:

            address_data = addresses_data[0]

            address = instance.addresses.filter(
                is_default=True
            ).first()

            if not address:
                address = instance.addresses.first()

            if address:

                for key, value in address_data.items():
                    setattr(address, key, value)

                address.save()

            else:

                CustomerAddress.objects.create(
                    customer=instance,
                    **address_data,
                )

        return instance
