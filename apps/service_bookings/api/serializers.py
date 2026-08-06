from rest_framework import serializers
from apps.service_bookings.models import ServiceBooking, ServiceBookingNote, ServiceStatusHistory

class ServiceBookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceBooking
        exclude = ["is_deleted", "deleted_at", "assigned_to", "status", "booking_id", "created_at", "updated_at"]

class ServiceBookingListSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    technician_email = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceBooking
        fields = [
            "id", "booking_id", "customer_name", "phone", "service_type", 
            "status", "preferred_date", "preferred_time", "product_name", 
            "technician_email", "created_at"
        ]
        
    def get_product_name(self, obj):
        return obj.product.name if obj.product else obj.product_model_text
        
    def get_technician_email(self, obj):
        return obj.assigned_to.email if obj.assigned_to else None


class ServiceBookingNoteSerializer(serializers.ModelSerializer):
    author_email = serializers.CharField(source="author.email", read_only=True)
    
    class Meta:
        model = ServiceBookingNote
        fields = ["id", "author_email", "note", "created_at"]
        read_only_fields = ["id", "created_at"]


class ServiceStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_email = serializers.CharField(source="changed_by.email", read_only=True)
    
    class Meta:
        model = ServiceStatusHistory
        fields = ["id", "old_status", "new_status", "changed_by_email", "created_at"]
        read_only_fields = ["id", "created_at"]


class ServiceBookingDetailSerializer(serializers.ModelSerializer):
    notes = ServiceBookingNoteSerializer(many=True, read_only=True)
    status_history = ServiceStatusHistorySerializer(many=True, read_only=True)
    product_name = serializers.SerializerMethodField()
    technician_email = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceBooking
        exclude = ["is_deleted", "deleted_at"]
        
    def get_product_name(self, obj):
        return obj.product.name if obj.product else obj.product_model_text
        
    def get_technician_email(self, obj):
        return obj.assigned_to.email if obj.assigned_to else None
