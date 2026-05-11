from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    LOG_LEVEL: str = "INFO"

    REDIS_AUTH_URL: str = "redis://redis-auth:6379/0"

    AUTH_SERVICE_URL: str = "http://auth-service:8001"

    PUBLIC_KEY: str

    @field_validator("PUBLIC_KEY", mode="before")
    @classmethod
    def fix_pem_newlines(cls, v: str) -> str:
        return v.replace("\\n", "\n")


settings = Settings()
