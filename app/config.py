from functools import lru_cache
from typing import Literal
from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Auth
    secret_key: str = "super_insecure_default_key"
    algorithm: str = "HS256"

    # Database
    database_url: str = "sqlite:///./local.db"

    # YooKassa
    yookassa_shop_id: str | None = None
    yookassa_secret_key: str | None = None
    yookassa_return_url: HttpUrl = "http://localhost:8000/"

    # Конфигурация Pydantic Settings
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
