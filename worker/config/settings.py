from pydantic_settings import BaseSettings, SettingsConfigDict


class SettingsEnv(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
    )
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    DATABASE_URL: str
    PAYMENT_PROCESSOR_DEFAULT: str
    PAYMENT_PROCESSOR_FALLBACK: str


settings = SettingsEnv()
