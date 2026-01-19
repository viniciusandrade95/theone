from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from core.config import get_config

_engine = None
_SessionLocal = None


def _get_engine():
    global _engine, _SessionLocal

    if _engine is None:
        cfg = get_config()
        _engine = create_engine(
            cfg.DATABASE_URL,
            pool_pre_ping=True,
        )
        _SessionLocal = sessionmaker(bind=_engine)

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
