from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class OutboundSendResult:
    provider: str
    provider_message_id: str


class OutboundProvider(Protocol):
    def send_whatsapp_text(
        self,
        *,
        phone_number_id: str,
        to_phone: str,
        body: str,
        trace_id: str,
        idempotency_key: str | None = None,
    ) -> OutboundSendResult: ...

