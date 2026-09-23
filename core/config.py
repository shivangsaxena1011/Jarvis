"""
SHIVANI Configuration System
Central configuration loaded from environment variables and .env files.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application runtime
    ENV: Literal["development", "production", "testing"] = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "127.0.0.1"

    # AI Model Provider
    LLM_PROVIDER: Literal["gemini", "openai", "local", "mock"] = "mock"
    LLM_MODEL: str = "gemini-2.5-flash"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    # Security & Permissions
    SECURITY_POLICY: Literal["strict", "standard", "lenient"] = "strict"
    AUDIT_LOG_PATH: str = "audit.jsonl"
    APPROVAL_TIMEOUT_SECONDS: int = 120

    # System & Execution Limits
    DEFAULT_TOOL_TIMEOUT: float = 30.0
    MAX_CONCURRENT_TASKS: int = 5
    SCREENSHOT_DIR: str = "screenshots"

    # Voice Engine
    VOICE_ENABLED: bool = False
    WAKE_WORD: str = "Shivani"
    STT_PROVIDER: Literal["mock", "whisper", "local"] = "mock"
    TTS_PROVIDER: Literal["mock", "edge_tts", "piper"] = "mock"

    # Browser
    BROWSER_HEADLESS: bool = False
    PREFERRED_BROWSER: Literal["chromium", "chrome", "brave", "edge"] = "chromium"

    # Mobile Bridge
    MOBILE_BRIDGE_HOST: str = "0.0.0.0"
    MOBILE_BRIDGE_PORT: int = 8765
    MOBILE_PAIRING_SECRET: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def is_production(self) -> bool:
        return self.ENV == "production"

    @property
    def screenshot_path(self) -> Path:
        path = Path(self.SCREENSHOT_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Returns singleton settings instance."""
    return Settings()
