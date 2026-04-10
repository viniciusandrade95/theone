import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from modules.assistant.models.prebook_request_orm import AssistantPrebookRequestORM


class AssistantPrebookRequestRepo:
    def __init__(self, session):
        self.session = session

    def get_by_idempotency_key(self, *, tenant_id: uuid.UUID, idempotency_key: str) -> AssistantPrebookRequestORM | None:
        stmt = (
            select(AssistantPrebookRequestORM)
            .where(AssistantPrebookRequestORM.tenant_id == tenant_id)
            .where(AssistantPrebookRequestORM.idempotency_key == idempotency_key)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def create_started(
        self,
        *,
        tenant_id: uuid.UUID,
        idempotency_key: str,
        conversation_id: uuid.UUID | None,
        session_id: str | None,
        trace_id: str | None,
        actor_type: str | None,
        actor_id: uuid.UUID | None,
    ) -> tuple[AssistantPrebookRequestORM | None, AssistantPrebookRequestORM | None]:
        """Create a placeholder row to enforce idempotency.

        Returns (created, existing) where exactly one is non-None.
        """
        row = AssistantPrebookRequestORM(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            idempotency_key=idempotency_key,
            conversation_id=conversation_id,
            session_id=session_id,
            trace_id=trace_id,
            actor_type=actor_type,
            actor_id=actor_id,
            status="started",
        )
        self.session.add(row)
        try:
            self.session.flush()
            return row, None
        except IntegrityError:
            self.session.rollback()
            existing = self.get_by_idempotency_key(tenant_id=tenant_id, idempotency_key=idempotency_key)
            return None, existing

    def mark_created(
        self,
        *,
        row: AssistantPrebookRequestORM,
        appointment_id: uuid.UUID,
        customer_id: uuid.UUID,
        service_id: uuid.UUID,
        location_id: uuid.UUID,
        starts_at,
        ends_at,
    ) -> AssistantPrebookRequestORM:
        row.appointment_id = appointment_id
        row.customer_id = customer_id
        row.service_id = service_id
        row.location_id = location_id
        row.starts_at = starts_at
        row.ends_at = ends_at
        row.status = "created"
        row.last_error = None
        self.session.add(row)
        self.session.flush()
        return row

    def delete(self, *, row: AssistantPrebookRequestORM) -> None:
        self.session.delete(row)
        self.session.flush()

