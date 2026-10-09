from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    database_url: str
    jwt_secret_key: str = Field(min_length=32)
    access_token_expire_minutes: int = 10080
    upload_dir: Path = Field(default=PROJECT_ROOT / "uploads")
    cors_origins: str = "*"
    auto_migrate: bool = True
    database_echo: bool = False
    environment: str = "production"
    image_storage_backend: Literal["local", "supabase"] = "local"
    supabase_s3_endpoint: str | None = None
    supabase_s3_region: str | None = None
    supabase_s3_access_key_id: str | None = None
    supabase_s3_secret_access_key: str | None = None
    supabase_storage_bucket: str | None = None

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_database_url(cls, v: str) -> str:
        if not isinstance(v, str):
            return v
        url = v.strip()
        # Render PostgreSQL URLs start with postgres:// or postgresql://
        # asyncpg requires postgresql+asyncpg://
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def cors_origins_list(self) -> list[str]:
        if not self.cors_origins or self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def database_connect_args(self) -> dict[str, object]:
        """Return asyncpg options required for Supabase connections."""
        url = make_url(self.database_url)
        host = (url.host or "").lower()
        is_supabase = host.endswith(".supabase.co") or host.endswith(".pooler.supabase.com")

        if not is_supabase:
            return {}

        # Supabase requires encrypted connections. Transaction poolers also
        # require asyncpg's prepared statement cache to be disabled.
        args: dict[str, object] = {"ssl": "require"}
        if url.port == 6543:
            args["statement_cache_size"] = 0
        return args


settings = Settings()
