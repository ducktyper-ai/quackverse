"""
Centralized logging module for quackcore.

This module provides a standardized approach to logging across all quackcore modules,
with support for Teaching Mode integration.

Example:
    Basic usage:
        from quackcore.logging import logger

        logger.info("Standard log message")

    Module-specific logger:
        from quackcore.logging import get_logger

        logger = get_logger(__name__)
        logger.debug("Module-specific debug info")

    Teaching mode log (will be formatted specially when Teaching Mode is enabled):
        logger.info("[Teaching Mode] This explains how the algorithm works")
"""

from .config import configure_logger, LOG_LEVELS, logging

__all__ = ["logger", "get_logger", "LOG_LEVELS"]

# Default logger for general quackcore usage
logger = configure_logger("quackcore")


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger for a specific module.

    Args:
        name: The name for the logger, typically __name__

    Returns:
        A configured logger instance
    """
    return configure_logger(name)