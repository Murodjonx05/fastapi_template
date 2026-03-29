from pathlib import Path
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
        default=False,
        alias="RUN_MIGRATIONS_ON_STARTUP",
    )
    host: str = Field(default="127.0.0.1", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    debug_mode: bool = Field(default=False, alias="RELOAD")
    trust_proxy_headers: bool = Field(default=False, alias="TRUST_PROXY_HEADERS")
    forwarded_allow_ips: str = Field(default="127.0.0.1", alias="FORWARDED_ALLOW_IPS")
    model_config = MODEL_CONFIG

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str, info: ValidationInfo) -> str:
        if not value.startswith(("postgresql://", "postgresql+asyncpg://", "postgresql+psycopg://")):
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
        return (
            self.database_url
            .replace("sqlite+aiosqlite:///", "sqlite:///", 1)
            .replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
        )

app_settings = AppSettings()
