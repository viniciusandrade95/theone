from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from contextlib import contextmanager
from sqlalchemy import text
from sqlalchemy.pool import StaticPool
from contextvars import ContextVar

from core.tenancy import get_tenant_id

from core.config import get_config
from core.db.base import Base

_engine = None
_SessionLocal = None
_engine_url: str | None = None
_schema_ready = False
_current_session: ContextVar[Session | None] = ContextVar("db_session", default=None)


def reset_engine_state() -> None:
    global _engine, _SessionLocal, _engine_url, _schema_ready
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
    _engine_url = None
    _schema_ready = False


def _initialize_schema(engine) -> None:
    from modules.tenants.models.tenant_orm import TenantORM  # noqa: F401
    from modules.tenants.models.tenant_settings_orm import TenantSettingsORM  # noqa: F401
    from modules.crm.models.customer_orm import CustomerORM  # noqa: F401
    from modules.crm.models.interaction_orm import InteractionORM  # noqa: F401
    from modules.crm.models.location_orm import LocationORM  # noqa: F401
    from modules.crm.models.service_orm import ServiceORM  # noqa: F401
    from modules.crm.models.appointment_orm import AppointmentORM  # noqa: F401
    from modules.iam.models.user_orm import UserORM  # noqa: F401
    from modules.messaging.models.whatsapp_account_orm import WhatsAppAccountORM  # noqa: F401
    from modules.messaging.models.webhook_event_orm import WebhookEventORM  # noqa: F401
    from modules.messaging.models.conversation_orm import ConversationORM  # noqa: F401
    from modules.messaging.models.message_orm import MessageORM  # noqa: F401
    from modules.audit.models.audit_log_orm import AuditLogORM  # noqa: F401

    Base.metadata.create_all(engine)


def _get_engine():
    global _engine, _SessionLocal, _engine_url, _schema_ready

    cfg = get_config()
    database_url = cfg.DATABASE_URL
    if database_url == "dev":
        database_url = "sqlite+pysqlite:///:memory:"

    if _engine is None or _engine_url != database_url:
        engine_kwargs = {"pool_pre_ping": True}
        if database_url.startswith("sqlite"):
            engine_kwargs["connect_args"] = {"check_same_thread": False}
            if ":memory:" in database_url:
                engine_kwargs["poolclass"] = StaticPool
        _engine = create_engine(database_url, **engine_kwargs)
        _SessionLocal = sessionmaker(bind=_engine)
        _engine_url = database_url
        _schema_ready = False

    if cfg.DATABASE_URL == "dev" and not _schema_ready:
        _initialize_schema(_engine)
        _schema_ready = True

    return _engine


@contextmanager
def db_session():
    if _SessionLocal is None:
        _get_engine()

    existing_session = _current_session.get()
    if existing_session is not None:
        yield existing_session
        return

    session = _SessionLocal()
    token = _current_session.set(session)
    tenant_id = get_tenant_id()
    if tenant_id:
        try:
            if session.bind and session.bind.dialect.name == "postgresql":
                #session.execute(text("SET LOCAL app.current_tenant_id = :tenant_id"), {"tenant_id": tenant_id})
                session.execute(text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_id)})
        except Exception:
            session.rollback()
            session.close()
            _current_session.reset(token)
            raise
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        _current_session.reset(token)
