import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_, select

from core.errors import NotFoundError, ValidationError
from modules.audit.logging import record_audit_log, snapshot_orm
from modules.crm.models.appointment_orm import AppointmentORM
from modules.crm.models.customer_orm import CustomerORM
from modules.crm.models.location_orm import LocationORM
from modules.crm.models.service_orm import ServiceORM


_ALLOWED_APPOINTMENT_STATUSES = {"booked", "completed", "cancelled", "no_show"}
_ALLOWED_APPOINTMENT_SORT_FIELDS = {
    "starts_at": AppointmentORM.starts_at,
    "ends_at": AppointmentORM.ends_at,
    "created_at": AppointmentORM.created_at,
    "status": AppointmentORM.status,
}


class AppointmentOverlapError(Exception):
    def __init__(self, conflicts: list[dict[str, str]]):
        super().__init__("APPOINTMENT_OVERLAP")
        self.conflicts = conflicts


@dataclass
class AppointmentCreate:
    customer_id: uuid.UUID
    location_id: uuid.UUID
    service_id: uuid.UUID | None
    starts_at: datetime
    ends_at: datetime
    status: str = "booked"
    notes: str | None = None
    cancelled_reason: str | None = None
    created_by_user_id: uuid.UUID | None = None
    updated_by_user_id: uuid.UUID | None = None


@dataclass
class CalendarItem:
    id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    status: str
    cancelled_reason: str | None
    notes: str | None
    location_id: uuid.UUID
    customer_id: uuid.UUID
    customer_name: str
    customer_phone: str | None
    service_id: uuid.UUID | None
    service_name: str | None
    service_duration_min: int | None
    service_price_cents: int | None


