from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    LOG_LEVEL: str = "INFO"

    POSTGRES_AUTH_DATABASE_URL: str

    REDIS_AUTH_URL: str = "redis://redis-auth:6379/0"

    API_GATEWAY_URL: str = "http://api-gateway:8000"

    INTERNAL_API_KEY: str

    PRIVATE_KEY: str
    PUBLIC_KEY: str

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @field_validator("PRIVATE_KEY", "PUBLIC_KEY", mode="before")
    @classmethod
    def fix_pem_newlines(cls, v: str) -> str:
        return v.replace("\\n", "\n")

    # Valida que el enlace sea para asyncpg, si no lo es lo remplaza.
    @field_validator("POSTGRES_AUTH_DATABASE_URL", mode="before")
    @classmethod
    def fix_database_url(cls, v: str) -> str:
        if v and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        if v and v.startswith("postgresql+psycopg2://"):
            return v.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
        return v


settings = Settings()
