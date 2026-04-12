import uuid

import requests

from core.config import get_config
from core.errors import ValidationError
from core.observability.logging import log_event
from core.observability.metrics import inc_counter, observe_histogram, start_timer
from core.observability.tracing import get_trace_id


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
        effective_trace_id = trace_id or get_trace_id() or str(uuid.uuid4())
        headers = {"Content-Type": "application/json", "Accept": "application/json", "X-Trace-Id": effective_trace_id}

        timer = start_timer()
        log_event("assistant_chatbot_upstream_started", url=f"{self.base_url}/message")
        try:
            resp = requests.post(
                f"{self.base_url}/message",
                json=payload,
                headers=headers,
                timeout=self.timeout_seconds,
            )
            resp.raise_for_status()
            inc_counter("assistant_chatbot_upstream_requests_total", labels={"outcome": "success"})
            return resp.json() if resp.content else {}
        except Exception as exc:
            inc_counter("assistant_chatbot_upstream_requests_total", labels={"outcome": "error"})
            log_event("assistant_chatbot_upstream_failed", level="error", error=str(exc))
            raise
        finally:
            observe_histogram("assistant_chatbot_upstream_duration_seconds", value=timer.seconds())
            log_event("assistant_chatbot_upstream_completed", duration_ms=int(timer.seconds() * 1000))

    def reset(self, *, payload: dict, trace_id: str | None = None) -> dict:
        self._require_base()
        effective_trace_id = trace_id or get_trace_id() or str(uuid.uuid4())
        headers = {"Content-Type": "application/json", "Accept": "application/json", "X-Trace-Id": effective_trace_id}

        timer = start_timer()
        log_event("assistant_chatbot_upstream_started", url=f"{self.base_url}/reset")
        try:
            resp = requests.post(
                f"{self.base_url}/reset",
                json=payload,
                headers=headers,
                timeout=self.timeout_seconds,
            )
            resp.raise_for_status()
            inc_counter("assistant_chatbot_upstream_requests_total", labels={"outcome": "success"})
            return resp.json() if resp.content else {}
        except Exception as exc:
            inc_counter("assistant_chatbot_upstream_requests_total", labels={"outcome": "error"})
            log_event("assistant_chatbot_upstream_failed", level="error", error=str(exc))
            raise
        finally:
            observe_histogram("assistant_chatbot_upstream_duration_seconds", value=timer.seconds())
            log_event("assistant_chatbot_upstream_completed", duration_ms=int(timer.seconds() * 1000))
