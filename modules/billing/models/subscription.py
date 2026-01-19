from dataclasses import dataclass
from datetime import datetime, timezone
from core.errors import ValidationError
from modules.billing.models.plans import PlanTier


def _now():
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Subscription:
    tenant_id: str
    tier: PlanTier
    active: bool
    started_at: datetime

    @staticmethod
    def create(*, tenant_id: str, tier: PlanTier, active: bool = True) -> "Subscription":
        if not tenant_id or tenant_id.strip() == "":
            raise ValidationError("tenant_id is required")
        return Subscription(
            tenant_id=tenant_id.strip(),
            tier=tier,
            active=bool(active),
            started_at=_now(),
        )

    def with_tier(self, tier: PlanTier) -> "Subscription":
        return Subscription(
            tenant_id=self.tenant_id,
            tier=tier,
            active=self.active,
            started_at=self.started_at,
        )

    def deactivate(self) -> "Subscription":
        return Subscription(
            tenant_id=self.tenant_id,
            tier=self.tier,
            active=False,
            started_at=self.started_at,
        )
