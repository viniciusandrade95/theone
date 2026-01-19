from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import get_config

_engine = None
_Session = None

def get_engine():
    global _engine
    if _engine is None:
        cfg = get_config()
        _engine = create_engine(cfg.DATABASE_URL, pool_pre_ping=True)
    return _engine

def get_session():
    global _Session
    if _Session is None:
        _Session = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _Session()
