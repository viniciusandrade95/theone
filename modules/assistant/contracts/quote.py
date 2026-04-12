from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from modules.assistant.contracts.common import AssistantActionEnvelopeV1, AssistantTimeWindowV1


QuoteStatusV1 = Literal["open", "in_review", "proposed", "accepted", "rejected", "expired"]


class AssistantQuoteConstraintsV1(BaseModel):
    """Loose but validateable constraint container for quote requests."""

    budget_max_cents: int | None = Field(default=None, ge=0)
    professional_preference: str | None = Field(default=None, max_length=255)
    extra: dict[str, Any] = Field(default_factory=dict)


class AssistantQuoteRequestInV1(AssistantActionEnvelopeV1):
    service_ids: list[UUID] = Field(min_length=1, description="At least one service id is required.")
    location_id: UUID | None = None
    requested_window: AssistantTimeWindowV1 | None = None
    constraints: AssistantQuoteConstraintsV1 = Field(default_factory=AssistantQuoteConstraintsV1)
    notes: str | None = Field(default=None, max_length=2000)


class AssistantQuoteResponseOutV1(BaseModel):
    ok: bool = True
    trace_id: str
    quote_request_id: UUID
    status: QuoteStatusV1
    service_ids: list[UUID]
    location_id: UUID | None
    summary: str | None = Field(default=None, max_length=2000)
    created_at: datetime
    updated_at: datetime

