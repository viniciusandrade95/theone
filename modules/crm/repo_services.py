import uuid
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete

from core.db.models import Service  # we’ll create this model in Step 2.3


@dataclass
class ServiceCreate:
    name: str
    price_cents: int
    duration_minutes: int


class ServicesRepo:
    def __init__(self, session: Session):
        self.session = session

    def list(self) -> list[Service]:
        return list(self.session.execute(select(Service).order_by(Service.created_at.desc())).scalars().all())

    def create(self, tenant_id, payload: ServiceCreate) -> Service:
        s = Service(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            name=payload.name,
            price_cents=payload.price_cents,
            duration_minutes=payload.duration_minutes,
        )
        self.session.add(s)
        self.session.flush()
        return s

    def update(self, service_id, fields: dict) -> Service:
        self.session.execute(
            update(Service).where(Service.id == service_id).values(**fields)
        )
        s = self.session.get(Service, service_id)
        if not s:
            raise ValueError("service_not_found")
        return s

    def delete(self, service_id) -> None:
        self.session.execute(delete(Service).where(Service.id == service_id))
