from abc import ABC, abstractmethod
from modules.iam.models.user import User


class UserRepo(ABC):
    @abstractmethod
    def get_by_email(self, tenant_id: str, email: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    def create(self, user: User) -> None:
        raise NotImplementedError

###########billing
    @abstractmethod
    def count_users(self, tenant_id: str) -> int:
        raise NotImplementedError

