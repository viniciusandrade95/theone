import os
import pytest

from core.config.loader import load_config, get_config


def _clear_env(keys: list[str]):
    for k in keys:
        os.environ.pop(k, None)


def _set_env(values: dict[str, str]):
    for k, v in values.items():
        os.environ[k] = v


@pytest.fixture(autouse=True)
def reset_config_singleton(monkeypatch):
    # Import interno para conseguir resetar o singleton do loader
    import core.config.loader as loader
    monkeypatch.setattr(loader, "_config", None)
    yield
    monkeypatch.setattr(loader, "_config", None)


def test_get_config_fails_if_not_loaded():
    with pytest.raises(RuntimeError) as e:
        get_config()
    assert "Config not loaded" in str(e.value)


def test_load_config_fails_fast_when_required_env_missing():
    required = ["ENV", "APP_NAME", "DATABASE_URL", "SECRET_KEY"]
    _clear_env(required)

    with pytest.raises(RuntimeError) as e:
        load_config()

    # Deve indicar exatamente qual env faltou
    assert "Missing required env var:" in str(e.value)


def test_load_config_applies_defaults_for_optional_env():
    _set_env({
        "ENV": "local",
        "APP_NAME": "beauty-crm",
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/db",
        "SECRET_KEY": "change-me",
        # não setamos HTTP_HOST, HTTP_PORT, LOG_LEVEL, TENANT_HEADER
    })

    cfg = load_config()

    assert cfg.HTTP_HOST == "0.0.0.0"
    assert cfg.HTTP_PORT == 8000
    assert cfg.LOG_LEVEL == "INFO"
    assert cfg.TENANT_HEADER == "X-Tenant-ID"
    assert cfg.WHATSAPP_WEBHOOK_SECRET is None


def test_load_config_then_get_config_returns_same_instance():
    _set_env({
        "ENV": "local",
        "APP_NAME": "beauty-crm",
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/db",
        "SECRET_KEY": "change-me",
    })

    cfg1 = load_config()
    cfg2 = get_config()

    assert cfg1 is cfg2


def test_load_config_is_idempotent():
    _set_env({
        "ENV": "local",
        "APP_NAME": "beauty-crm",
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/db",
        "SECRET_KEY": "change-me",
    })

    cfg1 = load_config()
    cfg2 = load_config()

    assert cfg1 is cfg2
