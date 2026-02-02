from uuid import UUID

from sqlalchemy import select, func, or_
from core.db.session import db_session
from modules.crm.repo.crm_repo import CrmRepo
from modules.crm.models.customer_orm import CustomerORM
from modules.crm.models.interaction_orm import InteractionORM
from modules.crm.models.customer import Customer
from modules.crm.models.interaction import Interaction


class SqlCrmRepo(CrmRepo):
    def _coerce_uuid(self, value: str):
        try:
            return UUID(value)
        except (TypeError, ValueError):
            return value

    # -------------------
    # Customers
    # -------------------

    def create_customer(self, customer: Customer) -> None:
        with db_session() as session:
            orm = CustomerORM(
                id=self._coerce_uuid(customer.id),
                tenant_id=self._coerce_uuid(customer.tenant_id),
                name=customer.name,
                phone=customer.phone,
                email=customer.email,
                tags=list(customer.tags),
                consent_marketing=customer.consent_marketing,
                stage=customer.stage.value,
            )
            session.add(orm)
            session.flush()

    def get_customer(self, tenant_id: str, customer_id: str) -> Customer | None:
        with db_session() as session:
            stmt = (
                select(CustomerORM)
                .where(CustomerORM.id == self._coerce_uuid(customer_id))
                .where(CustomerORM.tenant_id == self._coerce_uuid(tenant_id))
            )

            orm = session.execute(stmt).scalar_one_or_none()
            if not orm:
                return None

            return self._to_domain(orm)

    def find_customer_by_phone(self, tenant_id: str, phone: str) -> Customer | None:
        with db_session() as session:
            stmt = (
                select(CustomerORM)
                .where(CustomerORM.tenant_id == self._coerce_uuid(tenant_id))
                .where(CustomerORM.phone == phone)
            )
            orm = session.execute(stmt).scalar_one_or_none()
            return self._to_domain(orm) if orm else None

    def list_customers(
        self,
        tenant_id: str,
        *,
        limit: int | None = None,
        offset: int | None = None,
        search: str | None = None,
    ) -> list[Customer]:
        with db_session() as session:
            stmt = select(CustomerORM).where(CustomerORM.tenant_id == self._coerce_uuid(tenant_id))
            if search:
                term = f"%{search.strip().lower()}%"
                stmt = stmt.where(
                    or_(
                        func.lower(CustomerORM.name).like(term),
                        func.lower(CustomerORM.email).like(term),
                        func.lower(CustomerORM.phone).like(term),
                    )
                )
            stmt = stmt.order_by(CustomerORM.created_at.desc())
            if offset:
                stmt = stmt.offset(offset)
            if limit:
                stmt = stmt.limit(limit)
            rows = session.execute(stmt).scalars().all()
            return [self._to_domain(r) for r in rows]

    def count_customers(self, tenant_id: str, *, search: str | None = None) -> int:
        with db_session() as session:
            stmt = (
                select(func.count())
                .select_from(CustomerORM)
                .where(CustomerORM.tenant_id == self._coerce_uuid(tenant_id))
            )
            if search:
                term = f"%{search.strip().lower()}%"
                stmt = stmt.where(
                    or_(
                        func.lower(CustomerORM.name).like(term),
                        func.lower(CustomerORM.email).like(term),
                        func.lower(CustomerORM.phone).like(term),
                    )
                )
            return session.execute(stmt).scalar_one()

    def update_customer(self, customer: Customer) -> None:
        with db_session() as session:
            stmt = (
                select(CustomerORM)
                .where(CustomerORM.id == self._coerce_uuid(customer.id))
                .where(CustomerORM.tenant_id == self._coerce_uuid(customer.tenant_id))
            )
            orm = session.execute(stmt).scalar_one()

            orm.name = customer.name
            orm.phone = customer.phone
            orm.email = customer.email
            orm.tags = list(customer.tags)
            orm.stage = customer.stage.value
            orm.consent_marketing = customer.consent_marketing

    def delete_customer(self, tenant_id: str, customer_id: str) -> None:
        with db_session() as session:
            stmt = (
                select(CustomerORM)
                .where(CustomerORM.id == self._coerce_uuid(customer_id))
                .where(CustomerORM.tenant_id == self._coerce_uuid(tenant_id))
            )
            orm = session.execute(stmt).scalar_one_or_none()
            if orm:
                session.delete(orm)

    # -------------------
    # Interactions
    # -------------------

    def add_interaction(self, interaction: Interaction) -> None:
        with db_session() as session:
            orm = InteractionORM(
                id=self._coerce_uuid(interaction.id),
                tenant_id=self._coerce_uuid(interaction.tenant_id),
                customer_id=self._coerce_uuid(interaction.customer_id),
                type=interaction.type,
                payload={"content": interaction.content},
            )
            session.add(orm)

    def list_interactions(self, tenant_id: str, customer_id: str) -> list[Interaction]:
        with db_session() as session:
            stmt = (
                select(InteractionORM)
                .where(InteractionORM.tenant_id == self._coerce_uuid(tenant_id))
                .where(InteractionORM.customer_id == self._coerce_uuid(customer_id))
                .order_by(InteractionORM.created_at.desc())
            )
            rows = session.execute(stmt).scalars().all()
            return [i.to_domain() for i in rows]

    # -------------------
    # Helpers
    # -------------------

    def _to_domain(self, orm: CustomerORM) -> Customer:
        return orm.to_domain()
