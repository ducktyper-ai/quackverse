# src/quackcore/integrations/google/config.py
"""
Configuration management for Google integrations.

This module provides configuration validation and loading for
Google service integrations, with shared settings for authentication
and service-specific configurations.
"""

import logging
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator

from quackcore.integrations.core.base import BaseConfigProvider


class GoogleBaseConfig(BaseModel):
    """Base configuration model for Google services."""

    client_secrets_file: str = Field(
        ..., description="Path to Google API client secrets file"
    )
    credentials_file: str = Field(
        ..., description="Path where credentials should be stored"
    )

    @field_validator("client_secrets_file")
    @classmethod
    def validate_client_secrets_file(cls, v: str) -> str:
        """Validate that the client secrets path is not empty."""
        if not v or not v.strip():
            raise ValueError("Client secrets file path cannot be empty")
        return v

    @field_validator("credentials_file")
    @classmethod
    def validate_credentials_file(cls, v: str) -> str:
        """Validate that the credentials path is not empty."""
        if not v or not v.strip():
            raise ValueError("Credentials file path cannot be empty")
        return v


class GoogleDriveConfig(GoogleBaseConfig):
    """Configuration model for Google Drive integration."""

    shared_folder_id: str | None = Field(
        None, description="ID of the shared folder for uploads"
    )
    team_drive_id: str | None = Field(
        None, description="Team Drive ID for shared access"
    )
    default_share_access: str = Field(
        "reader", description="Default access level for shared files"
    )
    public_sharing: bool = Field(
        True, description="Whether to enable public sharing of files"
    )


class GoogleMailConfig(GoogleBaseConfig):
    """Configuration model for Google Mail integration."""

    gmail_labels: list[str] = Field(
        default_factory=list, description="Labels to filter emails"
    )
    gmail_days_back: int = Field(
        default=7, description="Number of days to look back for emails"
    )
    gmail_user_id: str = Field(default="me", description="User ID to use for Gmail API")


class GoogleConfigProvider(BaseConfigProvider):
    """Configuration provider for Google integrations."""

    ENV_PREFIX = "QUACK_GOOGLE_"
    DEFAULT_CONFIG_LOCATIONS = [
        "./config/google_config.yaml",
        "./config/quack_config.yaml",
        "./quack_config.yaml",
        "~/.quack/config.yaml",
    ]

    def __init__(self, service: str = "drive", log_level: int = logging.INFO) -> None:
        """
        Initialize the Google configuration provider.

        Args:
            service: Google service name (e.g., 'drive', 'mail')
            log_level: Logging level
        """
        super().__init__(log_level)
        self.service = service.lower()
        self._config_models = {
            "drive": GoogleDriveConfig,
            "mail": GoogleMailConfig,
        }

    @property
    def name(self) -> str:
        """Get the name of the configuration provider."""
        return f"Google{self.service.capitalize()}"

    def _extract_config(self, config_data: dict[str, Any]) -> dict[str, Any]:
        """
        Extract Google service configuration from the full config data.

        Args:
            config_data: Full configuration data

        Returns:
            dict[str, Any]: Google service-specific configuration
        """
        # Look for google_<service> section first
        service_key = f"google_{self.service}"
        if service_key in config_data:
            return config_data[service_key]

        # If not found, look for general google section
        google_config = config_data.get("google", {})
        service_config = google_config.get(self.service, {})

        # If service config exists as a subsection, merge it with google config
        if service_config and isinstance(service_config, dict):
            # Copy shared Google config
            merged_config = {
                k: v
                for k, v in google_config.items()
                if k != self.service and k not in ["mail", "drive"]
            }
            # Override with service-specific config
            merged_config.update(service_config)
            return merged_config

        # If it's not a nested config, just return the google section
        return google_config

    def validate_config(self, config: dict[str, Any]) -> bool:
        """
        Validate Google service configuration using Pydantic models.

        Args:
            config: Configuration data to validate

        Returns:
            bool: True if configuration is valid
        """
        try:
            config_model = self._config_models.get(self.service, GoogleBaseConfig)

            # Call the constructor with **config to expand it as keyword arguments
            # This ensures the mock's side effect is triggered in tests
            config_model(**config)
            return True
        except ValidationError as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error during configuration validation: {e}")
            return False

    def get_default_config(self) -> dict[str, Any]:
        """
        Get default configuration values for Google services.

        Returns:
            dict[str, Any]: Default configuration values
        """
        base_config = {
            "client_secrets_file": "config/google_client_secret.json",
            "credentials_file": "config/google_credentials.json",
        }

        if self.service == "drive":
            return {
                **base_config,
                "shared_folder_id": None,
                "team_drive_id": None,
                "default_share_access": "reader",
                "public_sharing": True,
            }
        elif self.service == "mail":
            return {
                **base_config,
                "gmail_labels": [],
                "gmail_days_back": 7,
                "gmail_user_id": "me",
            }

        return base_config

    def resolve_config_paths(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Resolve relative paths in configuration to absolute paths.

        Args:
            config: Configuration with potentially relative paths

        Returns:
            dict[str, Any]: Configuration with resolved paths
        """
        from quackcore.paths.resolver import resolve_project_path  # Direct import

        resolved_config = config.copy()

        # Resolve paths
        for key in ["client_secrets_file", "credentials_file"]:
            if key in resolved_config and resolved_config[key]:
                try:
                    resolved_path = resolve_project_path(
                        resolved_config[key]
                    )  # Direct call
                    resolved_config[key] = str(resolved_path)
                except Exception as e:
                    self.logger.warning(f"Could not resolve path for {key}: {e}")

        return resolved_config
