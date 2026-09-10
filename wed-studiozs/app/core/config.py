"""Application settings loaded from environment variables / .env file."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        hide_input_in_errors=True,
    )

    app_name: str = "WED STUDIOZS"
    environment: Literal["development", "testing", "production"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    database_url: str | None = Field(default=None, repr=False)
    database_host: str = "localhost"
    database_port: int = Field(default=5432, ge=1, le=65535)
    database_name: str = "wedstudiozs"
    database_user: str = "postgres"
    database_password: str | None = Field(default=None, repr=False)
    db_echo: bool = False
    db_pool_size: int = Field(default=5, ge=1, le=50)
    db_max_overflow: int = Field(default=0, ge=0, le=20)
    db_pool_timeout_seconds: float = Field(default=2, ge=0.1, le=30)
    db_pool_recycle_seconds: int = Field(default=900, ge=30, le=86400)
    schema_check_timeout_seconds: float = Field(default=3, ge=0.1, le=30)

    secret_key: str = Field(repr=False)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=60, ge=1, le=1440)

    business_phone: str = "+91 98765 43210"
    business_email: str = "hello@wedstudiozs.com"
    business_address: str = "2nd Floor, Jubilee Hills, Hyderabad, India"

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:8000"])
    default_page_size: int = 12
    max_page_size: int = 100

    @field_validator("secret_key")
    @classmethod
    def _validate_secret_key(cls, value: str) -> str:
        normalized = value.strip().lower()
        if (
            len(value.strip()) < 32
            or normalized.startswith(("change-me", "changeme", "insecure-dev-key"))
            or normalized in {"your-secret-key-here", "replace-with-a-long-random-secret"}
        ):
            raise ValueError("SECRET_KEY must be a generated secret of at least 32 characters.")
        return value

    @model_validator(mode="after")
    def _configure_database_url(self) -> "Settings":
        if self.database_url is None:
            if not self.database_password or not self.database_password.strip():
                raise ValueError("Set DATABASE_URL or supply DATABASE_PASSWORD and database connection fields.")
            self.database_url = URL.create(
                "postgresql+asyncpg",
                username=self.database_user,
                password=self.database_password,
                host=self.database_host,
                port=self.database_port,
                database=self.database_name,
            ).render_as_string(hide_password=False)
        try:
            url = make_url(self.database_url)
            driver = {
                "postgres": "postgresql+asyncpg",
                "postgresql": "postgresql+asyncpg",
                "sqlite": "sqlite+aiosqlite",
            }.get(url.drivername, url.drivername)
            if driver not in {"postgresql+asyncpg", "sqlite+aiosqlite"}:
                raise ValueError
            self.database_url = url.set(drivername=driver).render_as_string(hide_password=False)
        except (ArgumentError, ValueError, TypeError):
            raise ValueError("DATABASE_URL must be a valid PostgreSQL or SQLite connection URL.") from None
        return self

    @property
    def sync_database_url(self) -> str:
        """Alembic runs migrations synchronously in this project setup."""
        url = make_url(self.database_url)
        driver = "sqlite" if url.drivername == "sqlite+aiosqlite" else "postgresql+psycopg2"
        return url.set(drivername=driver).render_as_string(hide_password=False)

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached accessor so the .env file is parsed only once per process."""
    return Settings()


settings = get_settings()

__all__ = ["PostgresDsn", "Settings", "get_settings", "settings"]
