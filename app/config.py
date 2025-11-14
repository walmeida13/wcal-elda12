"""Configuration utilities for environment management."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict

ENV_CACHE: Dict[str, str] | None = None


def load_env(path: str = ".env") -> Dict[str, str]:
    """Load environment variables from a .env file if it exists."""
    global ENV_CACHE
    if ENV_CACHE is not None:
        return ENV_CACHE

    env_path = Path(path)
    variables: Dict[str, str] = {}

    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if not line or line.strip().startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                variables[key] = value
                os.environ.setdefault(key, value)

    ENV_CACHE = variables
    return variables


def get_google_api_key() -> str | None:
    """Return the configured Google Vision API key, if any."""
    return os.environ.get("GOOGLE_VISION_API_KEY")
