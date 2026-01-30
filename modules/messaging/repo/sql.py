from uuid import UUID

from sqlalchemy import select, update, func
from sqlalchemy.exc import IntegrityError

from core.db.session import db_session
from core.errors import ConflictError
from modules.messaging.repo.messaging_repo import MessagingRepo
from modules.messaging.models import WhatsAppAccount, WebhookEvent, Conversation, Message
from modules.messaging.models.whatsapp_account_orm import WhatsAppAccountORM
from modules.messaging.models.webhook_event_orm import WebhookEventORM
from modules.messaging.models.conversation_orm import ConversationORM
from modules.messaging.models.message_orm import MessageORM


class SqlMessagingRepo(MessagingRepo):
    def _coerce_uuid(self, value: str):
        try:
            return UUID(value)
        except (TypeError, ValueError):
            return value

    def get_whatsapp_account(self, *, provider: str, phone_number_id: str) -> WhatsAppAccount | None:
        with db_session() as session:
            stmt = (
                select(WhatsAppAccountORM)
                .where(WhatsAppAccountORM.provider == provider)
                .where(WhatsAppAccountORM.phone_number_id == phone_number_id)
            )
            row = session.execute(stmt).scalar_one_or_none()
            return row.to_domain() if row else None

    def create_whatsapp_account(self, account: WhatsAppAccount) -> None:
        try:
            with db_session() as session:
                session.add(
                    WhatsAppAccountORM(
                        id=self._coerce_uuid(account.id),
                        tenant_id=self._coerce_uuid(account.tenant_id),
                        provider=account.provider,
                        phone_number_id=account.phone_number_id,
                        status=account.status,
                    )
                )
        except IntegrityError:
            raise ConflictError(
                "whatsapp_account_exists",
                meta={"provider": account.provider, "phone_number_id": account.phone_number_id},
            )

    def record_webhook_event(self, event: WebhookEvent) -> bool:
        try:
            with db_session() as session:
                session.add(
                    WebhookEventORM(
                        id=self._coerce_uuid(event.id),
                        tenant_id=self._coerce_uuid(event.tenant_id),
                        provider=event.provider,
                        external_event_id=event.external_event_id,
                        payload=event.payload,
                        signature_valid=event.signature_valid,
                        status=event.status,
                    )
                )
            return True
        except IntegrityError:
            return False

    def mark_webhook_event_status(
        self, *, tenant_id: str, provider: str, external_event_id: str, status: str
    ) -> None:
        values = {"status": status}
        if status in {"processed", "dead_letter"}:
            values["processed_at"] = func.now()
        with db_session() as session:
            stmt = (
                update(WebhookEventORM)
                .where(WebhookEventORM.tenant_id == self._coerce_uuid(tenant_id))
                .where(WebhookEventORM.provider == provider)
                .where(WebhookEventORM.external_event_id == external_event_id)
                .values(**values)
            )
            session.execute(stmt)

    def get_conversation(self, *, tenant_id: str, customer_id: str, channel: str) -> Conversation | None:
        with db_session() as session:
            stmt = (
                select(ConversationORM)
                .where(ConversationORM.tenant_id == self._coerce_uuid(tenant_id))
                .where(ConversationORM.customer_id == self._coerce_uuid(customer_id))
                .where(ConversationORM.channel == channel)
            )
            row = session.execute(stmt).scalar_one_or_none()
            return row.to_domain() if row else None

    def upsert_conversation(self, conversation: Conversation) -> Conversation:
        with db_session() as session:
            stmt = (
                select(ConversationORM)
                .where(ConversationORM.tenant_id == self._coerce_uuid(conversation.tenant_id))
                .where(ConversationORM.customer_id == self._coerce_uuid(conversation.customer_id))
                .where(ConversationORM.channel == conversation.channel)
            )
            existing = session.execute(stmt).scalar_one_or_none()
            if existing:
                existing.last_message_at = conversation.last_message_at
                return existing.to_domain()

            orm = ConversationORM(
                id=self._coerce_uuid(conversation.id),
                tenant_id=self._coerce_uuid(conversation.tenant_id),
                customer_id=self._coerce_uuid(conversation.customer_id),
                channel=conversation.channel,
                state=conversation.state,
                last_message_at=conversation.last_message_at,
            )
            session.add(orm)
            session.flush()
            return orm.to_domain()

    def create_message(self, message: Message) -> Message:
        try:
            with db_session() as session:
                orm = MessageORM(
                    id=self._coerce_uuid(message.id),
                    tenant_id=self._coerce_uuid(message.tenant_id),
                    conversation_id=self._coerce_uuid(message.conversation_id),
                    direction=message.direction,
                    provider=message.provider,
                    provider_message_id=message.provider_message_id,
                    from_phone=message.from_phone,
                    to_phone=message.to_phone,
                    body=message.body,
                    status=message.status,
                    received_at=message.received_at,
                    sent_at=message.sent_at,
                )
                session.add(orm)
                session.flush()
                return orm.to_domain()
        except IntegrityError:
            with db_session() as session:
                stmt = (
                    select(MessageORM)
                    .where(MessageORM.tenant_id == self._coerce_uuid(message.tenant_id))
                    .where(MessageORM.provider_message_id == message.provider_message_id)
                )
                existing = session.execute(stmt).scalar_one()
                return existing.to_domain()

    def list_messages(self, *, tenant_id: str) -> list[Message]:
        with db_session() as session:
            stmt = select(MessageORM).where(MessageORM.tenant_id == self._coerce_uuid(tenant_id))
            return [m.to_domain() for m in session.execute(stmt).scalars().all()]

    def count_messages(self, *, tenant_id: str) -> int:
        with db_session() as session:
            stmt = select(MessageORM).where(MessageORM.tenant_id == self._coerce_uuid(tenant_id))
            return len(session.execute(stmt).scalars().all())

    def count_webhook_events(self, *, tenant_id: str) -> int:
        with db_session() as session:
            stmt = select(WebhookEventORM).where(WebhookEventORM.tenant_id == self._coerce_uuid(tenant_id))
            return len(session.execute(stmt).scalars().all())
