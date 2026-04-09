import uuid
from datetime import datetime, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from core.errors import NotFoundError, ValidationError
from modules.messaging.models.message_template_orm import MessageTemplateORM
from modules.messaging.models.outbound_message_orm import OutboundMessageORM


_ALLOWED_OUTBOUND_STATUSES = {"pending", "sent", "failed"}


def _now():
    return datetime.now(timezone.utc)


class OutboundRepo:
    def __init__(self, session: Session):
        self.session = session

    def _coerce_uuid(self, value: str | uuid.UUID) -> uuid.UUID:
        if isinstance(value, uuid.UUID):
            return value
        try:
            return uuid.UUID(str(value))
        except (TypeError, ValueError):
            raise ValidationError("invalid_uuid", meta={"value": value})

    # -----------------------
    # Templates
    # -----------------------

    def list_templates(
        self,
        *,
        tenant_id: uuid.UUID,
        type: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[MessageTemplateORM], int]:
        if page < 1:
            raise ValidationError("invalid_page")
        if page_size < 1 or page_size > 200:
            raise ValidationError("invalid_page_size")

        stmt = select(MessageTemplateORM).where(MessageTemplateORM.tenant_id == tenant_id)
        count_stmt = (
            select(func.count())
            .select_from(MessageTemplateORM)
            .where(MessageTemplateORM.tenant_id == tenant_id)
        )
        if type:
            stmt = stmt.where(MessageTemplateORM.type == type)
            count_stmt = count_stmt.where(MessageTemplateORM.type == type)
        if is_active is not None:
            stmt = stmt.where(MessageTemplateORM.is_active.is_(bool(is_active)))
            count_stmt = count_stmt.where(MessageTemplateORM.is_active.is_(bool(is_active)))
        stmt = stmt.order_by(MessageTemplateORM.updated_at.desc(), MessageTemplateORM.id.asc())

        total = int(self.session.execute(count_stmt).scalar_one())
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        items = list(self.session.execute(stmt).scalars().all())
        return items, total

    def get_template(self, *, tenant_id: uuid.UUID, template_id: str) -> MessageTemplateORM:
        tid = self._coerce_uuid(template_id)
        stmt = (
            select(MessageTemplateORM)
            .where(MessageTemplateORM.tenant_id == tenant_id)
            .where(MessageTemplateORM.id == tid)
        )
        row = self.session.execute(stmt).scalar_one_or_none()
        if row is None:
            raise NotFoundError("template_not_found", meta={"template_id": template_id})
        return row

    def create_template(
        self,
        *,
        tenant_id: uuid.UUID,
        name: str,
        type: str,
        channel: str,
        body: str,
        is_active: bool = True,
    ) -> MessageTemplateORM:
        template = MessageTemplateORM(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            name=name,
            type=type,
            channel=channel,
            body=body,
            is_active=bool(is_active),
        )
        self.session.add(template)
        self.session.flush()
        return template

    def update_template(
        self,
        *,
        tenant_id: uuid.UUID,
        template_id: str,
        patch: dict,
    ) -> MessageTemplateORM:
        template = self.get_template(tenant_id=tenant_id, template_id=template_id)
        for key, value in patch.items():
            setattr(template, key, value)
        template.updated_at = _now()
        self.session.flush()
        return template

    def delete_template(self, *, tenant_id: uuid.UUID, template_id: str) -> None:
        template = self.get_template(tenant_id=tenant_id, template_id=template_id)
        self.session.delete(template)
        self.session.flush()

    # -----------------------
    # Outbound messages
    # -----------------------

    def list_messages(
        self,
        *,
        tenant_id: uuid.UUID,
        customer_id: str | None = None,
        template_id: str | None = None,
        type: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[list[OutboundMessageORM], int]:
        if page < 1:
            raise ValidationError("invalid_page")
        if page_size < 1 or page_size > 200:
            raise ValidationError("invalid_page_size")

        stmt = select(OutboundMessageORM).where(OutboundMessageORM.tenant_id == tenant_id)
        count_stmt = (
            select(func.count())
            .select_from(OutboundMessageORM)
            .where(OutboundMessageORM.tenant_id == tenant_id)
        )

        if customer_id:
            cid = self._coerce_uuid(customer_id)
            stmt = stmt.where(OutboundMessageORM.customer_id == cid)
            count_stmt = count_stmt.where(OutboundMessageORM.customer_id == cid)
        if template_id:
            tid = self._coerce_uuid(template_id)
            stmt = stmt.where(OutboundMessageORM.template_id == tid)
            count_stmt = count_stmt.where(OutboundMessageORM.template_id == tid)
        if type:
            stmt = stmt.where(OutboundMessageORM.type == type)
            count_stmt = count_stmt.where(OutboundMessageORM.type == type)
        if status:
            lowered = status.strip().lower()
            if lowered not in _ALLOWED_OUTBOUND_STATUSES:
                raise ValidationError("invalid_outbound_status", meta={"allowed": sorted(_ALLOWED_OUTBOUND_STATUSES)})
            stmt = stmt.where(OutboundMessageORM.status == lowered)
            count_stmt = count_stmt.where(OutboundMessageORM.status == lowered)

        stmt = stmt.order_by(OutboundMessageORM.created_at.desc(), OutboundMessageORM.id.asc())
        total = int(self.session.execute(count_stmt).scalar_one())
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        items = list(self.session.execute(stmt).scalars().all())
        return items, total

    def get_message(self, *, tenant_id: uuid.UUID, message_id: str) -> OutboundMessageORM:
        mid = self._coerce_uuid(message_id)
        stmt = (
            select(OutboundMessageORM)
            .where(OutboundMessageORM.tenant_id == tenant_id)
            .where(OutboundMessageORM.id == mid)
        )
        row = self.session.execute(stmt).scalar_one_or_none()
        if row is None:
            raise NotFoundError("outbound_message_not_found", meta={"id": message_id})
        return row

    def create_message(
        self,
        *,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
        appointment_id: uuid.UUID | None,
        template_id: uuid.UUID | None,
        type: str,
        channel: str,
        rendered_body: str,
        status: str,
        error_message: str | None,
        sent_by_user_id: uuid.UUID | None,
        sent_at: datetime | None,
    ) -> OutboundMessageORM:
        normalized_status = (status or "").strip().lower()
        if normalized_status not in _ALLOWED_OUTBOUND_STATUSES:
            raise ValidationError("invalid_outbound_status", meta={"allowed": sorted(_ALLOWED_OUTBOUND_STATUSES)})
        msg = OutboundMessageORM(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            customer_id=customer_id,
            appointment_id=appointment_id,
            template_id=template_id,
            type=type,
            channel=channel,
            rendered_body=rendered_body,
            status=normalized_status,
            error_message=error_message,
            sent_by_user_id=sent_by_user_id,
            sent_at=sent_at,
            created_at=_now(),
            updated_at=_now(),
        )
        self.session.add(msg)
        self.session.flush()
        return msg

    def mark_failed(self, *, tenant_id: uuid.UUID, message_id: str, error_message: str) -> OutboundMessageORM:
        msg = self.get_message(tenant_id=tenant_id, message_id=message_id)
        msg.status = "failed"
        msg.error_message = error_message.strip()[:2000] if error_message else "unknown_error"
        msg.updated_at = _now()
        self.session.flush()
        return msg

    def mark_sent(self, *, tenant_id: uuid.UUID, message_id: str, sent_at: datetime | None = None) -> OutboundMessageORM:
        msg = self.get_message(tenant_id=tenant_id, message_id=message_id)
        msg.status = "sent"
        msg.error_message = None
        msg.sent_at = sent_at or _now()
        msg.updated_at = _now()
        self.session.flush()
        return msg

