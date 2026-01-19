from sqlalchemy import select
from core.db.session import db_session
from core.tenancy import get_tenant_id
from modules.crm.models.customer_orm import CustomerORM
from modules.crm.repo.crm_repo import CrmRepo


class SqlCrmRepo(CrmRepo):

    def create_customer(self, *, name: str, phone: str):
        tenant_id = get_tenant_id()

        with db_session() as session:
            customer = CustomerORM(
                tenant_id=tenant_id,
                name=name,
                phone=phone,
            )
            session.add(customer)
            session.flush()
            session.refresh(customer)
            return customer

    def get_customer(self, customer_id: str) -> Customer | None:
        tenant_id = get_tenant_id()

        with db_session() as session:
            stmt = select(CustomerORM).where(
                CustomerORM.id == customer_id,
                CustomerORM.tenant_id == tenant_id,
            )
            orm = session.execute(stmt).scalar_one_or_none()
            return orm.to_domain() if orm else None

    def find_by_phone(self, phone: str) -> Customer | None:
        tenant_id = get_tenant_id()

        with db_session() as session:
            stmt = select(CustomerORM).where(
                CustomerORM.phone == phone,
                CustomerORM.tenant_id == tenant_id,
            )
            orm = session.execute(stmt).scalar_one_or_none()
            return orm.to_domain() if orm else None

    def list_customers(self) -> list[Customer]:
        tenant_id = get_tenant_id()

        with db_session() as session:
            stmt = select(CustomerORM).where(CustomerORM.tenant_id == tenant_id)
            return [c.to_domain() for c in session.scalars(stmt)]

    def update_customer(self, customer: Customer) -> None:
        with db_session() as session:
            session.merge(CustomerORM.from_domain(customer))

    def count_customers(self) -> int:
        tenant_id = get_tenant_id()

        with db_session() as session:
            stmt = select(func.count()).select_from(CustomerORM).where(
                CustomerORM.tenant_id == tenant_id
            )
            return session.execute(stmt).scalar_one()

    def add_interaction(self, interaction: Interaction) -> None:
        with db_session() as session:
            session.add(InteractionORM.from_domain(interaction))

    def list_interactions(self, customer_id: str) -> list[Interaction]:
        tenant_id = get_tenant_id()

        with db_session() as session:
            stmt = select(InteractionORM).where(
                InteractionORM.customer_id == customer_id,
                InteractionORM.tenant_id == tenant_id,
            )
            return [i.to_domain() for i in session.scalars(stmt)]
