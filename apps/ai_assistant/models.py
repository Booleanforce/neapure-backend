from django.db import models
from django.conf import settings
from shared.mixins.uuid import UUIDMixin
from shared.mixins.timestamp import TimeStampMixin
from apps.ai_assistant.constants import KBCategory, MessageRole, AnswerSource

class KnowledgeBase(UUIDMixin, TimeStampMixin):
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=30, choices=KBCategory.choices)
    question = models.TextField()
    answer = models.TextField()
    tags = models.JSONField(default=list)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        db_table = "ai_knowledge_base"
        ordering = ["category", "title"]

    def __str__(self):
        return f"[{self.category}] {self.title}"


class ChatSession(UUIDMixin, TimeStampMixin):
    session_key = models.CharField(max_length=255, unique=True, db_index=True)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        db_table = "ai_chat_sessions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Session {self.session_key}"


class ChatMessage(UUIDMixin, TimeStampMixin):
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    role = models.CharField(max_length=15, choices=MessageRole.choices)
    content = models.TextField()
    answered_by = models.CharField(
        max_length=30,
        choices=AnswerSource.choices,
        blank=True,
        null=True
    )

    class Meta:
        db_table = "ai_chat_messages"
        ordering = ["created_at"]

    def __str__(self):
        return f"Message from {self.role} in {self.session.session_key}"
