from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from sqlalchemy import text

from core.tenancy import get_tenant_id

from core.config import get_config
from core.db.base import Base

_engine = None
_SessionLocal = None


def _initialize_schema(engine) -> None:
    from modules.tenants.models.tenant_orm import TenantORM  # noqa: F401
    from modules.crm.models.customer_orm import CustomerORM  # noqa: F401
    from modules.crm.models.interaction_orm import InteractionORM  # noqa: F401
    from modules.iam.models.user_orm import UserORM  # noqa: F401
    from modules.messaging.models.whatsapp_account_orm import WhatsAppAccountORM  # noqa: F401
    from modules.messaging.models.webhook_event_orm import WebhookEventORM  # noqa: F401
    from modules.messaging.models.conversation_orm import ConversationORM  # noqa: F401
    from modules.messaging.models.message_orm import MessageORM  # noqa: F401

    Base.metadata.create_all(engine)


def _get_engine():
    global _engine, _SessionLocal

    if _engine is None:
        cfg = get_config()
        database_url = cfg.DATABASE_URL
        if database_url == "dev":
            database_url = "sqlite+pysqlite:///:memory:"
        _engine = create_engine(
            database_url,
            pool_pre_ping=True,
        )
        _SessionLocal = sessionmaker(bind=_engine)
        if cfg.ENV == "test" or cfg.DATABASE_URL == "dev":
            _initialize_schema(_engine)

    return _engine


@contextmanager
def db_session():
    if _SessionLocal is None:
        _get_engine()

    session = _SessionLocal()
    tenant_id = get_tenant_id()
    if tenant_id:
        try:
            if session.bind and session.bind.dialect.name == "postgresql":
                session.execute(text("SET LOCAL app.current_tenant_id = :tenant_id"), {"tenant_id": tenant_id})
        except Exception:
            session.rollback()
            session.close()
            raise
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