class AppointmentsRepo:
    def __init__(self, session: Session):
        self.session = session

    def _normalize_status(self, value: str | None) -> str:
        status = (value or "").strip().lower()
        if status not in _ALLOWED_APPOINTMENT_STATUSES:
            raise ValidationError(
                "invalid_appointment_status",
                meta={
                    "allowed_statuses": sorted(_ALLOWED_APPOINTMENT_STATUSES),
                    "received": value,
                },
            )
        return status

    def _normalize_reason(self, value: str | None) -> str | None:
        if value is None:
            return None
        reason = value.strip()
        return reason or None

    def _validate_time_window(self, starts_at: datetime, ends_at: datetime) -> None:
        if starts_at >= ends_at:
            raise ValidationError(
                "invalid_appointment_window",
                meta={"starts_at": starts_at.isoformat(), "ends_at": ends_at.isoformat()},
            )

    def _assert_customer_is_usable(self, tenant_id: uuid.UUID, customer_id: uuid.UUID) -> None:
        stmt = (
            select(CustomerORM.id)
            .where(CustomerORM.tenant_id == tenant_id)
            .where(CustomerORM.id == customer_id)
            .where(CustomerORM.deleted_at.is_(None))
        )
        if self.session.execute(stmt).scalar_one_or_none() is None:
            raise ValidationError("customer_not_found", meta={"customer_id": str(customer_id)})

    def _assert_service_is_usable(
        self,
        tenant_id: uuid.UUID,
        service_id: uuid.UUID | None,
        *,
        require_active: bool = True,
    ) -> None:
        if service_id is None:
            return
        stmt = (
            select(ServiceORM.id)
            .where(ServiceORM.tenant_id == tenant_id)
            .where(ServiceORM.id == service_id)
            .where(ServiceORM.deleted_at.is_(None))
        )
        if require_active:
            stmt = stmt.where(ServiceORM.is_active.is_(True))
        if self.session.execute(stmt).scalar_one_or_none() is None:
            raise ValidationError(
                "service_not_found" if not require_active else "service_not_found_or_inactive",
                meta={"service_id": str(service_id)},
            )

    def _assert_location_is_usable(self, tenant_id: uuid.UUID, location_id: uuid.UUID) -> None:
        stmt = (
            select(LocationORM.allow_overlaps)
            .where(LocationORM.tenant_id == tenant_id)
            .where(LocationORM.id == location_id)
            .where(LocationORM.deleted_at.is_(None))
            .where(LocationORM.is_active.is_(True))
        )
        if self.session.execute(stmt).scalar_one_or_none() is None:
            raise ValidationError("location_not_found", meta={"location_id": str(location_id)})

    def _location_allows_overlaps(self, tenant_id: uuid.UUID, location_id: uuid.UUID) -> bool:
        stmt = (
            select(LocationORM.allow_overlaps)
            .where(LocationORM.tenant_id == tenant_id)
            .where(LocationORM.id == location_id)
            .where(LocationORM.deleted_at.is_(None))
            .where(LocationORM.is_active.is_(True))
        )
        allows = self.session.execute(stmt).scalar_one_or_none()
        if allows is None:
            raise ValidationError("location_not_found", meta={"location_id": str(location_id)})
        return bool(allows)

    def _find_overlaps(
        self,
        *,
        tenant_id: uuid.UUID,
        location_id: uuid.UUID,
        starts_at: datetime,
        ends_at: datetime,
        exclude_appointment_id: uuid.UUID | None = None,
    ) -> list[AppointmentORM]:
        stmt = (
            select(AppointmentORM)
            .where(AppointmentORM.tenant_id == tenant_id)
            .where(AppointmentORM.location_id == location_id)
            .where(AppointmentORM.deleted_at.is_(None))
            .where(AppointmentORM.status != "cancelled")
            .where(AppointmentORM.starts_at < ends_at)
            .where(AppointmentORM.ends_at > starts_at)
            .order_by(AppointmentORM.starts_at.asc())
        )
        if exclude_appointment_id is not None:
            stmt = stmt.where(AppointmentORM.id != exclude_appointment_id)
        return list(self.session.execute(stmt).scalars().all())

    def _assert_overlap_policy(
        self,
        *,
        tenant_id: uuid.UUID,
        location_id: uuid.UUID,
        starts_at: datetime,
        ends_at: datetime,
        status: str,
        exclude_appointment_id: uuid.UUID | None = None,
    ) -> None:
        if status == "cancelled":
            return
        if self._location_allows_overlaps(tenant_id=tenant_id, location_id=location_id):
            return
        conflicts = self._find_overlaps(
            tenant_id=tenant_id,
            location_id=location_id,
            starts_at=starts_at,
            ends_at=ends_at,
            exclude_appointment_id=exclude_appointment_id,
        )
        if not conflicts:
            return
        raise AppointmentOverlapError(
            conflicts=[
                {
                    "id": str(item.id),
                    "starts_at": item.starts_at.isoformat(),
                    "ends_at": item.ends_at.isoformat(),
                }
                for item in conflicts
            ]
        )

    def list(
        self,
        tenant_id: uuid.UUID,
        *,
        page: int = 1,
        page_size: int = 25,
        query: str | None = None,
        status: str | None = None,
        sort: str = "starts_at",
        order: str = "asc",
        from_dt: datetime,
        to_dt: datetime,
        location_id: uuid.UUID | None = None,
        customer_id: uuid.UUID | None = None,
        service_id: uuid.UUID | None = None,
    ) -> tuple[list[AppointmentORM], int]:
        sort_column = _ALLOWED_APPOINTMENT_SORT_FIELDS.get(sort)
        if sort_column is None:
            raise ValidationError(
                "invalid_sort_field",
                meta={"sort": sort, "allowed": sorted(_ALLOWED_APPOINTMENT_SORT_FIELDS.keys())},
            )
        sort_order = order.lower()
        if sort_order not in {"asc", "desc"}:
            raise ValidationError("invalid_sort_order", meta={"order": order, "allowed": ["asc", "desc"]})
        if from_dt >= to_dt:
            raise ValidationError(
                "invalid_appointment_range",
                meta={"from_dt": from_dt.isoformat(), "to_dt": to_dt.isoformat()},
            )
        normalized_status = self._normalize_status(status) if status is not None else None

        customer_name = func.lower(func.coalesce(CustomerORM.name, ""))
        notes_value = func.lower(func.coalesce(AppointmentORM.notes, ""))

        stmt = (
            select(AppointmentORM)
            .join(
                CustomerORM,
                and_(
                    CustomerORM.id == AppointmentORM.customer_id,
                    CustomerORM.tenant_id == tenant_id,
                    CustomerORM.deleted_at.is_(None),
                ),
            )
            .where(AppointmentORM.tenant_id == tenant_id)
            .where(AppointmentORM.deleted_at.is_(None))
        )
        count_stmt = (
            select(func.count())
            .select_from(AppointmentORM)
            .join(
                CustomerORM,
                and_(
                    CustomerORM.id == AppointmentORM.customer_id,
                    CustomerORM.tenant_id == tenant_id,
                    CustomerORM.deleted_at.is_(None),
                ),
            )
            .where(AppointmentORM.tenant_id == tenant_id)
            .where(AppointmentORM.deleted_at.is_(None))
        )

        if query:
            term = f"%{query.strip().lower()}%"
            search_filter = or_(
                customer_name.like(term),
                notes_value.like(term),
            )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        date_filter = and_(AppointmentORM.starts_at >= from_dt, AppointmentORM.starts_at < to_dt)
        stmt = stmt.where(date_filter)
        count_stmt = count_stmt.where(date_filter)

        if normalized_status is not None:
            status_filter = AppointmentORM.status == normalized_status
            stmt = stmt.where(status_filter)
            count_stmt = count_stmt.where(status_filter)

        if location_id is not None:
            location_filter = AppointmentORM.location_id == location_id
            stmt = stmt.where(location_filter)
            count_stmt = count_stmt.where(location_filter)

        if customer_id is not None:
            customer_filter = AppointmentORM.customer_id == customer_id
            stmt = stmt.where(customer_filter)
            count_stmt = count_stmt.where(customer_filter)

        if service_id is not None:
            service_filter = AppointmentORM.service_id == service_id
            stmt = stmt.where(service_filter)
            count_stmt = count_stmt.where(service_filter)

        total = int(self.session.execute(count_stmt).scalar_one())
        offset = (page - 1) * page_size
        if sort_order == "desc":
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())
        stmt = stmt.offset(offset).limit(page_size)

        return list(self.session.execute(stmt).scalars().all()), total

    def list_calendar(
        self,
        tenant_id: uuid.UUID,
        *,
        from_dt: datetime,
        to_dt: datetime,
        location_id: uuid.UUID | None = None,
    ) -> List[CalendarItem]:
        if from_dt >= to_dt:
            raise ValidationError(
                "invalid_appointment_range",
                meta={"from_dt": from_dt.isoformat(), "to_dt": to_dt.isoformat()},
            )

        stmt = (
            select(
                AppointmentORM.id.label("id"),
                AppointmentORM.starts_at.label("starts_at"),
                AppointmentORM.ends_at.label("ends_at"),
                AppointmentORM.status.label("status"),
                AppointmentORM.cancelled_reason.label("cancelled_reason"),
                AppointmentORM.notes.label("notes"),
                AppointmentORM.location_id.label("location_id"),
                CustomerORM.id.label("customer_id"),
                CustomerORM.name.label("customer_name"),
                CustomerORM.phone.label("customer_phone"),
                ServiceORM.id.label("service_id"),
                ServiceORM.name.label("service_name"),
                ServiceORM.duration_minutes.label("service_duration_min"),
                ServiceORM.price_cents.label("service_price_cents"),
            )
            .join(
                CustomerORM,
                and_(
                    CustomerORM.id == AppointmentORM.customer_id,
                    CustomerORM.tenant_id == tenant_id,
                    CustomerORM.deleted_at.is_(None),
                ),
            )
            .outerjoin(
                ServiceORM,
                and_(
                    ServiceORM.id == AppointmentORM.service_id,
                    ServiceORM.tenant_id == tenant_id,
                    ServiceORM.deleted_at.is_(None),
                ),
            )
            .where(AppointmentORM.tenant_id == tenant_id)
            .where(AppointmentORM.deleted_at.is_(None))
            .where(AppointmentORM.starts_at < to_dt)
            .where(AppointmentORM.ends_at > from_dt)
            .order_by(AppointmentORM.starts_at.asc(), AppointmentORM.id.asc())
        )

        if location_id is not None:
            stmt = stmt.where(AppointmentORM.location_id == location_id)

        rows = self.session.execute(stmt).all()
        return [
            CalendarItem(
                id=row.id,
                starts_at=row.starts_at,
                ends_at=row.ends_at,
                status=row.status,
                cancelled_reason=row.cancelled_reason,
                notes=row.notes,
                location_id=row.location_id,
                customer_id=row.customer_id,
                customer_name=row.customer_name,
                customer_phone=row.customer_phone,
                service_id=row.service_id,
                service_name=row.service_name,
                service_duration_min=row.service_duration_min,
                service_price_cents=row.service_price_cents,
            )
            for row in rows
        ]

    def create(self, tenant_id: uuid.UUID, payload: AppointmentCreate) -> AppointmentORM:
        self._assert_customer_is_usable(tenant_id=tenant_id, customer_id=payload.customer_id)
        self._assert_service_is_usable(tenant_id=tenant_id, service_id=payload.service_id, require_active=True)
        self._assert_location_is_usable(tenant_id=tenant_id, location_id=payload.location_id)
        self._validate_time_window(starts_at=payload.starts_at, ends_at=payload.ends_at)
        status = self._normalize_status(payload.status)
        reason = self._normalize_reason(payload.cancelled_reason)
        if status != "cancelled" and reason is not None:
            raise ValidationError("cancelled_reason_only_for_cancelled")
        self._assert_overlap_policy(
            tenant_id=tenant_id,
            location_id=payload.location_id,
            starts_at=payload.starts_at,
            ends_at=payload.ends_at,
            status=status,
        )
        a = AppointmentORM(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            customer_id=payload.customer_id,
            location_id=payload.location_id,
            service_id=payload.service_id,
            starts_at=payload.starts_at,
            ends_at=payload.ends_at,
            status=status,
            cancelled_reason=reason,
            status_updated_at=datetime.now(timezone.utc),
            notes=payload.notes,
            created_by_user_id=payload.created_by_user_id,
            updated_by_user_id=payload.updated_by_user_id or payload.created_by_user_id,
        )
        self.session.add(a)
        self.session.flush()
        record_audit_log(
            self.session,
            tenant_id=a.tenant_id,
            action="created",
            entity_type="appointment",
            entity_id=a.id,
            before=None,
            after=snapshot_orm(a),
        )
        return a

    def update(self, tenant_id: uuid.UUID, appointment_id: uuid.UUID, fields: dict) -> AppointmentORM:
        stmt = (
            select(AppointmentORM)
            .where(AppointmentORM.tenant_id == tenant_id)
            .where(AppointmentORM.id == appointment_id)
            .where(AppointmentORM.deleted_at.is_(None))
        )
        a = self.session.execute(stmt).scalar_one_or_none()
        if a is None:
            raise NotFoundError("appointment_not_found", meta={"appointment_id": str(appointment_id)})
        before = snapshot_orm(a)
        previous_status = a.status

        next_customer_id = fields.get("customer_id", a.customer_id)
        next_location_id = fields.get("location_id", a.location_id)
        next_service_id = fields.get("service_id", a.service_id)
        next_starts_at = fields.get("starts_at", a.starts_at)
        next_ends_at = fields.get("ends_at", a.ends_at)
        next_status = self._normalize_status(fields.get("status", a.status))
        next_reason = self._normalize_reason(fields.get("cancelled_reason", a.cancelled_reason))

        self._assert_customer_is_usable(tenant_id=tenant_id, customer_id=next_customer_id)
        if "service_id" in fields:
            self._assert_service_is_usable(tenant_id=tenant_id, service_id=next_service_id, require_active=True)
        self._assert_location_is_usable(tenant_id=tenant_id, location_id=next_location_id)
        self._validate_time_window(starts_at=next_starts_at, ends_at=next_ends_at)

        if next_status != "cancelled" and next_reason is not None:
            raise ValidationError("cancelled_reason_only_for_cancelled")

        self._assert_overlap_policy(
            tenant_id=tenant_id,
            location_id=next_location_id,
            starts_at=next_starts_at,
            ends_at=next_ends_at,
            status=next_status,
            exclude_appointment_id=a.id,
        )

        if "status" in fields and fields["status"] != a.status:
            fields["status_updated_at"] = datetime.now(timezone.utc)
        fields["status"] = next_status
        fields["cancelled_reason"] = next_reason if next_status == "cancelled" else None

        for key, value in fields.items():
            setattr(a, key, value)
        self.session.flush()
        record_audit_log(
            self.session,
            tenant_id=a.tenant_id,
            action="status_changed" if a.status != previous_status else "updated",
            entity_type="appointment",
            entity_id=a.id,
            before=before,
            after=snapshot_orm(a),
        )
        return a

    def delete(self, tenant_id: uuid.UUID, appointment_id: uuid.UUID) -> None:
        stmt = (
            select(AppointmentORM)
            .where(AppointmentORM.tenant_id == tenant_id)
            .where(AppointmentORM.id == appointment_id)
            .where(AppointmentORM.deleted_at.is_(None))
        )
        appointment = self.session.execute(stmt).scalar_one_or_none()
        if appointment is None:
            raise NotFoundError("appointment_not_found", meta={"appointment_id": str(appointment_id)})

        before = snapshot_orm(appointment)
        appointment.deleted_at = datetime.now(timezone.utc)
        self.session.flush()
        record_audit_log(
            self.session,
            tenant_id=appointment.tenant_id,
            action="deleted",
            entity_type="appointment",
            entity_id=appointment.id,
            before=before,
            after=snapshot_orm(appointment),
        )

    def restore(self, tenant_id: uuid.UUID, appointment_id: uuid.UUID) -> AppointmentORM:
        stmt = (
            select(AppointmentORM)
            .where(AppointmentORM.tenant_id == tenant_id)
            .where(AppointmentORM.id == appointment_id)
            .where(AppointmentORM.deleted_at.is_not(None))
        )
        appointment = self.session.execute(stmt).scalar_one_or_none()
        if appointment is None:
            raise NotFoundError("appointment_not_found", meta={"appointment_id": str(appointment_id)})

        before = snapshot_orm(appointment)
        appointment.deleted_at = None
        self.session.flush()
        record_audit_log(
            self.session,
            tenant_id=appointment.tenant_id,
            action="updated",
            entity_type="appointment",
            entity_id=appointment.id,
            before=before,
            after=snapshot_orm(appointment),
        )
        return appointment
