import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select

from modules.chatbot.models.conversation_message_orm import ChatbotConversationMessageORM


class ChatbotMessageHistoryRepo:
    """Lightweight assistant turn persistence for support/debugging.

    Keeps history tenant-scoped by writing rows with the conversation's tenant_id.
    Applies a compact retention policy per (conversation_id, epoch).
    """

    MAX_MESSAGES_PER_EPOCH = 50

    def __init__(self, session):
        self.session = session

    @staticmethod
    def _coerce_uuid(value: str | None):
        if value is None:
            return None
        try:
            return uuid.UUID(str(value))
        except (TypeError, ValueError):
            return value

    def append(
        self,
        *,
        conversation,
        role: str,
        content: str,
        intent: str | None = None,
        meta: dict | None = None,
    ) -> ChatbotConversationMessageORM:
        msg = ChatbotConversationMessageORM(
            conversation_id=conversation.conversation_id,
            tenant_id=conversation.tenant_id,
            user_id=conversation.user_id,
            surface=conversation.surface,
            role=role,
            content=content,
            intent=intent,
            epoch=int(conversation.conversation_epoch or 0),
            meta=meta,
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(msg)
        self.session.flush()
        self._enforce_retention(conversation_id=str(conversation.conversation_id), epoch=int(conversation.conversation_epoch or 0))
        return msg

    def list_recent(self, *, conversation_id: str, epoch: int | None = None, limit: int = 20) -> list[ChatbotConversationMessageORM]:
        stmt = select(ChatbotConversationMessageORM).where(
            ChatbotConversationMessageORM.conversation_id == self._coerce_uuid(conversation_id)
        )
        if epoch is not None:
            stmt = stmt.where(ChatbotConversationMessageORM.epoch == epoch)
        stmt = stmt.order_by(ChatbotConversationMessageORM.created_at.desc()).limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def _enforce_retention(self, *, conversation_id: str, epoch: int) -> None:
        # Find messages beyond the most recent MAX_MESSAGES_PER_EPOCH and delete them.
        stmt = (
            select(ChatbotConversationMessageORM.id)
            .where(ChatbotConversationMessageORM.conversation_id == self._coerce_uuid(conversation_id))
            .where(ChatbotConversationMessageORM.epoch == epoch)
            .order_by(ChatbotConversationMessageORM.created_at.desc())
            .offset(self.MAX_MESSAGES_PER_EPOCH)
        )
        ids = [row[0] for row in self.session.execute(stmt).all()]
        if not ids:
            return
        self.session.execute(delete(ChatbotConversationMessageORM).where(ChatbotConversationMessageORM.id.in_(ids)))

