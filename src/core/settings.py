from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = (BASE_DIR / "data" / "database.db").resolve()


class ProductSettings(BaseSettings):
    title: str = Field(default="FastAPI Application", alias="NAME")
    description: str = Field(default="FastAPI Application", alias="DESCRIPTION")
    version: str = Field(default="1.0.0", alias="VERSION")

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class DatabaseSettings(BaseSettings):
    database_url: str = Field(
        default=f"sqlite+aiosqlite:///{DEFAULT_DB_PATH.as_posix()}",
        alias="DATABASE_URL",
    )

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def sync_database_url(self) -> str:
        if self.database_url.startswith("sqlite+aiosqlite:///"):
            return self.database_url.replace("sqlite+aiosqlite:///", "sqlite:///", 1)
        if self.database_url.startswith("postgresql+asyncpg://"):
            return self.database_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
        return self.database_url


class AppSettings(ProductSettings, DatabaseSettings):
    host: str = Field(default="127.0.0.1", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    debug_mode: bool = Field(default=False, alias="RELOAD")

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()


app_settings = get_settings()