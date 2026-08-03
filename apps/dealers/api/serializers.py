from rest_framework import serializers
from apps.dealers.models import DealerProfile
from apps.accounts.api.serializers import UserSerializer

class DealerProfileSerializer(serializers.ModelSerializer):
    total_customers_registered = serializers.SerializerMethodField()

    class Meta:
        model = DealerProfile
        fields = ("company_name", "contact_person", "trade_license", "status", "total_customers_registered")

    def get_total_customers_registered(self, obj):
        if obj.user:
            return obj.user.registered_customers.count()
        return 0

class DealerSerializer(UserSerializer):
    dealer_profile = DealerProfileSerializer(read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ("dealer_profile",)
