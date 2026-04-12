from __future__ import annotations

import uuid
from contextvars import ContextVar

from fastapi import Request

_trace_id: ContextVar[str | None] = ContextVar("trace_id", default=None)

TRACE_HEADER_NAME = "X-Trace-Id"


def generate_trace_id() -> str:
    # Keep it compact + safe for logs/headers.
    return uuid.uuid4().hex


def set_trace_id(trace_id: str) -> None:
    cleaned = (trace_id or "").strip()
    if not cleaned:
        cleaned = generate_trace_id()
    _trace_id.set(cleaned)


def get_trace_id() -> str | None:
    return _trace_id.get()


def require_trace_id() -> str:
    trace_id = get_trace_id()
    if trace_id is None:
        raise RuntimeError("Missing trace context (trace_id not set)")
    return trace_id


def clear_trace_id() -> None:
    _trace_id.set(None)


def ensure_trace_id(request: Request | None = None) -> str:
    """Ensure a trace_id exists in context, preserving X-Trace-Id when provided."""
    existing = get_trace_id()
    if existing:
        return existing

    header_value = None
    if request is not None:
        header_value = request.headers.get(TRACE_HEADER_NAME)
    resolved = (header_value or "").strip() or generate_trace_id()
    set_trace_id(resolved)
    return resolved
