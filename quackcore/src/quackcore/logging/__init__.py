# quackcore/src/quackcore/logging/__init__.py
"""
Centralized logging module for quackcore.

This package provides a standardized approach to logging throughout quackcore.
It exposes the default logger, a module‐specific logger creator, and other
configuration constants.
"""

from .config import LOG_LEVELS, LogLevel, configure_logger

# Re-export get_logger from our dedicated logger module.
from .logger import get_logger

__all__ = ["get_logger", "configure_logger", "LOG_LEVELS", "LogLevel"]

# Optionally, you can still create a module-level default logger if desired:
default_logger = configure_logger("quackcore")
