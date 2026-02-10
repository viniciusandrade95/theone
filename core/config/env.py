from dataclasses import dataclass
import os


def _get(name: str, required: bool = True, default=None):
    value = os.getenv(name, default)

    if isinstance(value, str) and len(value) >= 2:
        if (value.startswith("'") and value.endswith("'")) or (value.startswith('"') and value.endswith('"')):
            value = value[1:-1]

    # Normaliza strings vazias para None (especialmente vindo de .env)
    if isinstance(value, str) and value.strip() == "":
        value = None

    if required and value is None:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def _get_csv(name: str, default: str = "") -> list[str]:
    raw = _get(name, required=False, default=default)
    if raw is None:
        return []
    if isinstance(raw, str):
        return [item.strip() for item in raw.split(",") if item.strip()]
    return []



@dataclass(frozen=True)
class AppConfig:
    # App
    ENV: str
    APP_NAME: str

    # HTTP
    HTTP_HOST: str
    HTTP_PORT: int
    CORS_ALLOW_ORIGINS: tuple[str, ...]
    CORS_ALLOW_ORIGIN_REGEX: str

    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str

    # Observability
    LOG_LEVEL: str

    # Queue
    REDIS_URL: str
    CELERY_TASK_ALWAYS_EAGER: bool

    # Tenancy
    TENANT_HEADER: str

    # Messaging (WhatsApp)
    WHATSAPP_WEBHOOK_SECRET: str | None

    @staticmethod
    def load() -> "AppConfig":
        return AppConfig(
            ENV=_get("ENV"),
            APP_NAME=_get("APP_NAME"),

            HTTP_HOST=_get("HTTP_HOST", default="0.0.0.0"),
            HTTP_PORT=int(_get("HTTP_PORT", default="8000")),
            CORS_ALLOW_ORIGINS=tuple(
                _get_csv(
                    "CORS_ALLOW_ORIGINS",
                    default="http://localhost:3000,http://127.0.0.1:3000",
                )
            ),
            CORS_ALLOW_ORIGIN_REGEX=_get(
                "CORS_ALLOW_ORIGIN_REGEX",
                required=False,
                default=(
                    r"^https?://("
                    r"localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\]|"
                    r"(?:[A-Za-z0-9-]+(?:\.local)?)|"
                    r"10(?:\.\d{1,3}){3}|"
                    r"192\.168(?:\.\d{1,3}){2}|"
                    r"172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2}"
                    r")(:\d+)?$"
                ),
            ),

            DATABASE_URL=_get("DATABASE_URL"),

            SECRET_KEY=_get("SECRET_KEY"),

            LOG_LEVEL=_get("LOG_LEVEL", default="INFO"),

            TENANT_HEADER=_get("TENANT_HEADER", default="X-Tenant-ID"),

            WHATSAPP_WEBHOOK_SECRET=_get(
                "WHATSAPP_WEBHOOK_SECRET", required=False
            ),

            REDIS_URL=_get("REDIS_URL", required=False, default="redis://localhost:6379/0"),
            CELERY_TASK_ALWAYS_EAGER=bool(
                str(_get("CELERY_TASK_ALWAYS_EAGER", required=False, default=""))
                .strip()
                .lower()
                in {"1", "true", "yes"}
            )
        )
