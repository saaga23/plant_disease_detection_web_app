"""Environment-based configuration. No secrets are stored in source code."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:  # optional at runtime; the app also works with real environment variables
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
except ImportError:  # pragma: no cover
    pass

APP_ROOT = Path(__file__).resolve().parent.parent.parent
ASSETS_DIR = APP_ROOT / "assets"
MODELS_DIR = APP_ROOT / "models"
MANIFEST_PATH = MODELS_DIR / "model_manifest.json"
DEMO_DATA_DIR = APP_ROOT / "data" / "demo"


@dataclass(frozen=True)
class Settings:
    db_mode: str
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str
    openai_api_key: str | None
    serpapi_api_key: str | None
    max_upload_mb: int

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def has_serpapi(self) -> bool:
        return bool(self.serpapi_api_key)


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


def get_settings() -> Settings:
    return Settings(
        db_mode=os.environ.get("DB_MODE", "sqlite").strip().lower(),
        db_host=os.environ.get("DB_HOST", "127.0.0.1"),
        db_port=_int_env("DB_PORT", 3306),
        db_user=os.environ.get("DB_USER", "plant_app_user"),
        db_password=os.environ.get("DB_PASSWORD", ""),
        db_name=os.environ.get("DB_NAME", "farm_demo"),
        openai_api_key=os.environ.get("OPENAI_API_KEY", "").strip() or None,
        serpapi_api_key=os.environ.get("SERPAPI_API_KEY", "").strip() or None,
        max_upload_mb=_int_env("MAX_UPLOAD_MB", 10),
    )
