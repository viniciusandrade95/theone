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
    AUTH_TOKEN_TTL_SECONDS: int

    # Observability
    LOG_LEVEL: str

    # Queue
    REDIS_URL: str
    CELERY_TASK_ALWAYS_EAGER: bool

    # Tenancy
    TENANT_HEADER: str

    # Messaging (WhatsApp)
    WHATSAPP_WEBHOOK_SECRET: str | None
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str | None
    WHATSAPP_CLOUD_ACCESS_TOKEN: str | None
    WHATSAPP_CLOUD_API_VERSION: str
    WHATSAPP_CLOUD_TIMEOUT_SECONDS: int

    # Messaging (Email / SMTP)
    SMTP_HOST: str | None
    SMTP_PORT: int
    SMTP_USERNAME: str | None
    SMTP_PASSWORD: str | None
    SMTP_FROM: str | None
    SMTP_TIMEOUT_SECONDS: int
    SMTP_USE_STARTTLS: bool

    # Chatbot integration
    CHATBOT_SERVICE_BASE_URL: str | None
    CHATBOT_SERVICE_TIMEOUT_SECONDS: int
    CHATBOT_CLIENT_ID: str | None
    ASSISTANT_CONNECTOR_HEADER: str
    ASSISTANT_CONNECTOR_TOKEN: str | None

    @staticmethod
    def load() -> "AppConfig":
        env = _get("ENV")
        assistant_token_required = env in {"prod", "production"}
        return AppConfig(
            ENV=env,
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
            AUTH_TOKEN_TTL_SECONDS=int(_get("AUTH_TOKEN_TTL_SECONDS", required=False, default="604800")),

            LOG_LEVEL=_get("LOG_LEVEL", default="INFO"),

            TENANT_HEADER=_get("TENANT_HEADER", default="X-Tenant-ID"),

            WHATSAPP_WEBHOOK_SECRET=_get(
                "WHATSAPP_WEBHOOK_SECRET", required=False
            ),
            WHATSAPP_WEBHOOK_VERIFY_TOKEN=_get("WHATSAPP_WEBHOOK_VERIFY_TOKEN", required=False),
            WHATSAPP_CLOUD_ACCESS_TOKEN=_get("WHATSAPP_CLOUD_ACCESS_TOKEN", required=False),
            WHATSAPP_CLOUD_API_VERSION=_get("WHATSAPP_CLOUD_API_VERSION", required=False, default="v19.0") or "v19.0",
            WHATSAPP_CLOUD_TIMEOUT_SECONDS=int(_get("WHATSAPP_CLOUD_TIMEOUT_SECONDS", required=False, default="10")),

            SMTP_HOST=_get("SMTP_HOST", required=False),
            SMTP_PORT=int(_get("SMTP_PORT", required=False, default="587") or 587),
            SMTP_USERNAME=_get("SMTP_USERNAME", required=False),
            SMTP_PASSWORD=_get("SMTP_PASSWORD", required=False),
            SMTP_FROM=_get("SMTP_FROM", required=False),
            SMTP_TIMEOUT_SECONDS=int(_get("SMTP_TIMEOUT_SECONDS", required=False, default="10") or 10),
            SMTP_USE_STARTTLS=bool(
                str(_get("SMTP_USE_STARTTLS", required=False, default="true")).strip().lower() in {"1", "true", "yes"}
            ),

            CHATBOT_SERVICE_BASE_URL=_get("CHATBOT_SERVICE_BASE_URL", required=False),
            CHATBOT_SERVICE_TIMEOUT_SECONDS=int(_get("CHATBOT_SERVICE_TIMEOUT_SECONDS", required=False, default="15")),
            CHATBOT_CLIENT_ID=_get("CHATBOT_CLIENT_ID", required=False),
            ASSISTANT_CONNECTOR_HEADER=_get(
                "ASSISTANT_CONNECTOR_HEADER",
                required=False,
                default="X-Assistant-Token",
            )
            or "X-Assistant-Token",
            ASSISTANT_CONNECTOR_TOKEN=_get("ASSISTANT_CONNECTOR_TOKEN", required=assistant_token_required),

            REDIS_URL=_get("REDIS_URL", required=False, default="redis://localhost:6379/0"),
            CELERY_TASK_ALWAYS_EAGER=bool(
                str(_get("CELERY_TASK_ALWAYS_EAGER", required=False, default=""))
                .strip()
                .lower()
                in {"1", "true", "yes"}
            )
        )
