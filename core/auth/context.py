from contextvars import ContextVar

_user_id: ContextVar[str | None] = ContextVar("user_id", default=None)


def set_current_user_id(user_id: str) -> None:
    if not user_id or user_id.strip() == "":
        raise RuntimeError("user_id cannot be empty")
    _user_id.set(user_id)


def get_current_user_id() -> str | None:
    return _user_id.get()


def clear_current_user_id() -> None:
    _user_id.set(None)
