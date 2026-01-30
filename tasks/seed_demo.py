import os
import uuid

from core.config import load_config, get_config
from core.tenancy import set_tenant_id, clear_tenant_id
from app.container import build_container
from app.auth_tokens import issue_token
from modules.iam.service.auth_service import AuthService
from modules.messaging.models import WhatsAppAccount


def main():
    load_config()
    cfg = get_config()

    container = build_container()

    tenant_id = os.getenv("SEED_TENANT_ID", str(uuid.uuid4()))
    email = os.getenv("SEED_USER_EMAIL", "admin@demo.local")
    password = os.getenv("SEED_USER_PASSWORD", "secret123")
    phone = os.getenv("SEED_CUSTOMER_PHONE", "351111")
    phone_number_id = os.getenv("SEED_WA_PHONE_NUMBER_ID", "pn-123")

    container.tenant_service.create_tenant(tenant_id, name=f"Demo {tenant_id[:6]}")

    set_tenant_id(tenant_id)
    try:
        auth = AuthService(container.users_repo, container.billing)
        user = auth.register(email=email, password=password)
        token = issue_token(secret=cfg.SECRET_KEY, tenant_id=tenant_id, user_id=user.id)

        customer = container.crm.create_customer(name="Demo Customer", phone=phone)

        account = WhatsAppAccount.create(
            account_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            provider="meta",
            phone_number_id=phone_number_id,
        )
        container.messaging_repo.create_whatsapp_account(account)
    finally:
        clear_tenant_id()

    print("Seed completed")
    print(f"Tenant ID: {tenant_id}")
    print(f"User Email: {email}")
    print(f"User Password: {password}")
    print(f"Bearer Token: {token}")
    print(f"Customer ID: {customer.id}")
    print(f"WhatsApp Phone Number ID: {phone_number_id}")


if __name__ == "__main__":
    main()
