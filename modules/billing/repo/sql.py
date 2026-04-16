from uuid import UUID

from sqlalchemy import select

from core.db.session import db_session
from modules.billing.models import Subscription
from modules.billing.models.subscription_orm import BillingSubscriptionORM
from modules.billing.repo.billing_repo import BillingRepo


class SqlBillingRepo(BillingRepo):
    def _coerce_uuid(self, value: str):
        try:
            return UUID(value)
        except (TypeError, ValueError):
            return value

    def get_subscription(self, tenant_id: str) -> Subscription | None:
        with db_session() as session:
            stmt = select(BillingSubscriptionORM).where(BillingSubscriptionORM.tenant_id == self._coerce_uuid(tenant_id))
            row = session.execute(stmt).scalar_one_or_none()
            return row.to_domain() if row else None

    def upsert_subscription(self, sub: Subscription) -> None:
        with db_session() as session:
            stmt = select(BillingSubscriptionORM).where(BillingSubscriptionORM.tenant_id == self._coerce_uuid(sub.tenant_id))
            existing = session.execute(stmt).scalar_one_or_none()
            if existing is None:
                session.add(
                    BillingSubscriptionORM(
                        tenant_id=self._coerce_uuid(sub.tenant_id),
                        tier=sub.tier.value,
                        active=sub.active,
                        started_at=sub.started_at,
                    )
                )
                return

            existing.tier = sub.tier.value
            existing.active = sub.active
            existing.started_at = sub.started_at

