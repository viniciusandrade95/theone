from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from core.observability.logging import log_event
from modules.assistant.repo.handoff_repo import AssistantHandoffRepo
from modules.assistant.service.assistant_communication_service import AssistantCommunicationService
from modules.assistant.service.funnel_events import (
    ASSISTANT_FALLBACK,
    ASSISTANT_HANDOFF_CREATED,
    ASSISTANT_HANDOFF_REQUESTED,
    AssistantFunnelEventsService,
)
from modules.crm.models.interaction_orm import InteractionORM


class AssistantHandoffService:
    """Thin MVP: durable handoff record + CRM interaction for visibility."""

    def __init__(self, session: Session):
        self.session = session
        self.repo = AssistantHandoffRepo(session)

    def ensure_open_handoff(
        self,
        *,
        tenant_id: str,
        conversation_id: str,
        conversation_epoch: int,
        surface: str,
        session_id: str | None,
        user_id: str | None,
        customer_id: str | None,
        trace_id: str,
        reason: str | None = None,
        summary: str | None = None,
    ):
        tenant_uuid = uuid.UUID(tenant_id)
        conversation_uuid = uuid.UUID(conversation_id)

        funnel = AssistantFunnelEventsService(self.session)
        funnel.emit_once(
            tenant_id=tenant_uuid,
            dedupe_key=f"assistant_handoff_requested:{conversation_id}:{conversation_epoch}",
            event_name=ASSISTANT_HANDOFF_REQUESTED,
            trace_id=trace_id,
            conversation_id=conversation_uuid,
            assistant_session_id=session_id,
            customer_id=uuid.UUID(customer_id) if customer_id else None,
            event_source="assistant_handoff",
            metadata={
                "surface": surface,
                "reason": reason,
                "conversation_epoch": int(conversation_epoch),
            },
        )
        if isinstance(reason, str) and reason and reason != "user_requested_human":
            funnel.emit_once(
                tenant_id=tenant_uuid,
                dedupe_key=f"assistant_fallback:{conversation_id}:{conversation_epoch}",
                event_name=ASSISTANT_FALLBACK,
                trace_id=trace_id,
                conversation_id=conversation_uuid,
                assistant_session_id=session_id,
                customer_id=uuid.UUID(customer_id) if customer_id else None,
                event_source="assistant_handoff",
                metadata={"reason": reason, "surface": surface, "conversation_epoch": int(conversation_epoch)},
            )

        existing = self.repo.get_open_by_conversation(
            tenant_id=tenant_id, conversation_id=conversation_id, conversation_epoch=conversation_epoch
        )
        if existing is not None:
            log_event(
                "assistant_handoff_idempotent_hit",
                tenant_id=tenant_id,
                trace_id=trace_id,
                conversation_id=conversation_id,
                handoff_id=str(existing.id),
            )
            return existing, False

        created = self.repo.create_open(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            conversation_epoch=conversation_epoch,
            surface=surface,
            session_id=session_id,
            user_id=user_id,
            customer_id=customer_id,
            reason=reason,
            summary=summary,
        )
        log_event(
            "assistant_handoff_created",
            tenant_id=tenant_id,
            trace_id=trace_id,
            conversation_id=conversation_id,
            handoff_id=str(created.id),
        )

        funnel.emit_once(
            tenant_id=tenant_uuid,
            dedupe_key=f"assistant_handoff_created:{created.id}",
            event_name=ASSISTANT_HANDOFF_CREATED,
            trace_id=trace_id,
            conversation_id=conversation_uuid,
            assistant_session_id=session_id,
            customer_id=uuid.UUID(customer_id) if customer_id else None,
            event_source="assistant_handoff",
            related_entity_type="assistant_handoff",
            related_entity_id=created.id,
            metadata={"surface": surface, "reason": reason, "conversation_epoch": int(conversation_epoch)},
        )

        # Operational visibility via CRM interaction when customer context exists.
        if customer_id:
            try:
                interaction = InteractionORM(
                    id=uuid.uuid4(),
                    tenant_id=uuid.UUID(tenant_id),
                    customer_id=uuid.UUID(customer_id),
                    type="assistant_handoff",
                    payload={
                        "content": summary or "Pedido de atendente humano via assistant.",
                        "handoff_id": str(created.id),
                        "trace_id": trace_id,
                        "conversation_id": conversation_id,
                    },
                    created_at=datetime.now(timezone.utc),
                )
                self.session.add(interaction)
                self.session.flush()
            except Exception:
                # Interaction is best-effort in MVP; do not fail the user flow.
                log_event(
                    "assistant_handoff_interaction_failed",
                    level="warning",
                    tenant_id=tenant_id,
                    trace_id=trace_id,
                    conversation_id=conversation_id,
                    handoff_id=str(created.id),
                )

        # Best-effort automatic confirmation for the customer.
        try:
            customer_uuid = uuid.UUID(customer_id) if customer_id else None
        except Exception:
            customer_uuid = None
        try:
            conversation_uuid = uuid.UUID(conversation_id)
        except Exception:
            conversation_uuid = None
        try:
            AssistantCommunicationService(self.session).confirm_handoff_created(
                tenant_id=uuid.UUID(tenant_id),
                handoff_id=created.id,
                customer_id=customer_uuid,
                trace_id=trace_id,
                conversation_id=conversation_uuid,
                assistant_session_id=session_id,
            )
        except Exception as err:
            log_event(
                "assistant_handoff_confirmation_failed",
                level="warning",
                tenant_id=tenant_id,
                trace_id=trace_id,
                conversation_id=conversation_id,
                handoff_id=str(created.id),
                error=str(err),
            )

        return created, True
