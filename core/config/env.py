from dataclasses import dataclass
import os


def _get(name: str, required: bool = True, default=None):
    value = os.getenv(name, default)

    # Normaliza strings vazias para None (especialmente vindo de .env)
    if isinstance(value, str) and value.strip() == "":
        value = None

    if required and value is None:
        raise RuntimeError(f"Missing required env var: {name}")
    return value



@dataclass(frozen=True)
class AppConfig:
    # App
    ENV: str
    APP_NAME: str

    # HTTP
    HTTP_HOST: str
    HTTP_PORT: int

    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str

    # Observability
    LOG_LEVEL: str

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

            DATABASE_URL=_get("DATABASE_URL"),

            SECRET_KEY=_get("SECRET_KEY"),

            LOG_LEVEL=_get("LOG_LEVEL", default="INFO"),

            TENANT_HEADER=_get("TENANT_HEADER", default="X-Tenant-ID"),

            WHATSAPP_WEBHOOK_SECRET=_get(
                "WHATSAPP_WEBHOOK_SECRET", required=False
            ),
        )
