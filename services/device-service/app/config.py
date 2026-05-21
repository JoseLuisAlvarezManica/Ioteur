from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    database_url: str = os.getenv("POSTGRES_DEVICE_DATABASE_URL")

    @field_validator("database_url", mode="before")
    @classmethod
    def fix_database_url(cls, v: str) -> str:
        prefixes = [
            "postgres://",
            "postgresql://",
            "postgresql+psycopg2://",
        ]
        for prefix in prefixes:
            if v and v.startswith(prefix):
                return v.replace(prefix, "postgresql+asyncpg://", 1)
        return v

    redis_url: str = os.getenv("REDIS_DEVICE_URL")
    rabbitmq_url: str = os.getenv("RABBITMQ_URL")


settings = Settings()
