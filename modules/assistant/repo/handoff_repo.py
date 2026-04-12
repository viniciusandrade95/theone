import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.errors import ConflictError
from modules.assistant.models.handoff_orm import AssistantHandoffORM


class AssistantHandoffRepo:
    def __init__(self, session: Session):
        self.session = session

    def _coerce_uuid(self, value: str | uuid.UUID | None) -> uuid.UUID | None:
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        try:
            return uuid.UUID(str(value))
        except (TypeError, ValueError):
            return None

    def get_open_by_conversation(
        self, *, tenant_id: str, conversation_id: str, conversation_epoch: int
    ) -> AssistantHandoffORM | None:
        stmt = (
            select(AssistantHandoffORM)
            .where(AssistantHandoffORM.tenant_id == self._coerce_uuid(tenant_id))
            .where(AssistantHandoffORM.conversation_id == self._coerce_uuid(conversation_id))
            .where(AssistantHandoffORM.conversation_epoch == int(conversation_epoch))
            .where(AssistantHandoffORM.status == "open")
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def create_open(
        self,
        *,
        tenant_id: str,
        conversation_id: str,
        conversation_epoch: int,
        surface: str,
        session_id: str | None,
        user_id: str | None,
        customer_id: str | None,
        reason: str | None,
        summary: str | None,
    ) -> AssistantHandoffORM:
        entity = AssistantHandoffORM(
            id=uuid.uuid4(),
            tenant_id=self._coerce_uuid(tenant_id),
            conversation_id=self._coerce_uuid(conversation_id),
            conversation_epoch=int(conversation_epoch),
            surface=surface,
            session_id=session_id,
            user_id=self._coerce_uuid(user_id),
            customer_id=self._coerce_uuid(customer_id),
            status="open",
            reason=reason,
            summary=summary,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.session.add(entity)
        try:
            self.session.flush()
        except IntegrityError:
            raise ConflictError("assistant_handoff_exists")
        return entity

    def list_open(self, *, tenant_id: str, limit: int = 50) -> list[AssistantHandoffORM]:
        stmt = (
            select(AssistantHandoffORM)
            .where(AssistantHandoffORM.tenant_id == self._coerce_uuid(tenant_id))
            .where(AssistantHandoffORM.status == "open")
            .order_by(AssistantHandoffORM.created_at.desc())
            .limit(int(limit))
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_by_id(self, *, tenant_id: str, handoff_id: str) -> AssistantHandoffORM | None:
        stmt = (
            select(AssistantHandoffORM)
            .where(AssistantHandoffORM.tenant_id == self._coerce_uuid(tenant_id))
            .where(AssistantHandoffORM.id == self._coerce_uuid(handoff_id))
        )
        return self.session.execute(stmt).scalar_one_or_none()

