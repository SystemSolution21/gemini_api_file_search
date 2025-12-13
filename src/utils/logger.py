# src/utils/logger.py
"""
Logging utilities.
Provides centralized logging configuration for the application.
"""

# Import built-in modules
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

# Import custom modules
from src.config import config


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    console_output: bool = True,
) -> logging.Logger:
    """Set up a logger with file and/or console handlers.

    Parameters
    ----------
    name : str
        Logger name (typically __name__ of the calling module).
    log_file : Optional[str]
        Log file name. If None, only console logging is enabled.
    level : int
        Logging level (default: logging.INFO).
    console_output : bool
        Whether to also output to console (default: True).

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Add file handler if log_file is specified
    if log_file:
        # Ensure logs directory exists
        logs_dir = Path(config.LOGS_DIR)
        logs_dir.mkdir(exist_ok=True)

        log_path = logs_dir / log_file
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Add console handler if requested
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def get_app_logger() -> logging.Logger:
    """Get the main application logger.

    Returns
    -------
    logging.Logger
        The main application logger with file and console output.
    """
    today: str = datetime.now().strftime(format="%Y-%m-%d")
    return setup_logger(name="gemini_file_search", log_file=f"app_{today}.log")
