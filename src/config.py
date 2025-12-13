# src/config.py
"""
Centralized configuration module.

Loads environment variables and provides configuration settings
for the application.
"""

# imports built-in modules
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# imports third-party modules
from dotenv import load_dotenv

# Basic logger to avoid circular import with src.utils.logger
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    # Google Gemini API
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")

    # Gemini Model Configuration
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    GEMINI_TEMPERATURE: float = float(os.getenv("GEMINI_TEMPERATURE") or 1.0)
    GEMINI_TOP_P: float = float(os.getenv("GEMINI_TOP_P") or 0.95)
    GEMINI_TOP_K: int = int(os.getenv("GEMINI_TOP_K") or 64)
    GEMINI_MAX_OUTPUT_TOKENS: int = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS") or 8192)

    # File Upload
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB") or 20)
    UPLOAD_TIMEOUT: int = int(os.getenv("UPLOAD_TIMEOUT") or 180)

    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent.resolve()
    UPLOAD_DIR: Path = BASE_DIR / "upload"
    LOGS_DIR: Path = BASE_DIR / "logs"
    SUMMARY_DIR: Path = BASE_DIR / "summary"

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration.

        Returns
        -------
        bool
            True if all required configuration is present.

        Raises
        ------
        SystemExit
            If required configuration is missing.
        """
        errors = []

        if not cls.GOOGLE_API_KEY:
            errors.append("GOOGLE_API_KEY environment variable not set")

        if errors:
            for error in errors:
                logger.error(f"❌ Configuration Error: {error}")
            return False

        return True

    @classmethod
    def validate_or_exit(cls) -> None:
        """Validate configuration and exit if invalid."""
        if not cls.validate():
            sys.exit(1)


# Create a singleton instance for easy access
config = Config()
