from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.errors import ValidationError
from modules.assistant.contracts.slot_finding import AssistantAvailabilitySlotOutV1
from modules.crm.models.location_orm import LocationORM
from modules.crm.models.service_orm import ServiceORM
from modules.crm.repo_locations import LocationsRepo
from modules.tenants.repo.booking_settings_sql import SqlBookingSettingsRepo

# Reuse the existing public booking availability source-of-truth helpers.
from app.http.routes.public_booking import (  # noqa: PLC0415
    _ensure_tz,
    _hours_for_location,
    _busy_intervals,
    _interval_free,
    _ceil_dt,
)


class SlotFindingService:
    def __init__(self, session: Session):
        self.session = session

    def _resolve_service(self, *, tenant_id: str, service_id: str) -> ServiceORM:
        try:
            svc_uuid = uuid.UUID(service_id)
        except ValueError:
            raise ValidationError("Serviço inválido.", meta={"field": "service_id"})
        stmt = (
            select(ServiceORM)
            .where(ServiceORM.tenant_id == uuid.UUID(tenant_id))
            .where(ServiceORM.id == svc_uuid)
            .where(ServiceORM.deleted_at.is_(None))
        )
        svc = self.session.execute(stmt).scalar_one_or_none()
        if svc is None:
            raise ValidationError("Serviço inválido.", meta={"field": "service_id"})
        if not svc.is_active:
            raise ValidationError("Este serviço não está disponível.", meta={"field": "service_id"})
        if not getattr(svc, "is_bookable_online", False):
            raise ValidationError("Este serviço não está disponível para marcação online.", meta={"field": "service_id"})
        return svc

    def _resolve_location(self, *, tenant_id: str, location_id: str | None) -> LocationORM:
        repo = LocationsRepo(self.session)
        if location_id:
            location = repo.get_location(tenant_id=tenant_id, location_id=location_id, include_deleted=False)
            if location is None or not location.is_active:
                raise ValidationError("Localização inválida.", meta={"field": "location_id"})
            return location
        return repo.ensure_default_location(tenant_id=tenant_id)

    def find_slots(
        self,
        *,
        tenant_id: str,
        service_id: str,
        target_date: date,
        location_id: str | None = None,
        limit: int = 5,
    ) -> tuple[str, str, str, list[AssistantAvailabilitySlotOutV1]]:
        """Return real availability slots based on the existing booking rules.

        Returns (service_id, location_id, timezone, slots).
        """

        service = self._resolve_service(tenant_id=tenant_id, service_id=service_id)
        location = self._resolve_location(tenant_id=tenant_id, location_id=location_id)

        settings = SqlBookingSettingsRepo(self.session).get_or_create(tenant_id=tenant_id)

        tz = _ensure_tz(location.timezone)
        hours = _hours_for_location(location, target_date)
        if hours is None:
            return str(service.id), str(location.id), str(tz), []

        start_local = datetime.combine(target_date, hours.opens_at, tzinfo=tz)
        end_local = datetime.combine(target_date, hours.closes_at, tzinfo=tz)
        from_utc = start_local.astimezone(timezone.utc)
        to_utc = end_local.astimezone(timezone.utc)

        busy = _busy_intervals(self.session, tenant_id, location.id, from_utc, to_utc)
        duration = int(service.duration_minutes)
        step_minutes = 15

        now_local = datetime.now(timezone.utc).astimezone(tz)
        earliest = _ceil_dt(
            now_local + timedelta(minutes=int(settings.min_booking_notice_minutes)),
            step_minutes=step_minutes,
        )
        latest = now_local + timedelta(days=int(settings.max_booking_notice_days))

        cursor = _ceil_dt(start_local, step_minutes=step_minutes)
        slots: list[AssistantAvailabilitySlotOutV1] = []
        while cursor + timedelta(minutes=duration) <= end_local:
            if cursor >= earliest and cursor + timedelta(minutes=duration) <= latest:
                candidate_start_utc = cursor.astimezone(timezone.utc)
                candidate_end_utc = (cursor + timedelta(minutes=duration)).astimezone(timezone.utc)
                if _interval_free(candidate_start_utc, candidate_end_utc, busy):
                    slots.append(
                        AssistantAvailabilitySlotOutV1(
                            starts_at=candidate_start_utc,
                            ends_at=candidate_end_utc,
                            label=cursor.strftime("%H:%M"),
                        )
                    )
                    if len(slots) >= int(limit):
                        break
            cursor = cursor + timedelta(minutes=step_minutes)

        return str(service.id), str(location.id), str(tz), slots

