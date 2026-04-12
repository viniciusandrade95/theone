from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from core.auth import get_current_user_id
from core.observability.tracing import get_trace_id
from core.tenancy import get_tenant_id

_LOGGER = logging.getLogger("theone")

_LEVELS: dict[str, int] = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}


def log_event(event: str, *, level: str = "info", **fields: Any) -> None:
    """Structured JSON logging baseline.

    Avoids high-cardinality fields; call sites should not log PII (phones, tokens).
    """
    normalized_level = (level or "info").strip().lower()
    payload: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": normalized_level,
        "event": str(event),
        "trace_id": get_trace_id(),
        "tenant_id": get_tenant_id(),
        "user_id": get_current_user_id(),
        **{k: v for k, v in fields.items() if v is not None},
    }
    _LOGGER.log(_LEVELS.get(normalized_level, logging.INFO), json.dumps(payload, ensure_ascii=False, default=str))
