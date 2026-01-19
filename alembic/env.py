from logging.config import fileConfig

from sqlalchemy import create_engine, pool
from alembic import context

from core.config import load_config, get_config
from core.db.base import Base

# IMPORTA MODELS PARA AUTOGENERATE
from modules.tenants.models.tenant import TenantORM  # noqa

# Alembic Config
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata global (NUNCA None)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    load_config()
    cfg = get_config()

    context.configure(
        url=cfg.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    load_config()
    cfg = get_config()

    engine = create_engine(
        cfg.DATABASE_URL,
        poolclass=pool.NullPool,
    )

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
