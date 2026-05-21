from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    LOG_LEVEL: str = "INFO"

    RABBITMQ_URL: str

    REDIS_DEVICE_URL: str

    DEVICE_SERVICE_URL: str = "http://device-service:8003"
    REGISTER_SERVICE_URL: str = "http://register-service:8005"
    TELEMETRY_SERVICE_URL: str = "http://telemetry-service:8006"
    AUTH_SERVICE_URL: str = "http://auth-service:8001"
    NOTIFICATION_SERVICE_URL: str = "http://notification-service:8004"

    SCHEDULER_INTERVAL_SECONDS: int = 500


settings = Settings()
