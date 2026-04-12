from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from modules.assistant.repo.funnel_event_repo import AssistantFunnelEventRepo


# Explicit, finite taxonomy (v1). Keep names stable.
ASSISTANT_MESSAGE_RECEIVED = "assistant_message_received"
ASSISTANT_MESSAGE_REPLIED = "assistant_message_replied"
ASSISTANT_FALLBACK = "assistant_fallback"
ASSISTANT_HANDOFF_REQUESTED = "assistant_handoff_requested"
ASSISTANT_HANDOFF_CREATED = "assistant_handoff_created"
ASSISTANT_PREBOOK_REQUESTED = "assistant_prebook_requested"
ASSISTANT_PREBOOK_CREATED = "assistant_prebook_created"
ASSISTANT_QUOTE_REQUESTED = "assistant_quote_requested"
ASSISTANT_QUOTE_CREATED = "assistant_quote_created"
ASSISTANT_CONSULT_REQUESTED = "assistant_consult_requested"
ASSISTANT_CONSULT_CREATED = "assistant_consult_created"
ASSISTANT_CONVERSION_CONFIRMED = "assistant_conversion_confirmed"


class AssistantFunnelEventsService:
    """Tenant-safe funnel event persistence helper."""

    def __init__(self, session: Session):
        self.repo = AssistantFunnelEventRepo(session)

    def emit(
        self,
        *,
        tenant_id: uuid.UUID,
        event_name: str,
        trace_id: str | None,
        conversation_id: uuid.UUID | None = None,
        assistant_session_id: str | None = None,
        customer_id: uuid.UUID | None = None,
        event_source: str = "theone",
        channel: str | None = None,
        related_entity_type: str | None = None,
        related_entity_id: uuid.UUID | None = None,
        metadata: dict | None = None,
    ) -> None:
        self.repo.create(
            tenant_id=tenant_id,
            event_name=event_name,
            trace_id=trace_id,
            conversation_id=conversation_id,
            assistant_session_id=assistant_session_id,
            customer_id=customer_id,
            event_source=event_source,
            channel=channel,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            metadata=metadata,
        )

    def emit_once(
        self,
        *,
        tenant_id: uuid.UUID,
        dedupe_key: str,
        event_name: str,
        trace_id: str | None,
        conversation_id: uuid.UUID | None = None,
        assistant_session_id: str | None = None,
        customer_id: uuid.UUID | None = None,
        event_source: str = "theone",
        channel: str | None = None,
        related_entity_type: str | None = None,
        related_entity_id: uuid.UUID | None = None,
        metadata: dict | None = None,
    ) -> bool:
        _, created = self.repo.create_once(
            tenant_id=tenant_id,
            dedupe_key=dedupe_key,
            event_name=event_name,
            trace_id=trace_id,
            conversation_id=conversation_id,
            assistant_session_id=assistant_session_id,
            customer_id=customer_id,
            event_source=event_source,
            channel=channel,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            metadata=metadata,
        )
        return created

