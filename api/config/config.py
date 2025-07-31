from pydantic_settings import BaseSettings, SettingsConfigDict


class SettingsEnv(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
    REDIS_URL: str
    DATABASE_URL: str
    PAYMENT_PROCESSOR_DEFAULT: str
    PAYMENT_PROCESSOR_FALLBACK: str


settings = SettingsEnv()
