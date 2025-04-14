# src/quackcore/logging/config.py
"""
Logger configuration for quackcore.

This module handles the setup and configuration of loggers,
including environment-based configuration and file output options.
"""

import logging
import os
import sys
from enum import Enum
from pathlib import Path
from typing import Any

from .formatter import TeachingAwareFormatter


# Define log levels enum for easy reference
class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# Mapping from string names to logging module constants
LOG_LEVELS = {
    LogLevel.DEBUG: logging.DEBUG,
    LogLevel.INFO: logging.INFO,
    LogLevel.WARNING: logging.WARNING,
    LogLevel.ERROR: logging.ERROR,
    LogLevel.CRITICAL: logging.CRITICAL,
}


def get_log_level() -> int:
    """
    Get the log level from environment variable or default to INFO.

    Returns:
        The log level as a logging module constant
    """
    env_level = os.environ.get("QUACKCORE_LOG_LEVEL", "INFO").upper()
    # Type checking complaint: env_level is a string, not a LogLevel enum
    # We'll convert it or use the default
    log_level = logging.INFO
    try:
        log_level = LOG_LEVELS[LogLevel(env_level)]
    except (ValueError, KeyError):
        # If env_level is not a valid LogLevel, use default
        pass
    return log_level


def configure_logger(
    name: str | None = None,
    level: int | None = None,
    log_file: str | Path | None = None,
    teaching_to_stdout: bool = True,
) -> logging.Logger:
    """
    Configure and return a logger with the specified name.

    This function ensures handlers are only added once per logger instance,
    and supports multiple output destinations.

    Args:
        name: The name for the logger, typically __name__
        level: The logging level (if None, use environment or default)
        log_file: Optional path to a log file
        teaching_to_stdout: If True, quackster logs go to stdout, otherwise stderr

    Returns:
        A configured logger instance
    """
    logger = logging.getLogger(name)

    # Only configure if no handlers exist yet
    if not logger.handlers:
        # Set log level from param, env var, or default
        logger_level = level if level is not None else get_log_level()
        logger.setLevel(logger_level)

        # Console handler (stderr by default)
        console_handler = logging.StreamHandler(
            sys.stdout if teaching_to_stdout else sys.stderr
        )
        console_handler.setFormatter(TeachingAwareFormatter())
        logger.addHandler(console_handler)

        # File handler (optional)
        if log_file:
            file_path = Path(log_file)
            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(file_path)
            file_handler.setFormatter(TeachingAwareFormatter(color_enabled=False))
            logger.addHandler(file_handler)

        # Prevent propagation to root logger to avoid duplicate logs
        logger.propagate = False

    return logger


def log_teaching(logger: Any, message: str, level: str = "INFO") -> None:
    """
    Log a quackster message with appropriate formatting.

    This is a convenience function to consistently format quackster messages.

    Args:
        logger: The logger instance to use
        message: The quackster message to log
        level: The log level to use (default: INFO)
    """
    log_method = getattr(logger, level.lower())
    log_method(f"[Teaching Mode] {message}")
