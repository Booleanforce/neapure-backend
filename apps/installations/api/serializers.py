from rest_framework import serializers
from apps.installations.models import InstallationRequest, ReplacementKitRequest, InstallationHistory, InstallationPhoto, InstallationChecklist, InstallationSignature

class InstallationHistorySerializer(serializers.ModelSerializer):
    performed_by_name = serializers.CharField(source='performed_by.full_name', read_only=True)
    performed_by_email = serializers.CharField(source='performed_by.email', read_only=True)

    class Meta:
        model = InstallationHistory
        fields = [
            'id', 
            'event_type', 
            'description', 
            'performed_by', 
            'performed_by_name', 
            'performed_by_email', 
            'created_at'
        ]
        read_only_fields = ['performed_by', 'created_at']


class InstallationPhotoSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.full_name', read_only=True)

    class Meta:
        model = InstallationPhoto
        fields = ['id', 'photo_type', 'photo', 'uploaded_by', 'uploaded_by_name', 'created_at']
        read_only_fields = ['uploaded_by', 'created_at']

class InstallationChecklistSerializer(serializers.ModelSerializer):
    submitted_by_name = serializers.CharField(source='submitted_by.full_name', read_only=True)

    class Meta:
        model = InstallationChecklist
        fields = ['id', 'data', 'submitted_by', 'submitted_by_name', 'created_at']
        read_only_fields = ['submitted_by', 'created_at']

class InstallationSignatureSerializer(serializers.ModelSerializer):
    collected_by_name = serializers.CharField(source='collected_by.full_name', read_only=True)

    class Meta:
        model = InstallationSignature
        fields = ['id', 'signature_image', 'collected_by', 'collected_by_name', 'created_at']
        read_only_fields = ['collected_by', 'created_at']

class InstallationRequestSerializer(serializers.ModelSerializer):
    history_logs = InstallationHistorySerializer(many=True, read_only=True)
    photos = InstallationPhotoSerializer(many=True, read_only=True)
    checklist = InstallationChecklistSerializer(read_only=True)
    signature = InstallationSignatureSerializer(read_only=True)
    dealer_name = serializers.CharField(source='dealer.full_name', read_only=True)
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    
    class Meta:
        model = InstallationRequest
        fields = [
            'id', 
            'registered_product', 
            'dealer', 
            'dealer_name',
            'customer', 
            'customer_name',
            'status', 
            'admin_notes', 
            'created_at', 
            'updated_at',
            'history_logs',
            'photos',
            'checklist',
            'signature'
        ]
        read_only_fields = ["id", "created_at", "updated_at", "status", "admin_notes", "dealer", "history_logs", "photos", "checklist", "signature"]

class ReplacementKitRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReplacementKitRequest
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "status", "admin_notes", "dealer"]
