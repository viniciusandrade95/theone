from core.errors import ConflictError
from modules.iam.models.user import User
from modules.iam.repo.user_repo import UserRepo


class InMemoryUserRepo(UserRepo):
    def __init__(self):
        # key: (tenant_id, email)
        self._users: dict[tuple[str, str], User] = {}

    def get_by_email(self, tenant_id: str, email: str) -> User | None:
        return self._users.get((tenant_id, email.strip().lower()))

    def get_by_id(self, tenant_id: str, user_id: str) -> User | None:
        for (tenant, _email), user in self._users.items():
            if tenant == tenant_id and user.id == user_id:
                return user
        return None

    def create(self, user: User) -> None:
        key = (user.tenant_id, user.email)
        if key in self._users:
            raise ConflictError("User already exists", meta={"tenant_id": user.tenant_id, "email": user.email})
        self._users[key] = user

############billing
    def count_users(self, tenant_id: str) -> int:
        return sum(1 for (t, _), _u in self._users.items() if t == tenant_id)
