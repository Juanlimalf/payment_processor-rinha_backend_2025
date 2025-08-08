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


settings = SettingsEnv()
