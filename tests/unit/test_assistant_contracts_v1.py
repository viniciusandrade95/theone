from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from modules.assistant.contracts import (
    AssistantActionEnvelopeV1,
    AssistantConsultRequestInV1,
    AssistantHandoffRequestInV1,
    AssistantQuoteRequestInV1,
    AssistantTimeWindowV1,
)


def _base_envelope() -> dict:
    return {
        "trace_id": "d7c2d4c7d04a4df8b02a2e4c37a1f9c1",
        "tenant_id": str(uuid4()),
        "conversation_id": None,
        "session_id": "chatbot-session-123",
        "customer_id": None,
        "source": "chatbot1",
        "actor": {"type": "service", "id": None},
        "idempotency_key": "x:1",
        "meta": {},
    }


def test_envelope_accepts_valid_payload():
    env = AssistantActionEnvelopeV1(**_base_envelope())
    assert env.trace_id
    assert env.idempotency_key == "x:1"


def test_envelope_strips_empty_idempotency_key_to_none():
    payload = _base_envelope()
    payload["idempotency_key"] = "   "
    env = AssistantActionEnvelopeV1(**payload)
    assert env.idempotency_key is None


def test_envelope_rejects_invalid_idempotency_key_chars():
    payload = _base_envelope()
    payload["idempotency_key"] = "bad key with spaces"
    with pytest.raises(ValidationError):
        AssistantActionEnvelopeV1(**payload)


def test_time_window_rejects_ends_without_starts():
    with pytest.raises(ValidationError):
        AssistantTimeWindowV1(ends_at=datetime.now(tz=UTC))


def test_time_window_requires_timezone_aware_datetimes():
    with pytest.raises(ValidationError):
        AssistantTimeWindowV1(starts_at=datetime(2026, 4, 20, 10, 0), ends_at=datetime(2026, 4, 20, 11, 0))


def test_time_window_rejects_invalid_requested_date():
    with pytest.raises(ValidationError):
        AssistantTimeWindowV1(requested_date="2026/04/20", requested_time="10:00", timezone="Europe/Lisbon")


def test_quote_requires_at_least_one_service_id():
    payload = {**_base_envelope(), "service_ids": [], "location_id": None, "requested_window": None, "constraints": {}, "notes": None}
    with pytest.raises(ValidationError):
        AssistantQuoteRequestInV1(**payload)


def test_handoff_accepts_minimal_valid_payload():
    payload = {
        **_base_envelope(),
        "reason": "validation_error",
        "queue_key": "ops.booking",
        "summary": "Cliente pediu agendamento, mas data/hora inválidas repetidamente.",
        "context": {},
        "requested_sla_minutes": 30,
    }
    req = AssistantHandoffRequestInV1(**payload)
    assert req.priority == "normal"
    assert req.queue_key == "ops.booking"


def test_consult_enforces_preferred_windows_max_5():
    preferred_windows = []
    now = datetime.now(tz=UTC)
    for i in range(6):
        preferred_windows.append(
            {
                "starts_at": (now + timedelta(days=i)).isoformat(),
                "ends_at": (now + timedelta(days=i, minutes=30)).isoformat(),
                "requested_date": None,
                "requested_time": None,
                "timezone": None,
            }
        )

    payload = {
        **_base_envelope(),
        "consult_type": "whatsapp",
        "service_interest": {"service_ids": [], "free_text": "Avaliar corte e barba"},
        "preferred_windows": preferred_windows,
        "location_preference": {"location_id": None, "free_text": "Centro"},
        "notes": None,
        "context": {},
    }
    with pytest.raises(ValidationError):
        AssistantConsultRequestInV1(**payload)
