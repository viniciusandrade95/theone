import uuid
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete

from modules.crm.models.service_orm import ServiceORM


@dataclass
class ServiceCreate:
    name: str
    price_cents: int
    duration_minutes: int


class ServicesRepo:
    def __init__(self, session: Session):
        self.session = session

    def list(self) -> list[ServiceORM]:
        stmt = select(ServiceORM).order_by(ServiceORM.created_at.desc())
        return list(self.session.execute(stmt).scalars().all())

    def create(self, tenant_id: uuid.UUID, payload: ServiceCreate) -> ServiceORM:
        s = ServiceORM(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            name=payload.name,
            price_cents=payload.price_cents,
            duration_minutes=payload.duration_minutes,
        )
        self.session.add(s)
        self.session.flush()
        return s

    def update(self, service_id: uuid.UUID, fields: dict) -> ServiceORM:
        self.session.execute(
            update(ServiceORM)
            .where(ServiceORM.id == service_id)
            .values(**fields)
        )
        s = self.session.get(ServiceORM, service_id)
        if not s:
            raise ValueError("service_not_found")
        return s

    def delete(self, service_id: uuid.UUID) -> None:
        self.session.execute(delete(ServiceORM).where(ServiceORM.id == service_id))
