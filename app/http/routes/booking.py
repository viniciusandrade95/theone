from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.http.deps import require_tenant_header, require_user
from core.db.session import db_session
from core.tenancy import require_tenant_id
from modules.tenants.repo.booking_settings_sql import SqlBookingSettingsRepo


router = APIRouter()


class BookingSettingsOut(BaseModel):
    tenant_id: str
    booking_enabled: bool
    booking_slug: str | None
    public_business_name: str | None
    public_contact_phone: str | None
    public_contact_email: str | None
    min_booking_notice_minutes: int
    max_booking_notice_days: int
    auto_confirm_bookings: bool
    created_at: datetime
    updated_at: datetime
    public_url_path: str | None


class BookingSettingsUpdateIn(BaseModel):
    booking_enabled: bool | None = None
    booking_slug: str | None = Field(default=None, max_length=80)
    public_business_name: str | None = Field(default=None, max_length=255)
    public_contact_phone: str | None = Field(default=None, max_length=40)
    public_contact_email: str | None = Field(default=None, max_length=255)
    min_booking_notice_minutes: int | None = Field(default=None, ge=0)
    max_booking_notice_days: int | None = Field(default=None, ge=1)
    auto_confirm_bookings: bool | None = None


def _to_out(settings) -> BookingSettingsOut:
    slug = settings.booking_slug
    return BookingSettingsOut(
        tenant_id=str(settings.tenant_id),
        booking_enabled=bool(settings.booking_enabled),
        booking_slug=slug,
        public_business_name=settings.public_business_name,
        public_contact_phone=settings.public_contact_phone,
        public_contact_email=settings.public_contact_email,
        min_booking_notice_minutes=int(settings.min_booking_notice_minutes),
        max_booking_notice_days=int(settings.max_booking_notice_days),
        auto_confirm_bookings=bool(settings.auto_confirm_bookings),
        created_at=settings.created_at,
        updated_at=settings.updated_at,
        public_url_path=f"/book/{slug}" if slug else None,
    )


@router.get("/booking/settings", response_model=BookingSettingsOut)
def get_booking_settings(_tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    tenant_id = require_tenant_id()
    with db_session() as session:
        repo = SqlBookingSettingsRepo(session)
        settings = repo.get_or_create(tenant_id=tenant_id)
        return _to_out(settings)


@router.put("/booking/settings", response_model=BookingSettingsOut)
def update_booking_settings(payload: BookingSettingsUpdateIn, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    patch = payload.model_dump(exclude_unset=True)
    tenant_id = require_tenant_id()
    with db_session() as session:
        repo = SqlBookingSettingsRepo(session)
        settings = repo.update(tenant_id=tenant_id, patch=patch)
        return _to_out(settings)

