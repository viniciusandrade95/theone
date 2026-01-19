from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

from core.db.base import Base


class TenantORM(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
