from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    LOG_LEVEL: str
    MONGO_REGISTER_URL: str
    MONGO_REGISTER_DB: str
    RABBITMQ_URL: str


settings = Settings()
