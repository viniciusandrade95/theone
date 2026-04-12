from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


_IDEMPOTENCY_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:._-]{0,254}$")


AssistantSourceV1 = Literal["dashboard", "chatbot1", "api", "system"]
AssistantActorTypeV1 = Literal["staff", "system", "customer", "service"]


class AssistantActorV1(BaseModel):
    type: AssistantActorTypeV1 = Field(description="Actor category for audit/governance.")
    id: UUID | None = Field(default=None, description="Actor id when applicable (e.g. staff user UUID).")


class AssistantActionEnvelopeV1(BaseModel):
    """Common envelope for assistant operational actions (v1).

    This is contract-first and intentionally minimal:
    - IDs are UUIDs when they represent CRM entities or tenant boundaries.
    - session_id may be non-UUID (chatbot runtime), so it stays as string.
    """

    trace_id: str = Field(min_length=8, max_length=128, description="Correlation id (propagated via X-Trace-Id).")
    tenant_id: UUID = Field(description="Tenant (workspace) id.")
    conversation_id: UUID | None = Field(default=None, description="Assistant conversation id, when known.")
    session_id: str | None = Field(
        default=None,
        max_length=255,
        description="Assistant session id (may be non-UUID, e.g. chatbot runtime session).",
    )
    customer_id: UUID | None = Field(default=None, description="Customer id, when the action is tied to a customer.")
    source: AssistantSourceV1 = Field(description="Origin of the action.")
    actor: AssistantActorV1 = Field(description="Who/what initiated the action.")
    idempotency_key: str | None = Field(
        default=None,
        max_length=255,
        description="Idempotency key for safe retries. Must be stable for the same intent.",
    )
    meta: dict[str, Any] = Field(default_factory=dict, description="Low-risk operational metadata (non-PII).")

    @model_validator(mode="after")
    def _validate_idempotency_key(self) -> "AssistantActionEnvelopeV1":
        if self.idempotency_key is None:
            return self
        key = str(self.idempotency_key).strip()
        if not key:
            self.idempotency_key = None
            return self
        if not _IDEMPOTENCY_KEY_RE.fullmatch(key):
            raise ValueError("idempotency_key must be <=255 chars and match ^[A-Za-z0-9][A-Za-z0-9:._-]*$")
        self.idempotency_key = key
        return self


class AssistantTimeWindowV1(BaseModel):
    """Reusable time window shape (v1).

    - Prefer RFC3339 datetimes when possible (starts_at/ends_at).
    - For conversational inputs, requested_date/requested_time + timezone is allowed.
    """

    starts_at: datetime | None = None
    ends_at: datetime | None = None
    requested_date: str | None = Field(default=None, description='Local date "YYYY-MM-DD".')
    requested_time: str | None = Field(default=None, description='Local time "HH:MM".')
    timezone: str | None = Field(default=None, max_length=64, description="IANA timezone name, e.g. Europe/Lisbon.")

    @model_validator(mode="after")
    def _validate_window(self) -> "AssistantTimeWindowV1":
        if self.starts_at is not None and self.ends_at is not None:
            if self.starts_at.tzinfo is None or self.ends_at.tzinfo is None:
                raise ValueError("starts_at/ends_at must be timezone-aware")
            if self.starts_at >= self.ends_at:
                raise ValueError("starts_at must be before ends_at")
        if self.ends_at is not None and self.starts_at is None:
            raise ValueError("ends_at requires starts_at")
        if self.starts_at is None:
            if self.requested_date is None or self.requested_time is None:
                # No window provided; allow higher-level schemas to decide requirements.
                return self
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(self.requested_date)):
                raise ValueError("requested_date must be YYYY-MM-DD")
            if not re.fullmatch(r"\d{1,2}:\d{2}", str(self.requested_time)):
                raise ValueError("requested_time must be HH:MM")
        return self

