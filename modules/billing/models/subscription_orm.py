from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from core.db.base import Base
from modules.billing.models.plans import PlanTier
from modules.billing.models.subscription import Subscription


class BillingSubscriptionORM(Base):
    __tablename__ = "billing_subscriptions"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True)
    tier = Column(String, nullable=False)
    active = Column(Boolean, nullable=False, server_default="true")
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    def to_domain(self) -> Subscription:
        try:
            tier = PlanTier(self.tier)
        except Exception:
            tier = PlanTier.STARTER
        return Subscription(
            tenant_id=str(self.tenant_id),
            tier=tier,
            active=bool(self.active),
            started_at=self.started_at,
        )
