from rest_framework import views, viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from drf_spectacular.utils import extend_schema

from apps.ai_assistant.models import KnowledgeBase
from apps.ai_assistant.api.serializers import ChatRequestSerializer, ChatResponseSerializer, KnowledgeBaseSerializer
from apps.ai_assistant.services.chat_service import ChatService

class ChatView(views.APIView):
    permission_classes = [AllowAny]
    
    @extend_schema(
        request=ChatRequestSerializer,
        responses={200: ChatResponseSerializer},
        tags=["AI Assistant"]
    )
    def post(self, request, *args, **kwargs):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        session_key = serializer.validated_data.get("session_key")
        message = serializer.validated_data["message"]
        user = request.user if request.user.is_authenticated else None
        
        answer, session_key, source = ChatService.handle_chat_message(session_key, message, user)
        
        resp_serializer = ChatResponseSerializer(data={
            "session_key": session_key,
            "answer": answer,
            "source": source
        })
        resp_serializer.is_valid(raise_exception=True)
        
        return Response(resp_serializer.data, status=status.HTTP_200_OK)


class KnowledgeBaseViewSet(viewsets.ModelViewSet):
    queryset = KnowledgeBase.objects.all()
    serializer_class = KnowledgeBaseSerializer
    permission_classes = [IsAdminUser]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
