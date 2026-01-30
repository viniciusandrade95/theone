from abc import ABC, abstractmethod
from modules.messaging.models import WhatsAppAccount, WebhookEvent, Conversation, Message


class MessagingRepo(ABC):
    @abstractmethod
    def get_whatsapp_account(self, *, provider: str, phone_number_id: str) -> WhatsAppAccount | None: ...

    @abstractmethod
    def create_whatsapp_account(self, account: WhatsAppAccount) -> None: ...

    @abstractmethod
    def record_webhook_event(self, event: WebhookEvent) -> bool: ...

    @abstractmethod
    def mark_webhook_event_status(
        self, *, tenant_id: str, provider: str, external_event_id: str, status: str
    ) -> None: ...

    @abstractmethod
    def get_conversation(self, *, tenant_id: str, customer_id: str, channel: str) -> Conversation | None: ...

    @abstractmethod
    def upsert_conversation(self, conversation: Conversation) -> Conversation: ...

    @abstractmethod
    def create_message(self, message: Message) -> Message: ...

    @abstractmethod
    def list_messages(self, *, tenant_id: str) -> list[Message]: ...

    @abstractmethod
    def count_messages(self, *, tenant_id: str) -> int: ...

    @abstractmethod
    def count_webhook_events(self, *, tenant_id: str) -> int: ...
