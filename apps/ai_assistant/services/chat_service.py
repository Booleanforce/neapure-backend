from apps.ai_assistant.models import ChatMessage
from apps.ai_assistant.constants import MessageRole
from apps.ai_assistant.selectors.chat_selector import ChatSelector
from apps.ai_assistant.services.intent_router import IntentRouter

class ChatService:

    @staticmethod
    def handle_chat_message(session_key, user_message, user=None):
        session = ChatSelector.get_or_create_session(session_key, user)
        
        # Save user message
        ChatMessage.objects.create(
            session=session,
            role=MessageRole.USER,
            content=user_message
        )
        
        history = ChatSelector.get_session_history(session, limit=7)
        # exclude the newly created user message from history for the LLM
        history_for_router = [msg for msg in history if msg.role != MessageRole.USER or msg.content != user_message]
        # if the user sent identical messages, it might exclude both, but that's a minor edge case.
        # A better way is:
        history_for_router = history[:-1] if history and history[-1].role == MessageRole.USER else history
        
        answer, source = IntentRouter.classify_and_answer(user_message, history_for_router)
        
        # Save assistant message
        ChatMessage.objects.create(
            session=session,
            role=MessageRole.ASSISTANT,
            content=answer,
            answered_by=source
        )
        
        return answer, session.session_key, source
