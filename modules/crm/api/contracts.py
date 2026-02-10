from dataclasses import dataclass
import re
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, EmailStr, Field, field_validator

from modules.crm.models.pipeline import PipelineStage

@dataclass(frozen=True)
class CreateCustomerRequest:
    name: str
    phone: str | None = None
    email: str | None = None

@dataclass(frozen=True)
class AddInteractionRequest:
    type: str
    content: str

@dataclass(frozen=True)
class MoveStageRequest:
    to_stage: PipelineStage


def _normalize_phone(value: str | None) -> str | None:
    if value is None:
        return None
    raw = value.strip()
    if raw == "":
        return None

    compact = re.sub(r"[^\d+]", "", raw)
    if compact.count("+") > 1 or ("+" in compact and not compact.startswith("+")):
        raise ValueError("Invalid phone format")

    digits = compact[1:] if compact.startswith("+") else compact
    if not digits.isdigit():
        raise ValueError("Invalid phone format")

    return f"+{digits}" if compact.startswith("+") else digits


class LocationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    timezone: str = Field(min_length=1, max_length=120)
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    postcode: str | None = None
    country: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    is_active: bool = True
    hours_json: dict | None = None
    allow_overlaps: bool = False

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        tz = value.strip()
        try:
            ZoneInfo(tz)
        except ZoneInfoNotFoundError:
            raise ValueError("Invalid IANA timezone")
        return tz

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str | None) -> str | None:
        return _normalize_phone(value)


class LocationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    timezone: str | None = Field(default=None, min_length=1, max_length=120)
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    postcode: str | None = None
    country: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    is_active: bool | None = None
    hours_json: dict | None = None
    allow_overlaps: bool | None = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        tz = value.strip()
        try:
            ZoneInfo(tz)
        except ZoneInfoNotFoundError:
            raise ValueError("Invalid IANA timezone")
        return tz

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str | None) -> str | None:
        return _normalize_phone(value)


class LocationOut(BaseModel):
    id: str
    tenant_id: str
    name: str
    timezone: str
    address_line1: str | None
    address_line2: str | None
    city: str | None
    postcode: str | None
    country: str | None
    phone: str | None
    email: EmailStr | None
    is_active: bool
    hours_json: dict | None
    allow_overlaps: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class LocationListOut(BaseModel):
    items: list[LocationOut]


class LocationDefaultOut(BaseModel):
    id: str
    name: str
    timezone: str
    allow_overlaps: bool
    hours_json: dict | None
