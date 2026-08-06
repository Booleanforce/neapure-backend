from django.contrib import admin
from apps.ai_assistant.models import KnowledgeBase, ChatSession, ChatMessage

@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "created_at")
    list_filter = ("category",)
    search_fields = ("title", "question", "answer", "tags")
    readonly_fields = ("created_by",)
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ("role", "content", "answered_by", "created_at")
    can_delete = False

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("session_key", "customer", "created_at")
    search_fields = ("session_key", "customer__email")
    inlines = [ChatMessageInline]
    readonly_fields = ("session_key",)
