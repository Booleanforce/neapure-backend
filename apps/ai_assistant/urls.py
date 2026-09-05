from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.ai_assistant.api.views import ChatView, KnowledgeBaseViewSet

app_name = "ai_assistant"

router = DefaultRouter()
router.register(r'knowledge-base', KnowledgeBaseViewSet, basename='knowledgebase')

urlpatterns = [
    path('chat/', ChatView.as_view(), name='chat'),
    path('', include(router.urls)),
]
