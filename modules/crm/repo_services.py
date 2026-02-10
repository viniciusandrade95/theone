import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, select

from core.errors import NotFoundError, ValidationError
from modules.audit.logging import record_audit_log, snapshot_orm
from modules.crm.models.service_orm import ServiceORM


@dataclass
class ServiceCreate:
    name: str
    price_cents: int
    duration_minutes: int
    is_active: bool = True


class ServicesRepo:
    def __init__(self, session: Session):
        self.session = session

    _SORT_FIELDS = {
        "created_at": ServiceORM.created_at,
        "name": ServiceORM.name,
        "price_cents": ServiceORM.price_cents,
        "duration_minutes": ServiceORM.duration_minutes,
    }

    def list(
        self,
        tenant_id: uuid.UUID,
        *,
        page: int = 1,
        page_size: int = 25,
        query: str | None = None,
        include_inactive: bool = False,
        sort: str = "created_at",
        order: str = "desc",
    ) -> tuple[list[ServiceORM], int]:
        sort_column = self._SORT_FIELDS.get(sort)
        if sort_column is None:
            raise ValidationError(
                "invalid_sort_field",
                meta={"sort": sort, "allowed": sorted(self._SORT_FIELDS.keys())},
            )
        sort_order = order.lower()
        if sort_order not in {"asc", "desc"}:
            raise ValidationError("invalid_sort_order", meta={"order": order, "allowed": ["asc", "desc"]})

        stmt = select(ServiceORM).where(ServiceORM.tenant_id == tenant_id)
        count_stmt = (
            select(func.count())
            .select_from(ServiceORM)
            .where(ServiceORM.tenant_id == tenant_id)
        )
        stmt = stmt.where(ServiceORM.deleted_at.is_(None))
        count_stmt = count_stmt.where(ServiceORM.deleted_at.is_(None))
        if not include_inactive:
            stmt = stmt.where(ServiceORM.is_active.is_(True))
            count_stmt = count_stmt.where(ServiceORM.is_active.is_(True))

        if query:
            term = f"%{query.strip().lower()}%"
            search_filter = func.lower(ServiceORM.name).like(term)
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        if sort_order == "desc":
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())

        total = int(self.session.execute(count_stmt).scalar_one())
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        return list(self.session.execute(stmt).scalars().all()), total

    def create(self, tenant_id: uuid.UUID, payload: ServiceCreate) -> ServiceORM:
        s = ServiceORM(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            name=payload.name,
            price_cents=payload.price_cents,
            duration_minutes=payload.duration_minutes,
            is_active=payload.is_active,
        )
        self.session.add(s)
        self.session.flush()
        record_audit_log(
            self.session,
            tenant_id=s.tenant_id,
            action="created",
            entity_type="service",
            entity_id=s.id,
            before=None,
            after=snapshot_orm(s),
        )
        return s

    def update(self, tenant_id: uuid.UUID, service_id: uuid.UUID, fields: dict) -> ServiceORM:
        stmt = (
            select(ServiceORM)
            .where(ServiceORM.tenant_id == tenant_id)
            .where(ServiceORM.id == service_id)
            .where(ServiceORM.deleted_at.is_(None))
        )
        s = self.session.execute(stmt).scalar_one_or_none()
        if s is None:
            raise NotFoundError("service_not_found", meta={"service_id": str(service_id)})
        before = snapshot_orm(s)
        for key, value in fields.items():
            setattr(s, key, value)
        self.session.flush()
        record_audit_log(
            self.session,
            tenant_id=s.tenant_id,
            action="updated",
            entity_type="service",
            entity_id=s.id,
            before=before,
            after=snapshot_orm(s),
        )
        return s

    def delete(self, tenant_id: uuid.UUID, service_id: uuid.UUID) -> None:
        stmt = (
            select(ServiceORM)
            .where(ServiceORM.tenant_id == tenant_id)
            .where(ServiceORM.id == service_id)
            .where(ServiceORM.deleted_at.is_(None))
        )
        service = self.session.execute(stmt).scalar_one_or_none()
        if service is None:
            raise NotFoundError("service_not_found", meta={"service_id": str(service_id)})

        before = snapshot_orm(service)
        service.deleted_at = datetime.now(timezone.utc)
        service.is_active = False
        self.session.flush()
        record_audit_log(
            self.session,
            tenant_id=service.tenant_id,
            action="deleted",
            entity_type="service",
            entity_id=service.id,
            before=before,
            after=snapshot_orm(service),
        )

    def restore(self, tenant_id: uuid.UUID, service_id: uuid.UUID) -> ServiceORM:
        stmt = (
            select(ServiceORM)
            .where(ServiceORM.tenant_id == tenant_id)
            .where(ServiceORM.id == service_id)
            .where(ServiceORM.deleted_at.is_not(None))
        )
        service = self.session.execute(stmt).scalar_one_or_none()
        if service is None:
            raise NotFoundError("service_not_found", meta={"service_id": str(service_id)})

        before = snapshot_orm(service)
        service.deleted_at = None
        service.is_active = True
        self.session.flush()
        record_audit_log(
            self.session,
            tenant_id=service.tenant_id,
            action="updated",
            entity_type="service",
            entity_id=service.id,
            before=before,
            after=snapshot_orm(service),
        )
        return service
