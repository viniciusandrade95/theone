import uuid
from core.errors import UnauthorizedError, ForbiddenError
from core.security.hashing import hash_password, verify_password
from core.tenancy import require_tenant_id
from modules.iam.models.user import User
from modules.iam.repo.user_repo import UserRepo
from modules.billing.service import BillingService


class AuthService:
    def __init__(self, repo: UserRepo, billing: BillingService):
        self.repo = repo
        self.billing = billing

    def register(self, *, email: str, password: str) -> User:
        tenant_id = require_tenant_id()

        # Enforce plan limit: users
        current = self.repo.count_users(tenant_id)
        res = self.billing.check_limit(kind="users", current=current + 1)
        if not res.allowed:
            raise ForbiddenError("Plan limit exceeded", meta={"reason": res.reason})

        pw_hash = hash_password(password)
        user = User.create(
            user_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            email=email,
            password_hash=pw_hash,
        )
        self.repo.create(user)
        return user

    def authenticate(self, *, email: str, password: str) -> User:
        tenant_id = require_tenant_id()

        user = self.repo.get_by_email(tenant_id, email)
        if user is None:
            raise UnauthorizedError("Invalid credentials")

        if not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid credentials")

        return user

    def get_user(self, *, user_id: str) -> User:
        tenant_id = require_tenant_id()
        user = self.repo.get_by_id(tenant_id, user_id)
        if user is None:
            raise UnauthorizedError("User not found")
        return user

    def authenticate_by_email_global(self, *, email: str, password: str) -> list[User]:
        candidates = self.repo.list_by_email(email)
        matches: list[User] = []
        for u in candidates:
            if verify_password(password, u.password_hash):
                matches.append(u)

        if not matches:
            raise UnauthorizedError("Invalid credentials")

        return matches