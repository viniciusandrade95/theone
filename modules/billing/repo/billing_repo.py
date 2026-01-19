from abc import ABC, abstractmethod
from modules.billing.models import Subscription


class BillingRepo(ABC):
    @abstractmethod
    def get_subscription(self, tenant_id: str) -> Subscription | None: ...

    @abstractmethod
    def upsert_subscription(self, sub: Subscription) -> None: ...
