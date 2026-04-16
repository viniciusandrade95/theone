from __future__ import annotations

from dataclasses import dataclass

import requests

from core.config import get_config
from core.errors import ValidationError
from modules.messaging.providers.outbound_provider import OutboundSendResult


@dataclass(frozen=True)
class MetaWhatsAppCloudProvider:
    """Thin WhatsApp Cloud API sender (Meta).

    This is intentionally minimal and only supports text messages for now.
    If provided, `idempotency_key` is forwarded as `Idempotency-Key` to help avoid duplicate sends.
    """

    api_version: str = "v19.0"

    def send_whatsapp_text(
        self,
        *,
        phone_number_id: str,
        to_phone: str,
        body: str,
        trace_id: str,
        idempotency_key: str | None = None,
    ) -> OutboundSendResult:
        cfg = get_config()
        token = (getattr(cfg, "WHATSAPP_CLOUD_ACCESS_TOKEN", None) or "").strip()
        if not token:
            raise ValidationError("whatsapp_cloud_not_configured")

        api_version = (getattr(cfg, "WHATSAPP_CLOUD_API_VERSION", None) or self.api_version).strip()
        url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "text",
            "text": {"body": body},
        }
        headers = {"Authorization": f"Bearer {token}", "X-Trace-Id": trace_id}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        timeout_s = max(1, int(getattr(cfg, "WHATSAPP_CLOUD_TIMEOUT_SECONDS", 10) or 10))
        resp = requests.post(url, json=payload, headers=headers, timeout=timeout_s)
        resp.raise_for_status()
        data = resp.json() if resp.content else {}
        msg_id = None
        if isinstance(data, dict):
            messages = data.get("messages")
            if isinstance(messages, list) and messages and isinstance(messages[0], dict):
                msg_id = messages[0].get("id")
        if not isinstance(msg_id, str) or not msg_id.strip():
            raise ValidationError("whatsapp_cloud_invalid_response")
        return OutboundSendResult(provider="meta", provider_message_id=msg_id.strip())
