import uuid
from dataclasses import dataclass
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, and_

from modules.crm.models.appointment_orm import AppointmentORM


@dataclass
class AppointmentCreate:
    customer_id: uuid.UUID
    service_id: uuid.UUID | None
    starts_at: datetime
    ends_at: datetime
    status: str = "booked"
    notes: str | None = None


class AppointmentsRepo:
    def __init__(self, session: Session):
        self.session = session

    def list(self, from_dt: datetime | None = None, to_dt: datetime | None = None) -> list[AppointmentORM]:
        stmt = select(AppointmentORM).order_by(AppointmentORM.starts_at.asc())

        if from_dt and to_dt:
            stmt = stmt.where(and_(AppointmentORM.starts_at >= from_dt, AppointmentORM.starts_at < to_dt))
        elif from_dt:
            stmt = stmt.where(AppointmentORM.starts_at >= from_dt)
        elif to_dt:
            stmt = stmt.where(AppointmentORM.starts_at < to_dt)

        return list(self.session.execute(stmt).scalars().all())

    def create(self, tenant_id: uuid.UUID, payload: AppointmentCreate) -> AppointmentORM:
        a = AppointmentORM(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            customer_id=payload.customer_id,
            service_id=payload.service_id,
            starts_at=payload.starts_at,
            ends_at=payload.ends_at,
            status=payload.status,
            notes=payload.notes,
        )
        self.session.add(a)
        self.session.flush()
        return a

    def update(self, appointment_id: uuid.UUID, fields: dict) -> AppointmentORM:
        self.session.execute(
            update(AppointmentORM)
            .where(AppointmentORM.id == appointment_id)
            .values(**fields)
        )
        a = self.session.get(AppointmentORM, appointment_id)
        if not a:
            raise ValueError("appointment_not_found")
        return a

    def delete(self, appointment_id: uuid.UUID) -> None:
        self.session.execute(delete(AppointmentORM).where(AppointmentORM.id == appointment_id))
