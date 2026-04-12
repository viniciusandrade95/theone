import uuid
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from modules.messaging.models.outbound_delivery_event_orm import OutboundDeliveryEventORM


class OutboundDeliveryEventsRepo:
    def __init__(self, session: Session):
        self.session = session

    def _coerce_uuid(self, value: str | uuid.UUID) -> uuid.UUID:
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))

    def record(
        self,
        *,
        tenant_id: uuid.UUID,
        provider: str,
        external_event_id: str,
        provider_message_id: str | None,
        channel: str,
        status: str,
        payload: dict | None,
        received_at: datetime | None = None,
    ) -> bool:
        try:
            row = OutboundDeliveryEventORM(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                provider=provider,
                external_event_id=external_event_id,
                provider_message_id=provider_message_id,
                channel=channel,
                status=status,
                payload=payload,
                received_at=received_at or datetime.now(timezone.utc),
            )
            self.session.add(row)
            self.session.flush()
            return True
        except IntegrityError:
            # Keep the session usable for subsequent reads/updates in the same request.
            self.session.rollback()
            return False
