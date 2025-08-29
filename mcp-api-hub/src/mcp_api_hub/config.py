from __future__ import annotations

from pydantic import BaseSettings, Field, AnyHttpUrl
from typing import Optional


class Settings(BaseSettings):
    # Global defaults
    DEFAULT_TIMEOUT: int = Field(60, description="Default HTTP timeout in seconds")
    RETRY_MAX: int = Field(3, description="Max retries for transient errors")

    # BPM / Firco Flask service
    BPM_URL: Optional[AnyHttpUrl] = Field(
        default=None, description="Base URL for Flask API (e.g., http://localhost:8088)"
    )
    BPM_USERNAME: Optional[str] = Field(default=None, description="Optional username for BPM system")
    BPM_PASSWORD: Optional[str] = Field(default=None, description="Optional password for BPM system")

    # Debug
    LOG_LEVEL: str = Field("INFO", description="Logging level: DEBUG, INFO, WARNING, ERROR")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
