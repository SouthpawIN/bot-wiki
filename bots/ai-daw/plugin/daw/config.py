"""Plugin configuration, read at call time.

Two sources, in priority order:

1. environment variables (``DAW_ENGINE``, ``DAW_REPLICATE_TOKEN``, ...)
2. ``config.json`` - ``DAW_CONFIG`` if set, else ``~/.hermes/daw-config.json``

The file lives outside the plugin directory so that deleting and reinstalling
the plugin (the documented uninstall) does not take the user's config with it.
Nothing is read at import time; the contract says no import-time side effects.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_ENGINE = "dryrun"  # 0.1 behaviour: generate_layer without a choice stays offline
CONFIG_PATH = Path.home() / ".hermes" / "daw-config.json"


def path() -> Path:
    return Path(os.environ.get("DAW_CONFIG") or CONFIG_PATH)


def load() -> dict[str, Any]:
    """The config file as a dict; a missing or malformed file is an empty config."""
    try:
        data = json.loads(path().read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def setting(key: str, env: str | None = None, default: Any = None) -> Any:
    """env (if set) > config.json > default."""
    value = os.environ.get(env or f"DAW_{key.upper()}")
    if value not in (None, ""):
        return value
    return load().get(key, default)


def engine_choice() -> str:
    """The configured default engine: a name, or ``auto``."""
    return str(setting("engine", default=DEFAULT_ENGINE) or DEFAULT_ENGINE)
