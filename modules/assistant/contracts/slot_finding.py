from __future__ import annotations

from datetime import date as dt_date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from modules.assistant.contracts.common import AssistantActionEnvelopeV1


class AssistantSlotFindingRequestInV1(AssistantActionEnvelopeV1):
    """Find real booking availability slots (contract v1).

    This contract is intentionally minimal and maps directly onto the existing
    public booking availability source-of-truth.
    """

    service_id: UUID = Field(description="Service id to check availability for.")
    date: dt_date = Field(description="Target local date for the location (YYYY-MM-DD).")
    location_id: UUID | None = Field(default=None, description="Location id (optional; defaults to tenant default).")
    limit: int = Field(default=5, ge=1, le=10, description="Max slots to return (low cardinality).")


class AssistantAvailabilitySlotOutV1(BaseModel):
    starts_at: datetime = Field(description="UTC RFC3339 datetime.")
    ends_at: datetime = Field(description="UTC RFC3339 datetime.")
    label: str = Field(description='Local label, e.g. "10:30".')


class AssistantSlotFindingResponseOutV1(BaseModel):
    ok: bool = True
    trace_id: str
    service_id: UUID
    location_id: UUID
    date: str
    timezone: str
    slots: list[AssistantAvailabilitySlotOutV1]


AssistantSlotFindingOutcomeV1 = Literal["success", "missing_info", "no_slots", "invalid"]


class AssistantSlotSuggestionsActionV1(BaseModel):
    """Action payload appended into the normalized chatbot response.

    Frontend can rely on this for structured slot display without parsing text.
    """

    type: Literal["assistant.slot_suggestions.v1"] = "assistant.slot_suggestions.v1"
    outcome: AssistantSlotFindingOutcomeV1
    trace_id: str
    service_id: UUID | None = None
    location_id: UUID | None = None
    date: str | None = None
    timezone: str | None = None
    slots: list[AssistantAvailabilitySlotOutV1] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list, description='Missing fields (e.g. ["service_id","date"]).')
    message: str | None = None
