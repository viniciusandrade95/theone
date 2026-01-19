from modules.billing.models import Subscription
from modules.billing.repo.billing_repo import BillingRepo


class InMemoryBillingRepo(BillingRepo):
    def __init__(self):
        self._subs: dict[str, Subscription] = {}

    def get_subscription(self, tenant_id: str) -> Subscription | None:
        return self._subs.get(tenant_id)

    def upsert_subscription(self, sub: Subscription) -> None:
        self._subs[sub.tenant_id] = sub
