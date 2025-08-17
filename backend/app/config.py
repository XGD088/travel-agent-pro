from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


_DOTENV_PATH = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """Application runtime settings loaded from environment and .env.

    This centralizes configuration to avoid reading environment variables
    across services and ensures consistent values during hot reloads.
    """

    # Provider API keys
    DASHSCOPE_API_KEY: str | None = None
    AMAP_API_KEY: str | None = None
    QWEATHER_API_KEY: str | None = None

    # Optional QWeather custom host/JWT
    QWEATHER_API_HOST: str | None = None
    QWEATHER_JWT: str | None = None

    # Vector DB / Chroma
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001

    # General
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=_DOTENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


