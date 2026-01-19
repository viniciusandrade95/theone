from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

from core.config import get_config
from core.db.base import Base

_engine = None
_SessionLocal = None


def _initialize_schema(engine) -> None:
    from modules.tenants.models.tenant_orm import TenantORM  # noqa: F401
    from modules.crm.models.customer_orm import CustomerORM  # noqa: F401
    from modules.crm.models.interaction_orm import InteractionORM  # noqa: F401

    Base.metadata.create_all(engine)


def _get_engine():
    global _engine, _SessionLocal

    if _engine is None:
        cfg = get_config()
        database_url = cfg.DATABASE_URL
        if database_url == "dev":
            database_url = "sqlite+pysqlite:///:memory:"
        engine_kwargs: dict[str, object] = {"pool_pre_ping": True}
        if database_url == "sqlite+pysqlite:///:memory:":
            engine_kwargs.update(
                {
                    "connect_args": {"check_same_thread": False},
                    "poolclass": StaticPool,
                }
            )
        _engine = create_engine(database_url, **engine_kwargs)
        _SessionLocal = sessionmaker(bind=_engine)
        if cfg.ENV == "test" or cfg.DATABASE_URL == "dev":
            _initialize_schema(_engine)

    return _engine


@contextmanager
def db_session():
    if _SessionLocal is None:
        _get_engine()

    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
