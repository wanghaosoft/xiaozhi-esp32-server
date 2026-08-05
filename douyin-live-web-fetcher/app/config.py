from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    app_name: str = Field(default="douyin-live-brain", alias="LIVE_BRAIN_APP_NAME")
    env: str = Field(default="dev", alias="LIVE_BRAIN_ENV")
    host: str = Field(default="0.0.0.0", alias="LIVE_BRAIN_HOST")
    port: int = Field(default=8090, alias="LIVE_BRAIN_PORT")
    database_url: str = Field(default="sqlite:///./data/live_brain.db", alias="LIVE_BRAIN_DATABASE_URL")
    settings_key: str = Field(default="live_brain_settings", alias="LIVE_BRAIN_SETTINGS_KEY")
    xiaozhi_base_url: str = Field(default="http://127.0.0.1:8002/xiaozhi", alias="LIVE_BRAIN_XIAOZHI_BASE_URL")
    xiaozhi_secret: str = Field(default="", alias="LIVE_BRAIN_XIAOZHI_SECRET")
    xiaozhi_timeout_seconds: float = Field(default=12.0, alias="LIVE_BRAIN_XIAOZHI_TIMEOUT_SECONDS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = AppSettings()