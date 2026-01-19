from sqlalchemy import select
from core.db.session import db_session
from core.tenancy import get_tenant_id
from modules.crm.models.customer_orm import CustomerORM
from modules.crm.repo.crm_repo import CrmRepo


class SqlCrmRepo(CrmRepo):

    def create_customer(self, *, name: str, phone: str):
        tenant_id = get_tenant_id()

        with db_session() as session:
            customer = CustomerORM(
                tenant_id=tenant_id,
                name=name,
                phone=phone,
            )
            session.add(customer)
            session.flush()
            session.refresh(customer)
            return customer

    def find_customer_by_phone(self, phone: str):
        tenant_id = get_tenant_id()

        with db_session() as session:
            stmt = (
                select(CustomerORM)
                .where(CustomerORM.tenant_id == tenant_id)
                .where(CustomerORM.phone == phone)
            )
            return session.execute(stmt).scalar_one_or_none()
