from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class PrebookCustomerIn(BaseModel):
    customer_id: str | None = None
    name: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=40)
    email: EmailStr | None = None


class PrebookBookingIn(BaseModel):
    service_id: str
    location_id: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    requested_date: str | None = Field(default=None, min_length=10, max_length=10)  # "YYYY-MM-DD"
    requested_time: str | None = Field(default=None, min_length=4, max_length=5)  # "HH:MM"
    timezone: str | None = Field(default=None, max_length=64)
    notes: str | None = Field(default=None, max_length=1000)


class PrebookIn(BaseModel):
    tenant_id: str | None = None
    conversation_id: str | None = None
    session_id: str | None = None
    trace_id: str | None = None
    idempotency_key: str | None = None
    customer: PrebookCustomerIn
    booking: PrebookBookingIn
    meta: dict[str, Any] = Field(default_factory=dict)
