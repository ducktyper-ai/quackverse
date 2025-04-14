# src/quackcore/config/models.py
"""
Configuration models for QuackCore.

This module provides Pydantic models for configuration management,
with support for validation, defaults, and merging of configurations.
"""

from typing import Any, ClassVar, TypeVar

from pydantic import BaseModel, Field, field_validator

from quackcore.paths import normalize_path

T = TypeVar("T")  # Generic type for flexible typing


class LoggingConfig(BaseModel):
    """Configuration for logging."""

    VALID_LEVELS: ClassVar[list[str]] = [
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ]

    level: str = Field(default="INFO", description="Logging level")
    file: str | None = Field(default=None, description="Log file path")
    console: bool = Field(default=True, description="Log to console")

    @field_validator("level", mode="before")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate and normalize logging level."""
        level_name = v.upper()
        if level_name not in cls.VALID_LEVELS:
            return "INFO"
        return level_name

    @field_validator("file", mode="before")
    @classmethod
    def normalize_file(cls, v: str | None) -> str | None:
        """Normalize the log file path (if provided)."""
        if v is None:
            return None
        return normalize_path(v)


class PathsConfig(BaseModel):
    """Configuration for file paths."""

    base_dir: str = Field(default="./", description="Base directory")
    output_dir: str = Field(default="./output", description="Output directory")
    assets_dir: str = Field(default="./assets", description="Assets directory")
    data_dir: str = Field(default="./data", description="Data directory")
    temp_dir: str = Field(default="./temp", description="Temporary directory")

    # Normalize all path fields using a field validator.
    @field_validator("*", mode="before")
    @classmethod
    def normalize_paths(cls, v: str) -> str:
        return normalize_path(v)


class GoogleConfig(BaseModel):
    """Configuration for Google integrations."""

    client_secrets_file: str | None = Field(
        default=None, description="Path to client secrets file for OAuth"
    )
    credentials_file: str | None = Field(
        default=None, description="Path to credentials file for OAuth"
    )
    shared_folder_id: str | None = Field(
        default=None, description="Google Drive shared folder ID"
    )
    gmail_labels: list[str] = Field(
        default_factory=list, description="Gmail labels to filter"
    )
    gmail_days_back: int = Field(
        default=1, description="Number of days back for Gmail queries"
    )

    @field_validator("client_secrets_file", "credentials_file", mode="before")
    @classmethod
    def normalize_google_paths(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return normalize_path(v)


class NotionConfig(BaseModel):
    """Configuration for Notion integration."""

    api_key: str | None = Field(default=None, description="Notion API key")
    database_ids: dict[str, str] = Field(
        default_factory=dict, description="Mapping of database names to IDs"
    )


class IntegrationsConfig(BaseModel):
    """Configuration for third-party integrations."""

    google: GoogleConfig = Field(
        default_factory=GoogleConfig, description="Google integration settings"
    )
    notion: NotionConfig = Field(
        default_factory=NotionConfig, description="Notion integration settings"
    )


class GeneralConfig(BaseModel):
    """General configuration settings."""

    project_name: str = Field(default="QuackCore", description="Name of the project")
    environment: str = Field(
        default="development",
        description="Environment (development, test, production)",
    )
    debug: bool = Field(default=False, description="Debug mode")
    verbose: bool = Field(default=False, description="Verbose output")


class PluginsConfig(BaseModel):
    """Configuration for plugins."""

    enabled: list[str] = Field(
        default_factory=list, description="List of enabled plugins"
    )
    disabled: list[str] = Field(
        default_factory=list, description="List of disabled plugins"
    )
    paths: list[str] = Field(
        default_factory=list, description="Additional plugin search paths"
    )

    @field_validator("paths", mode="before")
    @classmethod
    def normalize_plugin_paths(cls, v: list[str] | str) -> list[str]:
        # If a single string is provided, wrap it in a list
        if isinstance(v, str):
            v = [v]
        return [normalize_path(path_str) for path_str in v]


class QuackConfig(BaseModel):
    """Main configuration for QuackCore."""

    general: GeneralConfig = Field(
        default_factory=GeneralConfig, description="General settings"
    )
    paths: PathsConfig = Field(default_factory=PathsConfig, description="Path settings")
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig, description="Logging settings"
    )
    integrations: IntegrationsConfig = Field(
        default_factory=IntegrationsConfig, description="Integration settings"
    )
    plugins: PluginsConfig = Field(
        default_factory=PluginsConfig, description="Plugin settings"
    )
    custom: dict[str, Any] = Field(
        default_factory=dict, description="Custom configuration settings"
    )

    def setup_logging(self) -> None:
        """Set up logging based on configuration."""
        self.logging.setup_logging()

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the configuration to a dictionary.

        Returns:
            dict[str, Any]: Dictionary representation of the configuration
        """
        return self.model_dump()

    def get_plugin_enabled(self, plugin_name: str) -> bool:
        """
        Check if a plugin is enabled.

        Args:
            plugin_name: Name of the plugin

        Returns:
            bool: True if the plugin is enabled
        """
        if plugin_name in self.plugins.disabled:
            return False
        if self.plugins.enabled and plugin_name not in self.plugins.enabled:
            return False
        return True

    def get_custom(self, key: str, default: T = None) -> T:
        """
        Get a custom configuration value.

        Args:
            key: The configuration key
            default: Default value if the key doesn't exist

        Returns:
            The configuration value
        """
        return self.custom.get(key, default)
