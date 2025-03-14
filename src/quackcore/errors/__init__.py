# src/quackcore/errors/__init__.py
"""
Error handling utilities for QuackCore.

This module provides custom exception classes for QuackCore, with helpful context
and error messages for better diagnostics and troubleshooting.
"""

from quackcore.errors.base import (
    QuackAuthenticationError,
    QuackConfigurationError,
    QuackError,
    QuackFileExistsError,
    QuackFileNotFoundError,
    QuackFormatError,
    QuackIOError,
    QuackPermissionError,
    QuackPluginError,
    QuackValidationError,
    wrap_io_errors,
)

__all__ = [
    "QuackError",
    "QuackIOError",
    "QuackFileNotFoundError",
    "QuackPermissionError",
    "QuackFileExistsError",
    "QuackValidationError",
    "QuackFormatError",
    "QuackConfigurationError",
    "QuackPluginError",
    "QuackAuthenticationError",
    "wrap_io_errors",
]
