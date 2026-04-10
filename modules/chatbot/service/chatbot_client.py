import uuid

import requests

from core.config import get_config
from core.errors import ValidationError


class ChatbotClient:
    def __init__(self):
        cfg = get_config()
        self.base_url = (cfg.CHATBOT_SERVICE_BASE_URL or "").rstrip("/")
        self.timeout_seconds = cfg.CHATBOT_SERVICE_TIMEOUT_SECONDS

    def _require_base(self):
        if not self.base_url:
            raise ValidationError("CHATBOT_SERVICE_BASE_URL is not configured")

    def send_message(self, *, payload: dict, trace_id: str | None = None) -> dict:
        self._require_base()
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        headers["X-Trace-Id"] = trace_id or str(uuid.uuid4())

        resp = requests.post(
            f"{self.base_url}/message",
            json=payload,
            headers=headers,
            timeout=self.timeout_seconds,
        )
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    def reset(self, *, payload: dict, trace_id: str | None = None) -> dict:
        self._require_base()
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        headers["X-Trace-Id"] = trace_id or str(uuid.uuid4())

        resp = requests.post(
            f"{self.base_url}/reset",
            json=payload,
            headers=headers,
            timeout=self.timeout_seconds,
        )
        resp.raise_for_status()
        return resp.json() if resp.content else {}
