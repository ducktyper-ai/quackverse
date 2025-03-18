# src/quackcore/integrations/results.py
"""
Result models for integration operations.

This module provides standardized result classes for various integration
operations, enhancing error handling and return values.
"""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")  # Generic type for result content


class IntegrationResult(BaseModel, Generic[T]):
    """Base result for integration operations."""

    success: bool = Field(
        default=True,
        description="Whether the operation was successful",
    )

    message: str | None = Field(
        default=None,
        description="Additional message about the operation",
    )

    error: str | None = Field(
        default=None,
        description="Error message if operation failed",
    )

    content: T | None = Field(
        default=None,
        description="Result content if operation was successful",
    )

    @classmethod
    def success_result(cls, content: T | None = None, message: str | None = None) -> "IntegrationResult[T]":
        """
        Create a successful result.

        Args:
            content: Result content
            message: Optional success message

        Returns:
            IntegrationResult: Successful result
        """
        return cls(
            success=True,
            content=content,
            message=message,
            error=None,
        )

    @classmethod
    def error_result(cls, error: str, message: str | None = None) -> "IntegrationResult[T]":
        """
        Create an error result.

        Args:
            error: Error message
            message: Optional additional message

        Returns:
            IntegrationResult: Error result
        """
        return cls(
            success=False,
            content=None,
            message=message,
            error=error,
        )


class AuthResult(IntegrationResult[dict]):
    """Result for authentication operations."""

    token: str | None = Field(
        default=None,
        description="Authentication token if available",
    )

    expiry: int | None = Field(
        default=None,
        description="Token expiry timestamp",
    )

    credentials_path: str | None = Field(
        default=None,
        description="Path where credentials are stored",
    )

    @classmethod
    def success_result(
        cls,
        content: dict | None = None,
        message: str | None = None,
        token: str | None = None,
        expiry: int | None = None,
        credentials_path: str | None = None,
    ) -> "AuthResult":
        """
        Create a successful authentication result.

        Args:
            content: Result content
            message: Optional success message
            token: Authentication token
            expiry: Token expiry timestamp
            credentials_path: Path where credentials are stored

        Returns:
            AuthResult: Successful authentication result
        """
        return cls(
            success=True,
            content=content,
            message=message,
            error=None,
            token=token,
            expiry=expiry,
            credentials_path=credentials_path,
        )


class ConfigResult(IntegrationResult[dict]):
    """Result for configuration operations."""

    config_path: str | None = Field(
        default=None,
        description="Path to the configuration file",
    )

    validation_errors: list[str] | None = Field(
        default=None,
        description="Validation errors if any",
    )

    @classmethod
    def success_result(
        cls,
        content: dict | None = None,
        message: str | None = None,
        config_path: str | None = None,
    ) -> "ConfigResult":
        """
        Create a successful configuration result.

        Args:
            content: Configuration data
            message: Optional success message
            config_path: Path to the configuration file

        Returns:
            ConfigResult: Successful configuration result
        """
        return cls(
            success=True,
            content=content,
            message=message,
            error=None,
            config_path=config_path,
        )

    @classmethod
    def error_result(
        cls,
        error: str,
        message: str | None = None,
        validation_errors: list[str] | None = None,
    ) -> "ConfigResult":
        """
        Create an error configuration result.

        Args:
            error: Error message
            message: Optional additional message
            validation_errors: Validation errors if any

        Returns:
            ConfigResult: Error configuration result
        """
        return cls(
            success=False,
            content=None,
            message=message,
            error=error,
            validation_errors=validation_errors,
        )