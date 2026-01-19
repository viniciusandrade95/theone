from core.errors import ConflictError
from modules.crm.models import Customer, Interaction
from modules.crm.repo.crm_repo import CrmRepo


class InMemoryCrmRepo(CrmRepo):
    def __init__(self):
        # customers: key (tenant_id, customer_id)
        self._customers: dict[tuple[str, str], Customer] = {}
        # interactions: key (tenant_id, customer_id) -> list
        self._interactions: dict[tuple[str, str], list[Interaction]] = {}

    def create_customer(self, customer: Customer) -> None:
        key = (customer.tenant_id, customer.id)
        if key in self._customers:
            raise ConflictError("Customer already exists", meta={"tenant_id": customer.tenant_id, "customer_id": customer.id})
        self._customers[key] = customer

    def get_customer(self, tenant_id: str, customer_id: str) -> Customer | None:
        return self._customers.get((tenant_id, customer_id))

    def update_customer(self, customer: Customer) -> None:
        key = (customer.tenant_id, customer.id)
        self._customers[key] = customer

    def list_customers(self, tenant_id: str) -> list[Customer]:
        return [c for (t, _), c in self._customers.items() if t == tenant_id]

    def add_interaction(self, interaction: Interaction) -> None:
        key = (interaction.tenant_id, interaction.customer_id)
        self._interactions.setdefault(key, []).append(interaction)

    def list_interactions(self, tenant_id: str, customer_id: str) -> list[Interaction]:
        return list(self._interactions.get((tenant_id, customer_id), []))


###################### messaging

    def find_customer_by_phone(self, tenant_id: str, phone: str) -> Customer | None:
        phone_norm = phone.strip()
        for (t, _), c in self._customers.items():
            if t == tenant_id and c.phone == phone_norm:
                return c
        return None

#################### tiers
    def count_customers(self, tenant_id: str) -> int:
        return sum(1 for (t, _), _c in self._customers.items() if t == tenant_id)
