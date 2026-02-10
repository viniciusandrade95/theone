from core.errors import ConflictError
from modules.crm.models import Customer, Interaction
from modules.crm.repo.crm_repo import CrmRepo


class InMemoryCrmRepo(CrmRepo):
    def __init__(self):
        # customers: key (tenant_id, customer_id)
        self._customers: dict[tuple[str, str], Customer] = {}
        # interactions: key (tenant_id, customer_id) -> list
        self._interactions: dict[tuple[str, str], list[Interaction]] = {}
        # deleted customers tracked for soft-delete semantics
        self._deleted_customers: set[tuple[str, str]] = set()

    def create_customer(self, customer: Customer) -> None:
        key = (customer.tenant_id, customer.id)
        if key in self._customers:
            raise ConflictError("Customer already exists", meta={"tenant_id": customer.tenant_id, "customer_id": customer.id})
        self._customers[key] = customer
        self._deleted_customers.discard(key)

    def get_customer(self, tenant_id: str, customer_id: str) -> Customer | None:
        key = (tenant_id, customer_id)
        if key in self._deleted_customers:
            return None
        return self._customers.get(key)

    def update_customer(self, customer: Customer) -> None:
        key = (customer.tenant_id, customer.id)
        self._customers[key] = customer

    def list_customers(
        self,
        tenant_id: str,
        *,
        page: int = 1,
        page_size: int = 25,
        query: str | None = None,
        stage: str | None = None,
        sort: str = "created_at",
        order: str = "desc",
    ) -> list[Customer]:
        rows = [
            c
            for key, c in self._customers.items()
            if key[0] == tenant_id and key not in self._deleted_customers
        ]
        if query:
            term = query.strip().lower()
            rows = [
                c
                for c in rows
                if term in c.name.lower()
                or (c.email and term in c.email.lower())
                or (c.phone and term in c.phone.lower())
            ]
        if stage:
            rows = [c for c in rows if c.stage.value == stage]
        if sort == "name":
            rows.sort(key=lambda c: c.name.lower(), reverse=(order.lower() == "desc"))
        elif sort == "email":
            rows.sort(key=lambda c: (c.email or "").lower(), reverse=(order.lower() == "desc"))
        elif sort == "phone":
            rows.sort(key=lambda c: (c.phone or "").lower(), reverse=(order.lower() == "desc"))
        else:
            rows.sort(key=lambda c: c.created_at, reverse=(order.lower() == "desc"))
        start = (page - 1) * page_size
        end = start + page_size
        return rows[start:end]

    def add_interaction(self, interaction: Interaction) -> None:
        key = (interaction.tenant_id, interaction.customer_id)
        self._interactions.setdefault(key, []).append(interaction)

    def list_interactions(
        self,
        tenant_id: str,
        customer_id: str,
        *,
        page: int = 1,
        page_size: int = 25,
        query: str | None = None,
        sort: str = "created_at",
        order: str = "desc",
    ) -> list[Interaction]:
        rows = list(self._interactions.get((tenant_id, customer_id), []))
        if query:
            term = query.strip().lower()
            rows = [
                i
                for i in rows
                if term in i.type.lower() or term in i.content.lower()
            ]
        if sort == "type":
            rows.sort(key=lambda i: i.type.lower(), reverse=(order.lower() == "desc"))
        else:
            rows.sort(key=lambda i: i.created_at, reverse=(order.lower() == "desc"))
        start = (page - 1) * page_size
        end = start + page_size
        return rows[start:end]


###################### messaging

    def find_customer_by_phone(self, tenant_id: str, phone: str) -> Customer | None:
        phone_norm = phone.strip()
        for key, c in self._customers.items():
            if key in self._deleted_customers:
                continue
            t = key[0]
            if t == tenant_id and c.phone == phone_norm:
                return c
        return None

#################### tiers
    def count_customers(self, tenant_id: str, *, query: str | None = None, stage: str | None = None) -> int:
        rows = [
            c
            for key, c in self._customers.items()
            if key[0] == tenant_id and key not in self._deleted_customers
        ]
        if query:
            term = query.strip().lower()
            rows = [
                c
                for c in rows
                if term in c.name.lower()
                or (c.email and term in c.email.lower())
                or (c.phone and term in c.phone.lower())
            ]
        if stage:
            rows = [c for c in rows if c.stage.value == stage]
        return len(rows)

    def count_interactions(self, tenant_id: str, customer_id: str, *, query: str | None = None) -> int:
        rows = list(self._interactions.get((tenant_id, customer_id), []))
        if query:
            term = query.strip().lower()
            rows = [i for i in rows if term in i.type.lower() or term in i.content.lower()]
        return len(rows)

    def delete_customer(self, tenant_id: str, customer_id: str) -> None:
        key = (tenant_id, customer_id)
        if key in self._customers:
            self._deleted_customers.add(key)

    def restore_customer(self, tenant_id: str, customer_id: str) -> None:
        key = (tenant_id, customer_id)
        if key in self._customers:
            self._deleted_customers.discard(key)
