"""Configuration management for search-cli."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

CONFIG_DIR_NAME = "search-cli"


def get_config_dir() -> Path:
    """Return the configuration directory path, creating it if necessary."""
    # Check XDG_CONFIG_HOME or fallback to ~/.config/search-cli
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        config_dir = Path(xdg_config) / CONFIG_DIR_NAME
    else:
        config_dir = Path.home() / ".config" / CONFIG_DIR_NAME
    
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_path() -> Path:
    """Return path to config.json."""
    return get_config_dir() / "config.json"


def get_token_path() -> Path:
    """Return path to OAuth token file."""
    return get_config_dir() / "token.json"


def load_config() -> Dict[str, Any]:
    """Load configuration from config.json."""
    config_file = get_config_path()
    if not config_file.exists():
        return {}
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(config_data: Dict[str, Any]) -> None:
    """Save configuration to config.json."""
    config_file = get_config_path()
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)


def get_config_value(key: str, default: Any = None) -> Any:
    """Get a specific configuration value."""
    config = load_config()
    return config.get(key, default)


def set_config_value(key: str, value: Any) -> None:
    """Set a specific configuration value."""
    config = load_config()
    if value is None:
        config.pop(key, None)
    else:
        config[key] = value
    save_config(config)
