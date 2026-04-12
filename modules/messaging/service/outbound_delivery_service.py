from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from core.observability.logging import log_event
from modules.messaging.repo.outbound_delivery_events_repo import OutboundDeliveryEventsRepo
from modules.messaging.repo.outbound_sql import OutboundRepo


_STATUS_ORDER = {
    "queued": 0,
    "unconfirmed": 0,
    "accepted": 1,
    "sent": 2,
    "delivered": 3,
    "read": 4,
    "failed": 99,
}


class OutboundDeliveryService:
    def __init__(self, session: Session):
        self.session = session
        self.events = OutboundDeliveryEventsRepo(session)
        self.outbound = OutboundRepo(session)

    def ingest_event(
        self,
        *,
        tenant_id: uuid.UUID,
        provider: str,
        external_event_id: str,
        provider_message_id: str | None,
        channel: str,
        status: str,
        error_code: str | None,
        payload: dict | None,
        received_at: datetime | None = None,
    ) -> dict:
        now = received_at or datetime.now(timezone.utc)
        recorded = self.events.record(
            tenant_id=tenant_id,
            provider=provider,
            external_event_id=external_event_id,
            provider_message_id=provider_message_id,
            channel=channel,
            status=status,
            payload=payload,
            received_at=now,
        )

        updated_message_id = None
        updated_status = None

        if provider_message_id:
            msg = self.outbound.find_by_provider_message_id(
                tenant_id=tenant_id, provider=provider, provider_message_id=provider_message_id
            )
            if msg is not None:
                current = (msg.delivery_status or "").strip().lower() or "queued"
                desired = (status or "").strip().lower()
                if desired not in _STATUS_ORDER:
                    desired = current
                # Only advance monotonically, except allowing failed.
                if desired == "failed" or _STATUS_ORDER.get(desired, 0) >= _STATUS_ORDER.get(current, 0):
                    updated = self.outbound.update_delivery_status(
                        tenant_id=tenant_id,
                        message_id=msg.id,
                        delivery_status=desired,
                        error_code=error_code,
                        delivered_at=now if desired in {"delivered", "read"} else None,
                        failed_at=now if desired == "failed" else None,
                    )
                    updated_message_id = str(updated.id)
                    updated_status = updated.delivery_status

        log_event(
            "outbound_delivery_event_ingested",
            tenant_id=str(tenant_id),
            provider=provider,
            recorded=bool(recorded),
            updated_message_id=updated_message_id,
            status=status,
        )
        return {"recorded": recorded, "updated_message_id": updated_message_id, "delivery_status": updated_status}

