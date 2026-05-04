from functools import lru_cache
from pathlib import Path
import secrets
from urllib.parse import parse_qs, urlparse

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = (BASE_DIR / "data" / "database.db").resolve()

MODEL_CONFIG = SettingsConfigDict(
    env_file=BASE_DIR / ".env",
    env_file_encoding="utf-8",
    extra="ignore",
)


@lru_cache(maxsize=1)
def _get_dev_jwt_secret_key() -> str:
    return secrets.token_urlsafe(32)


class AppSettings(BaseSettings):
    title: str = Field(default="FastAPI Application", alias="NAME")
    description: str = Field(default="FastAPI Application", alias="DESCRIPTION")
    version: str = Field(default="1.0.0", alias="VERSION")
    db_require_tls: bool = Field(default=False, alias="DB_REQUIRE_TLS")
    database_url: str = Field(
        default=f"sqlite+aiosqlite:///{DEFAULT_DB_PATH.as_posix()}",
        alias="DATABASE_URL",
    )
    run_migrations_on_startup: bool = Field(
        default=True, alias="RUN_MIGRATIONS_ON_STARTUP"
    )
    host: str = Field(default="127.0.0.1", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    debug_mode: bool = Field(default=False, alias="RELOAD")
    trust_proxy_headers: bool = Field(default=False, alias="TRUST_PROXY_HEADERS")
    forwarded_allow_ips: str = Field(default="127.0.0.1", alias="FORWARDED_ALLOW_IPS")
    docs_enabled: bool | None = Field(default=None, alias="DOCS_ENABLED")
    jwt_secret_key: str | None = Field(default=None, alias="JWT_SECRET_KEY")

    model_config = MODEL_CONFIG

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str, info: ValidationInfo) -> str:
        if not value.startswith(
            ("postgresql://", "postgresql+asyncpg://", "postgresql+psycopg://")
        ):
            return value

        if not info.data.get("db_require_tls", False):
            return value

        parsed = urlparse(value)
        sslmode = parse_qs(parsed.query).get("sslmode", [""])[0].lower()
        allowed_modes = {"require", "verify-ca", "verify-full"}
        if sslmode not in allowed_modes:
            raise ValueError(
                "PostgreSQL DATABASE_URL must include sslmode=require|verify-ca|verify-full "
                "when DB_REQUIRE_TLS=true"
            )
        return value

    @property
    def sync_database_url(self) -> str:
        return self.database_url.replace(
            "sqlite+aiosqlite:///", "sqlite:///", 1
        ).replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret_key(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if len(value) < 32 or value.lower() in {
            "change-me",
            "your-secret-key",
            "secret",
            "password",
        }:
            raise ValueError(
                "JWT_SECRET_KEY must be set to a strong random value with at least 32 characters"
            )
        return value

    @property
    def effective_jwt_secret_key(self) -> str:
        if self.jwt_secret_key:
            return self.jwt_secret_key
        if self.debug_mode:
            return _get_dev_jwt_secret_key()
        raise ValueError("JWT_SECRET_KEY must be configured when RELOAD is false")

    @property
    def is_docs_enabled(self) -> bool:
        if self.docs_enabled is not None:
            return self.docs_enabled
        return self.debug_mode


app_settings = AppSettings()
