"""配置管理 - 使用 Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """应用配置."""

    # AI Provider Keys
    kimi_api_key: str | None = Field(default=None, alias="KIMI_API_KEY")
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")

    # API Server
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_key: str | None = Field(default=None, alias="API_KEY")

    # Discord
    discord_token: str | None = Field(default=None, alias="DISCORD_TOKEN")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


# 全局配置实例
settings = Settings()