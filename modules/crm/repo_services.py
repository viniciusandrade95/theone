import uuid
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import delete, func, select

from core.errors import NotFoundError, ValidationError
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
        return s

    def update(self, tenant_id: uuid.UUID, service_id: uuid.UUID, fields: dict) -> ServiceORM:
        stmt = (
            select(ServiceORM)
            .where(ServiceORM.tenant_id == tenant_id)
            .where(ServiceORM.id == service_id)
        )
        s = self.session.execute(stmt).scalar_one_or_none()
        if s is None:
            raise NotFoundError("service_not_found", meta={"service_id": str(service_id)})
        for key, value in fields.items():
            setattr(s, key, value)
        self.session.flush()
        return s

    def delete(self, tenant_id: uuid.UUID, service_id: uuid.UUID) -> None:
        result = self.session.execute(
            delete(ServiceORM)
            .where(ServiceORM.tenant_id == tenant_id)
            .where(ServiceORM.id == service_id)
        )
        if result.rowcount == 0:
            raise NotFoundError("service_not_found", meta={"service_id": str(service_id)})
