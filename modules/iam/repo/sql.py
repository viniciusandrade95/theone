from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from core.db.session import db_session
from core.errors import ConflictError
from modules.iam.repo.user_repo import UserRepo
from modules.iam.models.user import User
from modules.iam.models.user_orm import UserORM


class SqlUserRepo(UserRepo):
    def _coerce_uuid(self, value: str):
        try:
            return UUID(value)
        except (TypeError, ValueError):
            return value

    def get_by_email(self, tenant_id: str, email: str) -> User | None:
        with db_session() as session:
            stmt = (
                select(UserORM)
                .where(UserORM.tenant_id == self._coerce_uuid(tenant_id))
                .where(UserORM.email == email.strip().lower())
            )
            row = session.execute(stmt).scalar_one_or_none()
            return row.to_domain() if row else None

    def list_by_email(self, email: str) -> list[User]:
        with db_session() as session:
            stmt = select(UserORM).where(UserORM.email == email.strip().lower())
            rows = session.execute(stmt).scalars().all()
            return [r.to_domain() for r in rows]

    def get_by_id(self, tenant_id: str, user_id: str) -> User | None:
        with db_session() as session:
            stmt = (
                select(UserORM)
                .where(UserORM.tenant_id == self._coerce_uuid(tenant_id))
                .where(UserORM.id == self._coerce_uuid(user_id))
            )
            row = session.execute(stmt).scalar_one_or_none()
            return row.to_domain() if row else None

    def create(self, user: User) -> None:
        try:
            with db_session() as session:
                session.add(
                    UserORM(
                        id=self._coerce_uuid(user.id),
                        tenant_id=self._coerce_uuid(user.tenant_id),
                        email=user.email,
                        password_hash=user.password_hash,
                    )
                )
        except IntegrityError:
            raise ConflictError("User already exists", meta={"tenant_id": user.tenant_id, "email": user.email})

    def count_users(self, tenant_id: str) -> int:
        with db_session() as session:
            stmt = (
                select(func.count())
                .select_from(UserORM)
                .where(UserORM.tenant_id == self._coerce_uuid(tenant_id))
            )
            return session.execute(stmt).scalar_one()
