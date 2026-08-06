from rest_framework import serializers
from apps.ai_assistant.models import KnowledgeBase
import uuid

class ChatRequestSerializer(serializers.Serializer):
    session_key = serializers.CharField(required=False, allow_blank=True)
    message = serializers.CharField(required=True)
    
    def validate_session_key(self, value):
        if not value:
            return str(uuid.uuid4())
        return value

class ChatResponseSerializer(serializers.Serializer):
    session_key = serializers.CharField()
    answer = serializers.CharField()
    source = serializers.CharField()

class KnowledgeBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeBase
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "created_by"]
