"""Application configuration loaded from environment variables (and an optional .env file)."""
from __future__ import annotations

import warnings
from functools import lru_cache
from typing import List, Optional

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Used only for local development when GSTRECON_SECRET_KEY is not provided.
# Refused outright when ENV=production.
_DEV_SECRET_KEY = "dev-insecure-secret-key-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: str = Field(default="development", validation_alias=AliasChoices("ENV", "APP_ENV"))
    project_name: str = "GSTRecon AI"
    api_v1_prefix: str = "/api/v1"

    secret_key: Optional[str] = Field(default=None, validation_alias="GSTRECON_SECRET_KEY")
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = Field(default=60 * 12, validation_alias="JWT_EXPIRATION_MINUTES")

    database_url: str = Field(default="sqlite:///./gstrecon.db", validation_alias="DATABASE_URL")
    # Optional: when unset, reconciliation runs in-process (FastAPI BackgroundTasks) instead of Celery.
    redis_url: Optional[str] = Field(default=None, validation_alias="REDIS_URL")
    celery_broker_url: Optional[str] = Field(default=None, validation_alias="CELERY_BROKER_URL")
    celery_result_backend: Optional[str] = Field(default=None, validation_alias="CELERY_RESULT_BACKEND")

    # When false (default), POST /auth/register always creates an "accountant" user.
    allow_admin_signup: bool = Field(default=False, validation_alias="ALLOW_ADMIN_SIGNUP")

    storage_dir: str = Field(default="./storage", validation_alias="STORAGE_DIR")

    # Comma-separated list of allowed origins, e.g. "https://myapp.vercel.app,http://localhost:5173".
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173", validation_alias="CORS_ORIGINS"
    )
    # Optional regex, e.g. "https://.*\.vercel\.app" to also allow Vercel preview deployments.
    cors_origin_regex: Optional[str] = Field(default=None, validation_alias="CORS_ORIGIN_REGEX")

    @field_validator("database_url")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        value = value.strip()
        # Heroku/Railway-style URLs use "postgres://", which SQLAlchemy 2.x rejects.
        if value.startswith("postgres://"):
            value = "postgresql://" + value[len("postgres://"):]
        if value.startswith("postgresql://"):
            value = "postgresql+psycopg2://" + value[len("postgresql://"):]
        return value

    @field_validator(
        "secret_key", "redis_url", "celery_broker_url", "celery_result_backend", "cors_origin_regex",
        mode="before",
    )
    @classmethod
    def _blank_to_none(cls, value):
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @model_validator(mode="after")
    def _check_production(self) -> "Settings":
        if self.is_production:
            if not self.secret_key or self.secret_key == _DEV_SECRET_KEY or len(self.secret_key) < 32:
                raise ValueError(
                    "GSTRECON_SECRET_KEY must be set to a strong random value (>= 32 chars) when ENV=production"
                )
            if self.database_url.startswith("sqlite"):
                warnings.warn(
                    "ENV=production but DATABASE_URL points to SQLite; data will not survive redeploys.",
                    stacklevel=2,
                )
        elif not self.secret_key:
            self.secret_key = _DEV_SECRET_KEY
        return self

    @property
    def is_production(self) -> bool:
        return self.env.strip().lower() in {"production", "prod"}

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip().rstrip("/") for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def broker_url(self) -> Optional[str]:
        return self.celery_broker_url or self.redis_url

    @property
    def use_celery(self) -> bool:
        """Celery is used only when a broker (Redis) is configured."""
        return bool(self.broker_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()
