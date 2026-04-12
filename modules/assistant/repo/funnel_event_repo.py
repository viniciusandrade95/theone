from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from modules.assistant.models.funnel_event_orm import AssistantFunnelEventORM


class AssistantFunnelEventRepo:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        tenant_id: uuid.UUID,
        event_name: str,
        trace_id: str | None = None,
        conversation_id: uuid.UUID | None = None,
        assistant_session_id: str | None = None,
        customer_id: uuid.UUID | None = None,
        event_source: str = "theone",
        channel: str | None = None,
        related_entity_type: str | None = None,
        related_entity_id: uuid.UUID | None = None,
        metadata: dict | None = None,
        dedupe_key: str | None = None,
        created_at: datetime | None = None,
    ) -> AssistantFunnelEventORM:
        row = AssistantFunnelEventORM(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            trace_id=(trace_id.strip() if isinstance(trace_id, str) and trace_id.strip() else None),
            conversation_id=conversation_id,
            assistant_session_id=(assistant_session_id.strip() if isinstance(assistant_session_id, str) and assistant_session_id.strip() else None),
            customer_id=customer_id,
            event_name=event_name.strip(),
            event_source=(event_source or "theone").strip().lower(),
            channel=(channel.strip().lower() if isinstance(channel, str) and channel.strip() else None),
            related_entity_type=(related_entity_type.strip().lower() if isinstance(related_entity_type, str) and related_entity_type.strip() else None),
            related_entity_id=related_entity_id,
            meta=(metadata or {}),
            dedupe_key=(dedupe_key.strip() if isinstance(dedupe_key, str) and dedupe_key.strip() else None),
            created_at=created_at or datetime.now(timezone.utc),
        )
        self.session.add(row)
        self.session.flush()
        return row

    def create_once(
        self,
        *,
        tenant_id: uuid.UUID,
        dedupe_key: str,
        **kwargs,
    ) -> tuple[AssistantFunnelEventORM, bool]:
        try:
            # Important: isolate the uniqueness conflict without rolling back the whole request transaction.
            with self.session.begin_nested():
                row = self.create(tenant_id=tenant_id, dedupe_key=dedupe_key, **kwargs)
            return row, True
        except IntegrityError:
            stmt = (
                select(AssistantFunnelEventORM)
                .where(AssistantFunnelEventORM.tenant_id == tenant_id)
                .where(AssistantFunnelEventORM.dedupe_key == dedupe_key)
            )
            existing = self.session.execute(stmt).scalar_one()
            return existing, False
