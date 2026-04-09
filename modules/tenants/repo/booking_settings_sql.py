import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.errors import NotFoundError, ValidationError
from modules.tenants.models.booking_settings_orm import BookingSettingsORM


_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class SqlBookingSettingsRepo:
    def __init__(self, session: Session):
        self.session = session

    def _coerce_uuid(self, value: str | uuid.UUID) -> uuid.UUID | str:
        if isinstance(value, uuid.UUID):
            return value
        try:
            return uuid.UUID(str(value))
        except (TypeError, ValueError):
            return str(value)

    def _normalize_slug(self, value: str | None) -> str | None:
        if value is None:
            return None
        slug = value.strip().lower()
        if slug == "":
            return None
        if len(slug) < 3 or len(slug) > 80:
            raise ValidationError("booking_slug inválido (3–80 caracteres)")
        if not _SLUG_RE.match(slug):
            raise ValidationError("booking_slug inválido (use letras minúsculas, números e '-')")
        return slug

    def get_or_create(self, *, tenant_id: str) -> BookingSettingsORM:
        tenant_key = self._coerce_uuid(tenant_id)
        current = self.session.get(BookingSettingsORM, tenant_key)
        if current is not None:
            return current

        created = BookingSettingsORM(
            tenant_id=tenant_key,
            booking_enabled=False,
            booking_slug=None,
            public_business_name=None,
            public_contact_phone=None,
            public_contact_email=None,
            min_booking_notice_minutes=60,
            max_booking_notice_days=90,
            auto_confirm_bookings=True,
        )
        self.session.add(created)
        self.session.flush()
        return created

    def get_by_slug(self, *, slug: str) -> BookingSettingsORM | None:
        normalized = self._normalize_slug(slug)
        if normalized is None:
            return None
        stmt = select(BookingSettingsORM).where(BookingSettingsORM.booking_slug == normalized)
        return self.session.execute(stmt).scalar_one_or_none()

    def update(self, *, tenant_id: str, patch: dict) -> BookingSettingsORM:
        settings = self.get_or_create(tenant_id=tenant_id)

        normalized_patch: dict[str, object] = {}
        if "booking_enabled" in patch:
            normalized_patch["booking_enabled"] = bool(patch.get("booking_enabled"))
        if "booking_slug" in patch:
            normalized_patch["booking_slug"] = self._normalize_slug(patch.get("booking_slug"))
        if "public_business_name" in patch:
            name = (patch.get("public_business_name") or "").strip()
            normalized_patch["public_business_name"] = name or None
        if "public_contact_phone" in patch:
            phone = (patch.get("public_contact_phone") or "").strip()
            normalized_patch["public_contact_phone"] = phone or None
        if "public_contact_email" in patch:
            email = (patch.get("public_contact_email") or "").strip().lower()
            normalized_patch["public_contact_email"] = email or None
        if "min_booking_notice_minutes" in patch:
            value = patch.get("min_booking_notice_minutes")
            try:
                minutes = int(value)
            except (TypeError, ValueError):
                raise ValidationError("min_booking_notice_minutes inválido")
            if minutes < 0 or minutes > 60 * 24 * 30:
                raise ValidationError("min_booking_notice_minutes fora do intervalo")
            normalized_patch["min_booking_notice_minutes"] = minutes
        if "max_booking_notice_days" in patch:
            value = patch.get("max_booking_notice_days")
            try:
                days = int(value)
            except (TypeError, ValueError):
                raise ValidationError("max_booking_notice_days inválido")
            if days < 1 or days > 365:
                raise ValidationError("max_booking_notice_days fora do intervalo (1–365)")
            normalized_patch["max_booking_notice_days"] = days
        if "auto_confirm_bookings" in patch:
            normalized_patch["auto_confirm_bookings"] = bool(patch.get("auto_confirm_bookings"))

        for key, value in normalized_patch.items():
            setattr(settings, key, value)

        # Se enabled, exigimos slug + nome público
        if settings.booking_enabled:
            if not settings.booking_slug:
                raise ValidationError("Define um slug público para ativar o booking online")
            if not settings.public_business_name:
                raise ValidationError("Define um nome público do negócio para ativar o booking online")

        settings.updated_at = datetime.now(timezone.utc)
        try:
            self.session.flush()
        except IntegrityError:
            raise ValidationError("Este slug já está a ser usado por outro negócio")
        return settings

    def require_enabled_by_slug(self, *, slug: str) -> BookingSettingsORM:
        settings = self.get_by_slug(slug=slug)
        if settings is None:
            raise NotFoundError("booking_slug_not_found")
        if not settings.booking_enabled:
            raise NotFoundError("booking_disabled")
        return settings

