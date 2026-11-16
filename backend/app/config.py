"""Application configuration for Academic Paper Assistant v2.

Every setting comes from environment variables (a `.env` file at the repository
root is loaded automatically).  Nothing secret is ever written to the database
or returned by the API.
"""

from __future__ import annotations

import os
import secrets
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# repo root = .../backend/app/config.py -> parents[2]
ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"

for candidate in (ROOT_DIR / ".env", BACKEND_DIR / ".env"):
    if candidate.exists():
        load_dotenv(candidate, override=False)


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    try:
        return int(_env(name, str(default)))
    except ValueError:
        return default


class Settings:
    """Runtime settings, resolved once at import time."""

    APP_NAME = _env("APP_NAME", "Academic Paper Assistant")
    APP_VERSION = "2.0.0"
    ENV = _env("APP_ENV", "development")

    # ---- storage -------------------------------------------------------
    # Relative paths are resolved against the repository root, not the
    # process working directory, so the API behaves the same however it is
    # started (uvicorn, systemd, docker).
    DATA_DIR = Path(
        _env("DATA_DIR", str(ROOT_DIR / "data"))
        if Path(_env("DATA_DIR", str(ROOT_DIR / "data"))).is_absolute()
        else ROOT_DIR / _env("DATA_DIR", "data")
    ).resolve()
    DB_PATH = Path(
        _env("DB_PATH", str(DATA_DIR / "apa.db"))
        if Path(_env("DB_PATH", str(DATA_DIR / "apa.db"))).is_absolute()
        else ROOT_DIR / _env("DB_PATH", "data/apa.db")
    ).resolve()
    FRONTEND_DIST = Path(
        _env("FRONTEND_DIST", str(ROOT_DIR / "frontend" / "dist"))
        if Path(_env("FRONTEND_DIST", str(ROOT_DIR / "frontend" / "dist"))).is_absolute()
        else ROOT_DIR / _env("FRONTEND_DIST", "frontend/dist")
    ).resolve()

    # ---- auth ----------------------------------------------------------
    JWT_SECRET = _env("JWT_SECRET")
    JWT_ALGORITHM = "HS256"
    TOKEN_TTL_HOURS = _env_int("TOKEN_TTL_HOURS", 24 * 14)
    ALLOW_REGISTRATION = _env_bool("ALLOW_REGISTRATION", True)
    ADMIN_EMAIL = _env("ADMIN_EMAIL", "admin@example.com")
    ADMIN_PASSWORD = _env("ADMIN_PASSWORD", "")
    ADMIN_NAME = _env("ADMIN_NAME", "Administrator")

    # ---- LLM -----------------------------------------------------------
    # provider: "openai" (any OpenAI-compatible endpoint) or "anthropic"
    LLM_PROVIDER = _env("LLM_PROVIDER", "openai").lower()
    LLM_API_KEY = _env("LLM_API_KEY", _env("DEEPSEEK_API_KEY", ""))
    LLM_BASE_URL = _env("LLM_BASE_URL", "https://api.deepseek.com/v1").rstrip("/")
    LLM_MODEL = _env("LLM_MODEL", "deepseek-chat")
    LLM_MODEL_FAST = _env("LLM_MODEL_FAST", "") or LLM_MODEL
    LLM_TEMPERATURE = float(_env("LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS = _env_int("LLM_MAX_TOKENS", 4096)
    LLM_TIMEOUT_SECONDS = _env_int("LLM_TIMEOUT_SECONDS", 300)
    LLM_MAX_RETRIES = _env_int("LLM_MAX_RETRIES", 3)

    # ---- literature ----------------------------------------------------
    SEMANTIC_SCHOLAR_API_KEY = _env("SEMANTIC_SCHOLAR_API_KEY")
    OPENALEX_EMAIL = _env("OPENALEX_EMAIL")
    LITERATURE_TIMEOUT_SECONDS = _env_int("LITERATURE_TIMEOUT_SECONDS", 20)
    LITERATURE_CACHE_TTL_HOURS = _env_int("LITERATURE_CACHE_TTL_HOURS", 72)
    DEFAULT_REFERENCE_COUNT = _env_int("DEFAULT_REFERENCE_COUNT", 12)

    # ---- generation ----------------------------------------------------
    MAX_CONCURRENT_JOBS = _env_int("MAX_CONCURRENT_JOBS", 2)
    MAX_PAPERS_PER_USER = _env_int("MAX_PAPERS_PER_USER", 200)

    # ---- http ----------------------------------------------------------
    CORS_ORIGINS = [
        o.strip()
        for o in _env(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173",
        ).split(",")
        if o.strip()
    ]
    TRUSTED_HOSTS = [h.strip() for h in _env("TRUSTED_HOSTS", "*").split(",")]

    @property
    def llm_configured(self) -> bool:
        return bool(self.LLM_API_KEY)

    def ensure_dirs(self) -> None:
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        (self.DATA_DIR / "exports").mkdir(parents=True, exist_ok=True)
        (self.DATA_DIR / "uploads").mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()

    # A stable JWT secret is required; generate and persist one on first run so
    # that restarts do not invalidate every session.
    if not settings.JWT_SECRET:
        secret_file = settings.DATA_DIR / "jwt_secret"
        if secret_file.exists():
            settings.JWT_SECRET = secret_file.read_text(encoding="utf-8").strip()
        else:
            secret = secrets.token_urlsafe(48)
            secret_file.write_text(secret, encoding="utf-8")
            try:
                secret_file.chmod(0o600)
            except OSError:
                pass
            settings.JWT_SECRET = secret
    return settings
