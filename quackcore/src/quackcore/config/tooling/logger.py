"""
Logging setup utilities for QuackTools.

This module provides utilities for setting up consistent logging
across different QuackTools.
"""

import logging
import atexit
from quackcore.fs.service import get_service

# Track file handlers for cleanup during exit
_file_handlers = []


def setup_tool_logging(tool_name: str, log_level: str = "INFO") -> None:
    """
    Set up logging for a QuackTool.

    This sets the global log level, adds a console logger and a file logger,
    and ensures log files are cleaned up during tests.

    Args:
        tool_name: The tool name, e.g. 'quackmetadata'
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    fs = get_service()
    level = getattr(logging, log_level.upper(), logging.INFO)

    logs_dir = fs.normalize_path("./logs")
    fs.create_directory(logs_dir, exist_ok=True)
    log_file = fs.join_path(logs_dir, f"{tool_name}.log")

    logger = logging.getLogger()
    logger.setLevel(level)

    # Console handler (prints to screen)
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        ch = logging.StreamHandler()
        ch.setLevel(level)
        logger.addHandler(ch)

    # File handler (saves to file)
    fh = logging.FileHandler(str(log_file))
    fh.setLevel(level)
    logger.addHandler(fh)
    _file_handlers.append(fh)

    @atexit.register
    def _cleanup_handlers() -> None:
        for h in _file_handlers:
            h.close()
            logger.removeHandler(h)


def get_logger(tool_name: str) -> logging.Logger:
    """
    Get a named logger for the given tool.

    Args:
        tool_name: The tool name, e.g. 'quackmetadata'

    Returns:
        A Logger instance configured for the tool
    """
    return logging.getLogger(tool_name)