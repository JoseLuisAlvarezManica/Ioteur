from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    LOG_LEVEL: str
    MONGO_NOTIFICATIONS_URL: str
    MONGO_NOTIFICATIONS_DB: str
    RABBITMQ_URL: str

    EMAILJS_URL: str = "https://api.emailjs.com/api/v1.0/email/send"
    EMAILJS_SERVICE_ID: str
    EMAILJS_TEMPLATE_ID: str
    EMAILJS_PUBLIC_KEY: str
    EMAILJS_PRIVATE_KEY: str


settings = Settings()
