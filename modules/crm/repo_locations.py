import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from core.errors import NotFoundError
from modules.audit.logging import record_audit_log, snapshot_orm
from modules.crm.models.location_orm import LocationORM


@dataclass
class LocationCreateData:
    name: str
    timezone: str
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    postcode: str | None = None
    country: str | None = None
    phone: str | None = None
    email: str | None = None
    is_active: bool = True
    hours_json: dict | None = None
    allow_overlaps: bool = False


class LocationsRepo:
    def __init__(self, session: Session):
        self.session = session

    def _coerce_uuid(self, value: str | uuid.UUID) -> uuid.UUID | str:
        if isinstance(value, uuid.UUID):
            return value
        try:
            return uuid.UUID(str(value))
        except (TypeError, ValueError):
            return str(value)

    def _normalize_email(self, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        return normalized or None

    def _trim(self, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    def create_location(self, tenant_id: str, payload: LocationCreateData) -> LocationORM:
        location = LocationORM(
            id=uuid.uuid4(),
            tenant_id=self._coerce_uuid(tenant_id),
            name=payload.name.strip(),
            timezone=payload.timezone.strip(),
            address_line1=self._trim(payload.address_line1),
            address_line2=self._trim(payload.address_line2),
            city=self._trim(payload.city),
            postcode=self._trim(payload.postcode),
            country=self._trim(payload.country),
            phone=self._trim(payload.phone),
            email=self._normalize_email(payload.email),
            is_active=payload.is_active,
            hours_json=payload.hours_json,
            allow_overlaps=payload.allow_overlaps,
        )
        self.session.add(location)
        self.session.flush()
        record_audit_log(
            self.session,
            tenant_id=location.tenant_id,
            action="created",
            entity_type="location",
            entity_id=location.id,
            before=None,
            after=snapshot_orm(location),
        )
        return location

    def list_locations(
        self,
        tenant_id: str,
        include_inactive: bool = False,
        include_deleted: bool = False,
    ) -> list[LocationORM]:
        stmt = (
            select(LocationORM)
            .where(LocationORM.tenant_id == self._coerce_uuid(tenant_id))
            .order_by(LocationORM.created_at.asc())
        )
        if not include_inactive:
            stmt = stmt.where(LocationORM.is_active.is_(True))
        if not include_deleted:
            stmt = stmt.where(LocationORM.deleted_at.is_(None))
        return list(self.session.execute(stmt).scalars().all())

    def get_location(self, tenant_id: str, location_id: str, include_deleted: bool = False) -> LocationORM | None:
        stmt = (
            select(LocationORM)
            .where(
                and_(
                    LocationORM.tenant_id == self._coerce_uuid(tenant_id),
                    LocationORM.id == self._coerce_uuid(location_id),
                )
            )
        )
        if not include_deleted:
            stmt = stmt.where(LocationORM.deleted_at.is_(None))
        return self.session.execute(stmt).scalar_one_or_none()

    def get_default_location(self, tenant_id: str) -> LocationORM | None:
        stmt = (
            select(LocationORM)
            .where(LocationORM.tenant_id == self._coerce_uuid(tenant_id))
            .where(LocationORM.deleted_at.is_(None))
            .where(LocationORM.is_active.is_(True))
            .order_by(LocationORM.created_at.asc())
            .limit(1)
        )
        return self.session.execute(stmt).scalars().first()

    def ensure_default_location(self, tenant_id: str, default_timezone: str = "UTC") -> LocationORM:
        current = self.get_default_location(tenant_id)
        if current is not None:
            return current
        return self.create_location(
            tenant_id=tenant_id,
            payload=LocationCreateData(
                name="Main Location",
                timezone=default_timezone,
                is_active=True,
                allow_overlaps=False,
            ),
        )

    def update_location(self, tenant_id: str, location_id: str, patch: dict) -> LocationORM:
        location = self.get_location(tenant_id, location_id, include_deleted=True)
        if location is None:
            raise NotFoundError("location_not_found", meta={"location_id": location_id})
        before = snapshot_orm(location)

        for key, value in patch.items():
            if key == "email":
                setattr(location, key, self._normalize_email(value))
            elif isinstance(value, str):
                setattr(location, key, self._trim(value))
            else:
                setattr(location, key, value)
        location.updated_at = datetime.now(timezone.utc)
        self.session.flush()
        record_audit_log(
            self.session,
            tenant_id=location.tenant_id,
            action="updated",
            entity_type="location",
            entity_id=location.id,
            before=before,
            after=snapshot_orm(location),
        )
        return location

    def delete_location(self, tenant_id: str, location_id: str) -> None:
        location = self.get_location(tenant_id, location_id, include_deleted=True)
        if location is None:
            raise NotFoundError("location_not_found", meta={"location_id": location_id})
        if location.deleted_at is not None:
            return

        before = snapshot_orm(location)
        now = datetime.now(timezone.utc)
        location.is_active = False
        location.deleted_at = now
        location.updated_at = now
        self.session.flush()
        record_audit_log(
            self.session,
            tenant_id=location.tenant_id,
            action="deleted",
            entity_type="location",
            entity_id=location.id,
            before=before,
            after=snapshot_orm(location),
        )
