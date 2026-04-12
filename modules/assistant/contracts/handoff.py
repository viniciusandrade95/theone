from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from modules.assistant.contracts.common import AssistantActionEnvelopeV1


HandoffPriorityV1 = Literal["low", "normal", "high", "urgent"]
HandoffStatusV1 = Literal["open", "accepted", "closed", "expired"]


class AssistantHandoffRequestInV1(AssistantActionEnvelopeV1):
    """Create a handoff request (contract v1)."""

    reason: str = Field(min_length=1, max_length=500, description="Why the assistant requests a human handoff.")
    priority: HandoffPriorityV1 = Field(default="normal")
    queue_key: str = Field(min_length=1, max_length=64, description="Routing key for human queue selection.")
    summary: str = Field(min_length=1, max_length=2000, description="Short human-readable summary for the operator.")
    context: dict[str, Any] = Field(default_factory=dict, description="Structured context (non-PII when possible).")
    requested_sla_minutes: int | None = Field(
        default=None,
        ge=1,
        le=7 * 24 * 60,
        description="Requested SLA in minutes for first response.",
    )


class AssistantHandoffAcceptedByV1(BaseModel):
    actor_type: Literal["staff", "system"] = "staff"
    actor_id: UUID | None = None
    name: str | None = Field(default=None, max_length=255)


class AssistantHandoffResponseOutV1(BaseModel):
    ok: bool = True
    trace_id: str
    handoff_id: UUID
    status: HandoffStatusV1
    queue_key: str
    accepted_by: AssistantHandoffAcceptedByV1 | None = None
    opened_at: datetime
    updated_at: datetime

