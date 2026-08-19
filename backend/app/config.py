"""
Application configuration using pydantic-settings.
Loads environment variables from .env file.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- Application ---
    APP_NAME: str = "AI-Powered UI Consistency Checker"
    DEBUG: bool = False

    # --- AI ---
    GEMINI_API_KEY: str = ""

    # --- MongoDB (optional) ---
    MONGODB_URI: Optional[str] = None
    MONGODB_DB_NAME: str = "ui_consistency_checker"

    # --- CORS ---
    FRONTEND_URL: str = "http://localhost:5173"

    # --- File Upload ---
    MAX_FILE_SIZE_MB: int = 10
    MAX_SCREENSHOTS: int = 20
    MIN_SCREENSHOTS: int = 2
    ALLOWED_IMAGE_TYPES: list[str] = ["image/png", "image/jpeg", "image/jpg", "image/webp"]

    # --- Playwright ---
    PLAYWRIGHT_TIMEOUT_MS: int = 30000
    MAX_PAGES_TO_CRAWL: int = 5

    # --- Tolerance Thresholds (for consistency engine) ---
    # Color difference (deltaE): below IGNORE is ok, above ISSUE is an issue, between is warning
    COLOR_TOLERANCE_IGNORE: float = 5.0
    COLOR_TOLERANCE_ISSUE: float = 15.0
    # Size difference (px): below IGNORE is ok, above ISSUE is an issue, between is warning
    SIZE_TOLERANCE_IGNORE: float = 2.0
    SIZE_TOLERANCE_ISSUE: float = 6.0
    # Border radius (px)
    RADIUS_TOLERANCE_IGNORE: float = 2.0
    RADIUS_TOLERANCE_ISSUE: float = 6.0
    # Spacing (px)
    SPACING_TOLERANCE_IGNORE: float = 4.0
    SPACING_TOLERANCE_ISSUE: float = 10.0

    # --- Score Weights ---
    SCORE_WEIGHTS: dict[str, float] = {
        "buttons": 0.15,
        "typography": 0.15,
        "spacing": 0.12,
        "colors": 0.15,
        "cards": 0.10,
        "navbar": 0.10,
        "forms": 0.10,
        "responsive": 0.13,
    }

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Singleton settings instance
settings = Settings()
