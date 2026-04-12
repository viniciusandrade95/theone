from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from modules.assistant.contracts.common import AssistantActionEnvelopeV1, AssistantTimeWindowV1


ConsultTypeV1 = Literal["in_person", "phone", "video", "whatsapp", "unspecified"]
ConsultStatusV1 = Literal["open", "contacting", "scheduled", "completed", "cancelled"]


class AssistantConsultServiceInterestV1(BaseModel):
    """Structured service interest (v1).

    Supports both structured service ids and a free-text fallback.
    """

    service_ids: list[UUID] = Field(default_factory=list)
    free_text: str | None = Field(default=None, max_length=255)


class AssistantLocationPreferenceV1(BaseModel):
    location_id: UUID | None = None
    free_text: str | None = Field(default=None, max_length=255)


class AssistantConsultRequestInV1(AssistantActionEnvelopeV1):
    consult_type: ConsultTypeV1 = "unspecified"
    service_interest: AssistantConsultServiceInterestV1 = Field(default_factory=AssistantConsultServiceInterestV1)
    preferred_windows: list[AssistantTimeWindowV1] = Field(default_factory=list, max_length=5)
    location_preference: AssistantLocationPreferenceV1 | None = None
    notes: str | None = Field(default=None, max_length=2000)
    context: dict[str, Any] = Field(default_factory=dict)


class AssistantConsultResponseOutV1(BaseModel):
    ok: bool = True
    trace_id: str
    consult_request_id: UUID
    status: ConsultStatusV1
    consult_type: ConsultTypeV1
    created_at: datetime
    updated_at: datetime

