import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from modules.chatbot.models.conversation_session_orm import ChatbotConversationSessionORM
from core.errors import ForbiddenError


class ChatbotSessionRepo:
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

    def get_by_conversation_id(self, conversation_id: str):
        stmt = select(ChatbotConversationSessionORM).where(
            ChatbotConversationSessionORM.conversation_id == self._coerce_uuid(conversation_id)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_conversation_id_scoped(self, *, conversation_id: str, tenant_id: str, user_id: str, surface: str):
        stmt = (
            select(ChatbotConversationSessionORM)
            .where(ChatbotConversationSessionORM.conversation_id == self._coerce_uuid(conversation_id))
            .where(ChatbotConversationSessionORM.tenant_id == self._coerce_uuid(tenant_id))
            .where(ChatbotConversationSessionORM.user_id == self._coerce_uuid(user_id))
            .where(ChatbotConversationSessionORM.surface == surface)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_scope(self, *, tenant_id: str, user_id: str, surface: str):
        stmt = (
            select(ChatbotConversationSessionORM)
            .where(ChatbotConversationSessionORM.tenant_id == self._coerce_uuid(tenant_id))
            .where(ChatbotConversationSessionORM.user_id == self._coerce_uuid(user_id))
            .where(ChatbotConversationSessionORM.surface == surface)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_or_create(
        self,
        *,
        tenant_id: str,
        user_id: str,
        client_id: str,
        surface: str,
        conversation_id: str | None = None,
        customer_id: str | None = None,
        start_new: bool = False,
    ):
        target = None
        if conversation_id:
            target = self.get_by_conversation_id_scoped(
                conversation_id=conversation_id, tenant_id=tenant_id, user_id=user_id, surface=surface
            )
            if target is None:
                # Explicitly reject cross-tenant or cross-user conversation reuse attempts.
                unscoped = self.get_by_conversation_id(conversation_id=conversation_id)
                if unscoped is not None:
                    raise ForbiddenError("conversation_scope_mismatch")

        if target is None:
            target = self.get_by_scope(tenant_id=tenant_id, user_id=user_id, surface=surface)

        if target is None:
            target = ChatbotConversationSessionORM(
                conversation_id=self._coerce_uuid(conversation_id) if conversation_id else uuid.uuid4(),
                tenant_id=self._coerce_uuid(tenant_id),
                user_id=self._coerce_uuid(user_id),
                customer_id=self._coerce_uuid(customer_id),
                client_id=client_id,
                surface=surface,
                status="active",
                last_message_at=datetime.now(timezone.utc),
            )
            self.session.add(target)
            self.session.flush()
            return target

        target.client_id = client_id
        if start_new and not conversation_id:
            self.reset(entity=target)
        if customer_id:
            target.customer_id = self._coerce_uuid(customer_id)
        return target

    def update_continuity(
        self,
        *,
        entity,
        last_intent: str | None = None,
        last_intent_confidence: float | None = None,
        state_payload: dict | None = None,
        context_payload: dict | None = None,
    ):
        if last_intent is not None:
            entity.last_intent = last_intent
        if last_intent_confidence is not None:
            entity.last_intent_confidence = last_intent_confidence
        if state_payload is not None:
            entity.state_payload = state_payload
        if context_payload is not None:
            entity.context_payload = context_payload
        self.session.add(entity)
        self.session.flush()
        return entity

    def mark_message(
        self,
        *,
        entity,
        chatbot_session_id: str | None,
        status: str = "active",
        error: str | None = None,
    ):
        entity.chatbot_session_id = chatbot_session_id or entity.chatbot_session_id
        entity.status = status
        entity.last_error = error
        entity.last_message_at = datetime.now(timezone.utc)
        self.session.add(entity)
        self.session.flush()
        return entity

    def reset(self, *, entity):
        entity.chatbot_session_id = None
        entity.status = "reset"
        entity.last_error = None
        entity.last_intent = None
        entity.last_intent_confidence = None
        entity.state_payload = None
        entity.context_payload = None
        entity.conversation_epoch = int(entity.conversation_epoch or 0) + 1
        entity.last_message_at = datetime.now(timezone.utc)
        self.session.add(entity)
        self.session.flush()
        return entity
