import os

DYNAMIC_CONFIG: dict[str, str] = {}


def resolve_config(key: str) -> str:
    """Returns a configuration value from dynamic session config or environment."""
    return DYNAMIC_CONFIG.get(key) or os.getenv(key, "")


def is_configured(*keys: str) -> bool:
    return all(bool(resolve_config(key)) for key in keys)
