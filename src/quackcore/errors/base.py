# src/quackcore/errors/base.py
"""
Base error classes for QuackCore.

This module defines the base exception hierarchy for all errors in the QuackCore
ecosystem, providing consistent error handling and detailed diagnostic information.
"""

import builtins
from functools import wraps
from pathlib import Path
from typing import Callable, TypeVar

T = TypeVar("T")  # Generic return type for functions
R = TypeVar("R")  # Generic return type for wrapped functions


class QuackError(Exception):
    """Base exception for all errors in the QuackCore ecosystem."""

    def __init__(
        self,
        message: str,
        context: dict[str, object] | None = None,
        original_error: Exception | None = None,
    ) -> None:
        """
        Initialize a QuackError.

        Args:
            message: The error message
            context: Additional context information (optional)
            original_error: The original exception that caused this error (optional)
        """
        self.context = context or {}
        self.original_error = original_error

        # Create a formatted message with context information
        formatted_message = message
        if context:
            context_str = ", ".join(f"{k}={v!r}" for k, v in context.items())
            formatted_message = f"{message} (context: {context_str})"

        super().__init__(formatted_message)


class QuackIOError(QuackError):
    """Base exception for all input/output related errors."""

    def __init__(
        self,
        message: str,
        path: str | Path | None = None,
        original_error: Exception | None = None,
    ) -> None:
        """
        Initialize an IO error.

        Args:
            message: The error message
            path: The file or directory path related to the error (optional)
            original_error: The original exception that caused this error (optional)
        """
        context = {}
        if path is not None:
            context["path"] = str(path)

        super().__init__(message, context, original_error)
        self.path = str(path) if path else None


class QuackFileNotFoundError(QuackIOError):
    """Raised when a file or directory does not exist."""

    def __init__(
        self,
        path: str | Path,
        message: str | None = None,
        original_error: Exception | None = None,
    ) -> None:
        """
        Initialize a file not found error.

        Args:
            path: The file or directory path that wasn't found
            message: A custom error message (optional)
            original_error: The original exception that caused this error (optional)
        """
        if message is None:
            message = f"File or directory not found: {path}"

        super().__init__(message, path, original_error)


class QuackPermissionError(QuackIOError):
    """Raised when permission is denied for a file operation."""

    def __init__(
        self,
        path: str | Path,
        operation: str,
        message: str | None = None,
        original_error: Exception | None = None,
    ) -> None:
        """
        Initialize a permission error.

        Args:
            path: The file or directory path for which permission was denied
            operation: The operation that was attempted (e.g., "read", "write")
            message: A custom error message (optional)
            original_error: The original exception that caused this error (optional)
        """
        if message is None:
            message = f"Permission denied for {operation} operation on {path}"

        context = {"path": str(path), "operation": operation}
        super().__init__(message, path, original_error)
        self.operation = operation


class QuackFileExistsError(QuackIOError):
    """Raised when trying to create a file or directory that already exists."""

    def __init__(
        self,
        path: str | Path,
        message: str | None = None,
        original_error: Exception | None = None,
    ) -> None:
        """
        Initialize a file exists error.

        Args:
            path: The file or directory path that already exists
            message: A custom error message (optional)
            original_error: The original exception that caused this error (optional)
        """
        if message is None:
            message = f"File or directory already exists: {path}"

        super().__init__(message, path, original_error)


class QuackValidationError(QuackError):
    """Raised when data validation fails."""

    def __init__(
        self,
        message: str,
        path: str | Path | None = None,
        errors: dict[str, list[str]] | None = None,
        original_error: Exception | None = None,
    ) -> None:
        """
        Initialize a validation error.

        Args:
            message: The error message
            path: The file or directory path related to the error (optional)
            errors: Detailed validation errors (optional)
            original_error: The original exception that caused this error (optional)
        """
        context = {}
        if path is not None:
            context["path"] = str(path)
        if errors is not None:
            context["errors"] = errors

        super().__init__(message, context, original_error)
        self.path = str(path) if path else None
        self.errors = errors or {}


