from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field, model_validator


class PrebookCustomerIn(BaseModel):
    customer_id: str | None = None
    name: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=40)
    email: EmailStr | None = None

    @model_validator(mode="after")
    def _validate_customer(self):
        if (self.customer_id or "").strip():
            return self
        if not (self.name or "").strip():
            raise ValueError("customer.name is required when customer_id is not provided")
        if not (self.phone or "").strip() and not (str(self.email or "").strip()):
            raise ValueError("customer.phone or customer.email is required when customer_id is not provided")
        return self


class PrebookBookingIn(BaseModel):
    service_id: str
    location_id: str | None = None
    requested_date: str = Field(min_length=10, max_length=10)  # "YYYY-MM-DD"
    requested_time: str = Field(min_length=4, max_length=5)  # "HH:MM"
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    timezone: str | None = Field(default=None, max_length=64)
    notes: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def _validate_booking_format(self):
        # Force strict parsing to raise 422 for malformed dates/times.
        from datetime import date as _date
        from datetime import time as _time

        try:
            _date.fromisoformat(self.requested_date)
        except ValueError:
            raise ValueError("booking.requested_date must be YYYY-MM-DD")
        try:
            _time.fromisoformat(self.requested_time)
        except ValueError:
            raise ValueError("booking.requested_time must be HH:MM")
        return self


class PrebookIn(BaseModel):
    tenant_id: str | None = None
    session_id: str | None = None
    trace_id: str | None = None
    idempotency_key: str | None = None
    customer: PrebookCustomerIn
    booking: PrebookBookingIn
    meta: dict[str, Any] = Field(default_factory=dict)
