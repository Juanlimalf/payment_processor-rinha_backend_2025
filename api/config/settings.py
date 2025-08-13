from pydantic_settings import BaseSettings, SettingsConfigDict


class SettingsEnv(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
    )
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    PAYMENT_PROCESSOR_DEFAULT: str = "http://localhost:8001"
    PAYMENT_PROCESSOR_FALLBACK: str = "http://localhost:8002"
    NUM_WORKERS: int = 3
    LOG_LEVEL: str = "INFO"


settings = SettingsEnv()
