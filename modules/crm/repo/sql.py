from uuid import UUID
from typing import List

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from core.db.session import db_session
from core.tenancy import get_tenant_id

from modules.crm.repo.crm_repo import CrmRepo
from modules.crm.models.customer_orm import CustomerORM
from modules.crm.models.interaction_orm import InteractionORM
from modules.crm.models.customer import Customer
from modules.crm.models.pipeline import PipelineStage


class SqlCrmRepo(CrmRepo):

    # -------------------
    # Customers
    # -------------------

    def create_customer(
        self,
        *,
        customer: Customer,
    ) -> Customer:

        tenant_id = get_tenant_id()

        with db_session() as session:
            orm = CustomerORM(
                id=UUID(customer.id),
                tenant_id=UUID(tenant_id),
                name=customer.name,
                phone=customer.phone,
                email=customer.email,
                tags=list(customer.tags),
                consent_marketing=customer.consent_marketing,
                stage=customer.stage.value,
            )
            session.add(orm)
            session.flush()
            return customer

    def get_customer(self, customer_id: str) -> Customer | None:
        tenant_id = get_tenant_id()

        with db_session() as session:
            stmt = (
                select(CustomerORM)
                .where(CustomerORM.id == UUID(customer_id))
                .where(CustomerORM.tenant_id == UUID(tenant_id))
            )

            orm = session.execute(stmt).scalar_one_or_none()
            if not orm:
                return None

            return self._to_domain(orm)

    def find_by_phone(self, phone: str) -> Customer | None:
        tenant_id = get_tenant_id()

        with db_session() as session:
            stmt = (
                select(CustomerORM)
                .where(CustomerORM.tenant_id == UUID(tenant_id))
                .where(CustomerORM.phone == phone)
            )
            orm = session.execute(stmt).scalar_one_or_none()
            return self._to_domain(orm) if orm else None

    def list_customers(self) -> List[Customer]:
        tenant_id = get_tenant_id()

        with db_session() as session:
            stmt = select(CustomerORM).where(CustomerORM.tenant_id == UUID(tenant_id))
            rows = session.execute(stmt).scalars().all()
            return [self._to_domain(r) for r in rows]

    def count_customers(self) -> int:
        tenant_id = get_tenant_id()

        with db_session() as session:
            stmt = (
                select(func.count())
                .select_from(CustomerORM)
                .where(CustomerORM.tenant_id == UUID(tenant_id))
            )
            return session.execute(stmt).scalar_one()

    def update_customer(self, customer: Customer) -> None:
        tenant_id = get_tenant_id()

        with db_session() as session:
            stmt = (
                select(CustomerORM)
                .where(CustomerORM.id == UUID(customer.id))
                .where(CustomerORM.tenant_id == UUID(tenant_id))
            )
            orm = session.execute(stmt).scalar_one()

            orm.name = customer.name
            orm.phone = customer.phone
            orm.email = customer.email
            orm.tags = list(customer.tags)
            orm.stage = customer.stage.value
            orm.consent_marketing = customer.consent_marketing

    # -------------------
    # Interactions
    # -------------------

    def add_interaction(self, *, customer_id: str, interaction_type: str, payload: dict) -> None:
        tenant_id = get_tenant_id()

        with db_session() as session:
            orm = InteractionORM(
                tenant_id=UUID(tenant_id),
                customer_id=UUID(customer_id),
                type=interaction_type,
                payload=payload,
            )
            session.add(orm)

    def list_interactions(self, customer_id: str):
        tenant_id = get_tenant_id()

        with db_session() as session:
            stmt = (
                select(InteractionORM)
                .where(InteractionORM.tenant_id == UUID(tenant_id))
                .where(InteractionORM.customer_id == UUID(customer_id))
                .order_by(InteractionORM.created_at.desc())
            )
            return session.execute(stmt).scalars().all()

    # -------------------
    # Helpers
    # -------------------

    def _to_domain(self, orm: CustomerORM) -> Customer:
        return Customer(
            id=str(orm.id),
            tenant_id=str(orm.tenant_id),
            name=orm.name,
            phone=orm.phone,
            email=orm.email,
            tags=frozenset(orm.tags or []),
            consent_marketing=orm.consent_marketing,
            stage=PipelineStage(orm.stage),
            created_at=orm.created_at,
        )
