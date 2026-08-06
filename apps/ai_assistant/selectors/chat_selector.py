from apps.ai_assistant.models import ChatSession, ChatMessage

class ChatSelector:

    @staticmethod
    def get_or_create_session(session_key, user=None):
        if not session_key:
            import uuid
            session_key = str(uuid.uuid4())

        session, _ = ChatSession.objects.get_or_create(
            session_key=session_key,
            defaults={"customer": user}
        )
        # Update user if it was created anonymously but now has a user
        if user and session.customer != user:
            session.customer = user
            session.save(update_fields=["customer"])
        return session

    @staticmethod
    def get_session_history(session, limit=6):
        # Return the last `limit` messages in chronological order
        # We fetch descending to get the most recent, then reverse to chronological
        messages = list(ChatMessage.objects.filter(session=session).order_by("-created_at")[:limit])
        messages.reverse()
        return messages
