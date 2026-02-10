import uuid
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session

from core.errors import ValidationError
from modules.crm.repo_locations import LocationsRepo
from modules.tenants.models.tenant_orm import TenantORM
from modules.tenants.models.tenant_settings_orm import TenantSettingsORM

_ALLOWED_CALENDAR_VIEWS = {"week", "day"}


class SqlTenantSettingsRepo:
    def __init__(self, session: Session):
        self.session = session

    def _coerce_uuid(self, value: str | uuid.UUID) -> uuid.UUID | str:
        if isinstance(value, uuid.UUID):
            return value
        try:
            return uuid.UUID(str(value))
        except (TypeError, ValueError):
            return str(value)

    def _normalize_str(self, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    def _parse_uuid_or_none(self, value: str | uuid.UUID | None, *, error_key: str) -> uuid.UUID | None:
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        try:
            return uuid.UUID(str(value))
        except (TypeError, ValueError):
            raise ValidationError(error_key, meta={"value": value})

    def _normalize_timezone(self, value: str | None) -> str | None:
        normalized = self._normalize_str(value)
        if normalized is None:
            return None
        try:
            ZoneInfo(normalized)
        except ZoneInfoNotFoundError:
            raise ValidationError("invalid_timezone", meta={"timezone": value})
        return normalized

    def _normalize_calendar_view(self, value: str | None) -> str | None:
        normalized = self._normalize_str(value)
        if normalized is None:
            return None
        lowered = normalized.lower()
        if lowered not in _ALLOWED_CALENDAR_VIEWS:
            raise ValidationError(
                "invalid_calendar_default_view",
                meta={"calendar_default_view": value, "allowed": sorted(_ALLOWED_CALENDAR_VIEWS)},
            )
        return lowered

    def _resolve_default_location_id(
        self,
        *,
        tenant_id: str,
        desired_location_id: str | uuid.UUID | None,
        fallback_timezone: str,
    ) -> uuid.UUID:
        locations_repo = LocationsRepo(self.session)
        parsed_desired_location_id = self._parse_uuid_or_none(
            desired_location_id,
            error_key="invalid_default_location_id",
        )

        if parsed_desired_location_id is not None:
            candidate = locations_repo.get_location(
                tenant_id=tenant_id,
                location_id=str(parsed_desired_location_id),
            )
            if candidate is not None and candidate.is_active and candidate.deleted_at is None:
                return candidate.id

        ensured = locations_repo.ensure_default_location(tenant_id=tenant_id, default_timezone=fallback_timezone)
        return ensured.id

    def get_or_create(self, tenant_id: str) -> TenantSettingsORM:
        tenant_key = self._coerce_uuid(tenant_id)
        settings = self.session.get(TenantSettingsORM, tenant_key)

        if settings is None:
            tenant = self.session.get(TenantORM, tenant_key)
            fallback_timezone = "UTC"
            default_location_id = self._resolve_default_location_id(
                tenant_id=tenant_id,
                desired_location_id=None,
                fallback_timezone=fallback_timezone,
            )
            location = LocationsRepo(self.session).get_location(
                tenant_id=tenant_id,
                location_id=str(default_location_id),
            )

            settings = TenantSettingsORM(
                tenant_id=tenant_key,
                business_name=tenant.name if tenant is not None else None,
                default_timezone=location.timezone if location is not None else fallback_timezone,
                currency="USD",
                calendar_default_view="week",
                default_location_id=default_location_id,
            )
            self.session.add(settings)
            self.session.flush()
            return settings

        default_timezone = self._normalize_timezone(settings.default_timezone) or "UTC"
        resolved_default_location_id = self._resolve_default_location_id(
            tenant_id=tenant_id,
            desired_location_id=settings.default_location_id,
            fallback_timezone=default_timezone,
        )

        if settings.default_location_id != resolved_default_location_id:
            settings.default_location_id = resolved_default_location_id
            settings.updated_at = datetime.now(timezone.utc)
            self.session.flush()

        return settings

    def update(self, tenant_id: str, patch: dict) -> TenantSettingsORM:
        settings = self.get_or_create(tenant_id)
        normalized_patch: dict[str, str | uuid.UUID | None] = {}

        if "business_name" in patch:
            normalized_patch["business_name"] = self._normalize_str(patch.get("business_name"))
        if "default_timezone" in patch:
            normalized_patch["default_timezone"] = self._normalize_timezone(patch.get("default_timezone"))
        if "currency" in patch:
            currency = self._normalize_str(patch.get("currency"))
            normalized_patch["currency"] = currency.upper() if currency else None
        if "calendar_default_view" in patch:
            normalized_patch["calendar_default_view"] = self._normalize_calendar_view(patch.get("calendar_default_view"))
        if "primary_color" in patch:
            normalized_patch["primary_color"] = self._normalize_str(patch.get("primary_color"))
        if "logo_url" in patch:
            normalized_patch["logo_url"] = self._normalize_str(patch.get("logo_url"))

        if "default_location_id" in patch:
            desired_location_id = patch.get("default_location_id")
            if desired_location_id is None:
                normalized_patch["default_location_id"] = self._resolve_default_location_id(
                    tenant_id=tenant_id,
                    desired_location_id=None,
                    fallback_timezone=settings.default_timezone or "UTC",
                )
            else:
                parsed_location_id = self._parse_uuid_or_none(
                    desired_location_id,
                    error_key="invalid_default_location_id",
                )
                location = LocationsRepo(self.session).get_location(
                    tenant_id=tenant_id,
                    location_id=str(parsed_location_id),
                )
                if location is None or not location.is_active or location.deleted_at is not None:
                    raise ValidationError(
                        "default_location_not_found",
                        meta={"default_location_id": str(parsed_location_id)},
                    )
                normalized_patch["default_location_id"] = location.id

        for key, value in normalized_patch.items():
            if value is None and key in {"default_timezone", "currency", "calendar_default_view"}:
                continue
            setattr(settings, key, value)

        resolved_default_location_id = self._resolve_default_location_id(
            tenant_id=tenant_id,
            desired_location_id=settings.default_location_id,
            fallback_timezone=settings.default_timezone or "UTC",
        )
        settings.default_location_id = resolved_default_location_id
        settings.updated_at = datetime.now(timezone.utc)
        self.session.flush()
        return settings
