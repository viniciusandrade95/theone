from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from core.db.base import Base
from modules.crm.models.interaction import Interaction


class InteractionORM(Base):
    __tablename__ = "interactions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("tenants.id"),
        index=True,
        nullable=False,
    )
    customer_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("customers.id"),
        index=True,
        nullable=False,
    )

    type: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    def to_domain(self) -> Interaction:
        return Interaction(
            id=self.id,
            tenant_id=self.tenant_id,
            customer_id=self.customer_id,
            type=self.type,
            content=self.content,
            created_at=self.created_at,
        )

    @staticmethod
    def from_domain(interaction: Interaction) -> "InteractionORM":
        return InteractionORM(
            id=interaction.id,
            tenant_id=interaction.tenant_id,
            customer_id=interaction.customer_id,
            type=interaction.type,
            content=interaction.content,
            created_at=interaction.created_at,
        )
