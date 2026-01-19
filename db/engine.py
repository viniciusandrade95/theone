from sqlalchemy import create_engine
from core.config import get_config

_engine = None

def get_engine():
    global _engine
    if _engine is None:
        cfg = get_config()
        _engine = create_engine(cfg.DATABASE_URL, pool_pre_ping=True)
    return _engine
