from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    LOG_LEVEL: str = "INFO"

    RABBITMQ_URL: str

    REDIS_DEVICE_URL: str

    DEVICE_SERVICE_URL: str = "http://device-service:8003"
    REGISTER_SERVICE_URL: str = "http://register-service:8005"
    TELEMETRY_SERVICE_URL: str = "http://telemetry-service:8006"


settings = Settings()
