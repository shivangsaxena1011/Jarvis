"""
SHIVANI Configuration System
Central configuration loaded from environment variables and .env files.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from core.config.app_dirs import AppDirectories, get_app_dirs


class Settings(BaseSettings):
    # Application runtime
    ENV: Literal["development", "production", "testing"] = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "127.0.0.1"

    # AI Model Provider
    LLM_PROVIDER: Literal["gemini", "openai", "local", "mock", "ollama", "fallback", "chain"] = "mock"
    LLM_MODEL: str = "gemini-2.5-flash"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"

    # Security & Permissions
    SECURITY_POLICY: Literal["strict", "standard", "lenient"] = "strict"
    AUDIT_LOG_PATH: str = "audit.jsonl"
    APPROVAL_TIMEOUT_SECONDS: int = 120

    # System & Execution Limits
    DEFAULT_TOOL_TIMEOUT: float = 30.0
    MAX_CONCURRENT_TASKS: int = 5
    SCREENSHOT_DIR: str = "screenshots"

    # Desktop Automation Limits
    DESKTOP_APP_TIMEOUT: float = 15.0
    DESKTOP_WINDOW_TIMEOUT: float = 3.0
    DESKTOP_INPUT_TIMEOUT: float = 2.0
    DESKTOP_MAX_RETRIES: int = 3
    DESKTOP_VISION_ENABLED: bool = False

    # Voice Engine & Audio
    VOICE_ENABLED: bool = True
    WAKE_WORD: str = "Shivani"
    STT_PROVIDER: Literal["mock", "whisper", "local"] = "whisper"
    STT_MODEL: str = "tiny"
    TTS_PROVIDER: Literal["mock", "edge_tts", "pyttsx3", "piper"] = "edge_tts"
    TTS_VOICE: str = "hi-IN-SwaraNeural"
    TTS_RATE: str = "+0%"
    CONFIDENCE_THRESHOLD: float = 0.65
    AUDIO_OUTPUT_DIR: str = "audio_cache"

    # Browser
    BROWSER_HEADLESS: bool = False
    PREFERRED_BROWSER: Literal["chromium", "chrome", "brave", "edge"] = "chromium"
    BROWSER_NAVIGATION_TIMEOUT: float = 30.0
    BROWSER_ACTION_TIMEOUT: float = 10.0
    BROWSER_USER_DATA_DIR: str = ""
    BROWSER_DOWNLOAD_DIR: str = "downloads"

    # Productivity Integrations & Workflows (Phase 5)
    AUTHORIZED_PROJECT_ROOTS: list[str] = []
    GITHUB_TOKEN: str = ""
    RESEARCH_OUTPUT_DIR: str = "research"
    RATE_LIMIT_COOLDOWN_SECONDS: float = 0.5

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

    @property
    def download_path(self) -> Path:
        path = Path(self.BROWSER_DOWNLOAD_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def research_path(self) -> Path:
        path = Path(self.RESEARCH_OUTPUT_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Returns singleton settings instance."""
    return Settings()
