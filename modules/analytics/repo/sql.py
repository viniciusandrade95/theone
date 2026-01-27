from datetime import datetime
from uuid import UUID

from sqlalchemy import select

from core.db.session import db_session
from modules.analytics.repo.analytics_repo import AnalyticsRepo
from modules.crm.models import Customer, Interaction
from modules.crm.models.customer_orm import CustomerORM
from modules.crm.models.interaction_orm import InteractionORM


class SqlAnalyticsRepo(AnalyticsRepo):
    def _coerce_uuid(self, value: str):
        try:
            return UUID(value)
        except (TypeError, ValueError):
            return value

    def list_customers(self, tenant_id: str) -> list[Customer]:
        with db_session() as session:
            stmt = select(CustomerORM).where(CustomerORM.tenant_id == self._coerce_uuid(tenant_id))
            return [c.to_domain() for c in session.scalars(stmt)]

    def list_interactions(self, tenant_id: str) -> list[Interaction]:
        with db_session() as session:
            stmt = select(InteractionORM).where(InteractionORM.tenant_id == self._coerce_uuid(tenant_id))
            return [i.to_domain() for i in session.scalars(stmt)]

    def list_customers_created_between(
        self, tenant_id: str, start: datetime, end: datetime
    ) -> list[Customer]:
        with db_session() as session:
            stmt = select(CustomerORM).where(
                CustomerORM.tenant_id == self._coerce_uuid(tenant_id),
                CustomerORM.created_at >= start,
                CustomerORM.created_at <= end,
            )
            return [c.to_domain() for c in session.scalars(stmt)]
