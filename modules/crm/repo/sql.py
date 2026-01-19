from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from core.db.session import db_session
from core.errors import ConflictError
from modules.crm.models import Customer, Interaction
from modules.crm.models.customer_orm import CustomerORM
from modules.crm.models.interaction_orm import InteractionORM
from modules.crm.repo.crm_repo import CrmRepo


class SqlCrmRepo(CrmRepo):

    def create_customer(self, customer: Customer) -> None:
        with db_session() as session:
            try:
                session.add(CustomerORM.from_domain(customer))
                session.flush()
            except IntegrityError as exc:
                raise ConflictError(
                    "Customer already exists",
                    meta={"tenant_id": customer.tenant_id, "customer_id": customer.id},
                ) from exc

    def get_customer(self, tenant_id: str, customer_id: str) -> Customer | None:
        with db_session() as session:
            stmt = select(CustomerORM).where(
                CustomerORM.id == customer_id,
                CustomerORM.tenant_id == tenant_id,
            )
            orm = session.execute(stmt).scalar_one_or_none()
            return orm.to_domain() if orm else None

    def find_customer_by_phone(self, tenant_id: str, phone: str) -> Customer | None:
        with db_session() as session:
            stmt = select(CustomerORM).where(
                CustomerORM.phone == phone,
                CustomerORM.tenant_id == tenant_id,
            )
            orm = session.execute(stmt).scalar_one_or_none()
            return orm.to_domain() if orm else None

    def list_customers(self, tenant_id: str) -> list[Customer]:
        with db_session() as session:
            stmt = select(CustomerORM).where(CustomerORM.tenant_id == tenant_id)
            return [c.to_domain() for c in session.scalars(stmt)]

    def update_customer(self, customer: Customer) -> None:
        with db_session() as session:
            session.merge(CustomerORM.from_domain(customer))

    def count_customers(self, tenant_id: str) -> int:
        with db_session() as session:
            stmt = select(func.count()).select_from(CustomerORM).where(
                CustomerORM.tenant_id == tenant_id
            )
            return session.execute(stmt).scalar_one()

    def add_interaction(self, interaction: Interaction) -> None:
        with db_session() as session:
            session.add(InteractionORM.from_domain(interaction))

    def list_interactions(self, tenant_id: str, customer_id: str) -> list[Interaction]:
        with db_session() as session:
            stmt = select(InteractionORM).where(
                InteractionORM.customer_id == customer_id,
                InteractionORM.tenant_id == tenant_id,
            )
            return [i.to_domain() for i in session.scalars(stmt)]
