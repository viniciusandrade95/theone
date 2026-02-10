from core.config.env import AppConfig

_config: AppConfig | None = None


def load_config() -> AppConfig:
    global _config
    if _config is None:
        _config = AppConfig.load()
        if _config.ENV == "test" and _config.DATABASE_URL == "dev":
            from core.db.session import reset_engine_state

            reset_engine_state()
    return _config


def get_config() -> AppConfig:
    if _config is None:
        raise RuntimeError("Config not loaded. Call load_config() at startup.")
    return _config