class QuackFormatError(QuackIOError):
    """Raised when there's an error in file format or parsing."""

    def __init__(
        self,
        path: str | Path,
        format_name: str,
        message: str | None = None,
        original_error: Exception | None = None,
    ) -> None:
        """
        Initialize a format error.

        Args:
            path: The file path with the format error
            format_name: The name of the format (e.g., "JSON", "YAML")
            message: A custom error message (optional)
            original_error: The original exception that caused this error (optional)
        """
        if message is None:
            message = f"Invalid {format_name} format in {path}"

        context = {"path": str(path), "format": format_name}
        super().__init__(message, path, original_error)
        self.format_name = format_name


class QuackConfigurationError(QuackError):
    """Raised when there's an error in configuration."""

    def __init__(
        self,
        message: str,
        config_path: str | Path | None = None,
        config_key: str | None = None,
        original_error: Exception | None = None,
    ) -> None:
        """
        Initialize a configuration error.

        Args:
            message: The error message
            config_path: The configuration file path (optional)
            config_key: The specific configuration key with the error (optional)
            original_error: The original exception that caused this error (optional)
        """
        context = {}
        if config_path is not None:
            context["config_path"] = str(config_path)
        if config_key is not None:
            context["config_key"] = config_key

        super().__init__(message, context, original_error)
        self.config_path = str(config_path) if config_path else None
        self.config_key = config_key


class QuackPluginError(QuackError):
    """Raised when there's an error with a plugin."""

    def __init__(
        self,
        message: str,
        plugin_name: str | None = None,
        plugin_path: str | Path | None = None,
        original_error: Exception | None = None,
    ) -> None:
        """
        Initialize a plugin error.

        Args:
            message: The error message
            plugin_name: The name of the plugin (optional)
            plugin_path: The path to the plugin module or file (optional)
            original_error: The original exception that caused this error (optional)
        """
        context = {}
        if plugin_name is not None:
            context["plugin_name"] = plugin_name
        if plugin_path is not None:
            context["plugin_path"] = str(plugin_path)

        super().__init__(message, context, original_error)
        self.plugin_name = plugin_name
        self.plugin_path = str(plugin_path) if plugin_path else None


class QuackAuthenticationError(QuackError):
    """Raised when there's an authentication error."""

    def __init__(
        self,
        message: str,
        service: str | None = None,
        credentials_path: str | Path | None = None,
        original_error: Exception | None = None,
    ) -> None:
        """
        Initialize an authentication error.

        Args:
            message: The error message
            service: The service name (e.g., "Google Drive", "Gmail") (optional)
            credentials_path: The path to the credentials file (optional)
            original_error: The original exception that caused this error (optional)
        """
        context = {}
        if service is not None:
            context["service"] = service
        if credentials_path is not None:
            context["credentials_path"] = str(credentials_path)

        super().__init__(message, context, original_error)
        self.service = service
        self.credentials_path = str(credentials_path) if credentials_path else None


def wrap_io_errors(func: Callable[..., R]) -> Callable[..., R]:
    """
    Decorator to wrap standard IO exceptions with QuackCore's custom exceptions.

    Args:
        func: Function to wrap

    Returns:
        A wrapped function that converts standard exceptions to QuackCore exceptions
    """

    @wraps(func)
    def wrapper(*args: object, **kwargs: object) -> R:
        try:
            return func(*args, **kwargs)
        except builtins.ValueError as e:
            raise QuackValidationError(str(e), original_error=e) from e
        except builtins.FileNotFoundError as e:
            path = getattr(e, "filename", None)
            raise QuackFileNotFoundError(path or "unknown", original_error=e) from e
        except builtins.PermissionError as e:
            path = getattr(e, "filename", None)
            operation = "access"
            raise QuackPermissionError(
                path or "unknown", operation, original_error=e
            ) from e
        except builtins.FileExistsError as e:
            path = getattr(e, "filename", None)
            raise QuackFileExistsError(path or "unknown", original_error=e) from e
        except builtins.IsADirectoryError as e:
            path = getattr(e, "filename", None)
            raise QuackIOError(
                f"Path is a directory: {path}", path, original_error=e
            ) from e
        except builtins.NotADirectoryError as e:
            path = getattr(e, "filename", None)
            raise QuackIOError(
                f"Path is not a directory: {path}", path, original_error=e
            ) from e
        except OSError as e:
            # Handle other OS errors
            path = getattr(e, "filename", None)
            raise QuackIOError(str(e), path, original_error=e) from e
        except Exception as e:
            raise QuackError(str(e), original_error=e) from e

    return wrapper
