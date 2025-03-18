# src/quackcore/integrations/base.py
"""
Base classes for QuackCore integrations.

This module provides abstract base classes that integration implementations
can inherit from, providing common functionality and ensuring
consistent behavior.
"""

import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path

from quackcore.errors import QuackConfigurationError, QuackIOError
from quackcore.fs import service as fs
from quackcore.integrations.protocols import (
    AuthProviderProtocol,
    ConfigProviderProtocol,
    IntegrationProtocol,
)
from quackcore.integrations.results import (
    AuthResult,
    ConfigResult,
    IntegrationResult,
)
from quackcore.paths import resolver


class BaseAuthProvider(ABC):
    """Base class for authentication providers."""

    def __init__(
            self,
            credentials_file: str | Path | None = None,
            log_level: int = logging.INFO,
    ) -> None:
        """
        Initialize the base authentication provider.

        Args:
            credentials_file: Path to credentials file
            log_level: Logging level
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.setLevel(log_level)

        self.credentials_file = self._resolve_path(
            credentials_file) if credentials_file else None
        self.authenticated = False

    def _resolve_path(self, file_path: str | Path) -> Path:
        """
        Resolve a path relative to the project root if needed.

        Args:
            file_path: Path to resolve

        Returns:
            Path: Resolved absolute path
        """
        path_obj = Path(file_path)

        # If the path is already absolute, return it unchanged
        if path_obj.is_absolute():
            return path_obj

        # Try to find the project root
        try:
            project_root = resolver.get_project_root()
            return resolver.resolve_project_path(path_obj, project_root)
        except Exception as e:
            self.logger.warning(f"Could not resolve project root: {e}")
            # Fall back to current directory
            return Path.cwd() / path_obj

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the authentication provider."""
        ...

    @abstractmethod
    def authenticate(self) -> AuthResult:
        """
        Authenticate with the external service.

        Returns:
            AuthResult: Result of authentication
        """
        ...

    @abstractmethod
    def refresh_credentials(self) -> AuthResult:
        """
        Refresh authentication credentials if expired.

        Returns:
            AuthResult: Result of refresh operation
        """
        ...

    @abstractmethod
    def get_credentials(self) -> object:
        """
        Get the current authentication credentials.

        Returns:
            object: The authentication credentials
        """
        ...

    def save_credentials(self) -> bool:
        """
        Save the current authentication credentials.

        This is a placeholder implementation that should be overridden
        by subclasses to provide actual credential saving.

        Returns:
            bool: True if saving was successful
        """
        self.logger.warning(
            "save_credentials() not implemented in base class. Override in subclass."
        )
        return False

    def _ensure_credentials_directory(self) -> bool:
        """
        Ensure the directory for credentials exists.

        Returns:
            bool: True if directory exists or was created
        """
        if not self.credentials_file:
            return False

        try:
            credentials_dir = Path(self.credentials_file).parent
            fs.create_directory(credentials_dir, exist_ok=True)
            return True
        except (QuackIOError, Exception) as e:
            self.logger.error(f"Failed to create credentials directory: {e}")
            return False


class BaseConfigProvider(ABC):
    """Base class for configuration providers."""

    DEFAULT_CONFIG_LOCATIONS = [
        "./config/integration_config.yaml",
        "./quack_config.yaml",
        "~/.quack/config.yaml",
    ]

    def __init__(self, log_level: int = logging.INFO) -> None:
        """
        Initialize the base configuration provider.

        Args:
            log_level: Logging level
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.setLevel(log_level)

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the configuration provider."""
        ...

    def load_config(self, config_path: str | Path | None = None) -> ConfigResult:
        """
        Load configuration from a file.

        Args:
            config_path: Path to configuration file

        Returns:
            ConfigResult: Result containing configuration data
        """
        try:
            # Determine config path
            if not config_path:
                config_path = self._find_config_file()
                if not config_path:
                    return ConfigResult.error_result(
                        "Configuration file not found in default locations."
                    )

            path_obj = self._resolve_path(config_path)

            # Check if configuration file exists
            file_info = fs.get_file_info(path_obj)
            if not file_info.success or not file_info.exists:
                self.logger.warning(f"Configuration file not found: {path_obj}")
                return ConfigResult.error_result(
                    f"Configuration file not found: {path_obj}"
                )

            # Read configuration file
            yaml_result = fs.read_yaml(path_obj)
            if not yaml_result.success:
                return ConfigResult.error_result(
                    f"Failed to read YAML configuration: {yaml_result.error}"
                )

            # Extract integration-specific configuration
            config_data = yaml_result.data
            integration_config = self._extract_config(config_data)

            # Validate configuration
            if not self.validate_config(integration_config):
                return ConfigResult.error_result(
                    "Invalid configuration",
                    validation_errors=["Configuration validation failed"]
                )

            return ConfigResult.success_result(
                content=integration_config,
                message="Successfully loaded configuration",
                config_path=str(path_obj),
            )

        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            return ConfigResult.error_result(
                f"Failed to load configuration: {str(e)}"
            )

    def _extract_config(self, config_data: dict) -> dict:
        """
        Extract integration-specific configuration from the full config data.

        Args:
            config_data: Full configuration data

        Returns:
            dict: Integration-specific configuration
        """
        # Default implementation - override in subclass
        # to extract integration-specific section
        integration_name = self.name.lower().replace(" ", "_")
        return config_data.get(integration_name, {})

    def _find_config_file(self) -> Path | None:
        """
        Find a configuration file in standard locations.

        Returns:
            Path | None: Path to the configuration file if found, None otherwise
        """
        # Check environment variable first
        env_var = f"QUACK_{self.name.upper()}_CONFIG"
        if config_path := os.environ.get(env_var):
            path = Path(config_path).expanduser()
            if path.exists():
                return path

        # Check default locations
        for location in self.DEFAULT_CONFIG_LOCATIONS:
            path = Path(location).expanduser()
            if path.exists():
                return path

        return None

    def _resolve_path(self, file_path: str | Path) -> Path:
        """
        Resolve a path relative to the project root if needed.

        Args:
            file_path: Path to resolve

        Returns:
            Path: Resolved absolute path
        """
        path_obj = Path(file_path)

        # If the path is already absolute, return it unchanged
        if path_obj.is_absolute():
            return path_obj

        # Try to find the project root
        try:
            project_root = resolver.get_project_root()
            return resolver.resolve_project_path(path_obj, project_root)
        except Exception as e:
            self.logger.warning(f"Could not resolve project root: {e}")
            # Fall back to current directory
            return Path.cwd() / path_obj

    @abstractmethod
    def validate_config(self, config: dict) -> bool:
        """
        Validate configuration data.

        Args:
            config: Configuration data to validate

        Returns:
            bool: True if configuration is valid
        """
        ...

    @abstractmethod
    def get_default_config(self) -> dict:
        """
        Get default configuration values.

        Returns:
            dict: Default configuration values
        """
        ...


class BaseIntegrationService(ABC):
    """Base class for integration services."""

    def __init__(
            self,
            config_provider: ConfigProviderProtocol | None = None,
            auth_provider: AuthProviderProtocol | None = None,
            config_path: str | Path | None = None,
            log_level: int = logging.INFO,
    ) -> None:
        """
        Initialize the base integration service.

        Args:
            config_provider: Configuration provider
            auth_provider: Authentication provider
            config_path: Path to configuration file
            log_level: Logging level
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.setLevel(log_level)
        self.log_level = log_level

        self.config_provider = config_provider
        self.auth_provider = auth_provider
        self.config_path = config_path
        self.config: dict | None = None
        self._initialized = False

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the integration."""
        ...

    @property
    def version(self) -> str:
        """Version of the integration."""
        return "1.0.0"  # Default version, override in subclass

    def initialize(self) -> IntegrationResult:
        """
        Initialize the integration.

        This method initializes the integration by loading configuration and
        initializing required components.

        Returns:
            IntegrationResult: Result of initialization
        """
        try:
            # Load configuration if not already loaded
            if not self.config and self.config_provider:
                config_result = self.config_provider.load_config(self.config_path)
                if not config_result.success:
                    return IntegrationResult.error_result(
                        f"Failed to load configuration: {config_result.error}"
                    )
                self.config = config_result.content

            # Initialize authentication if not already initialized
            if self.auth_provider and not getattr(self.auth_provider, "authenticated",
                                                  False):
                auth_result = self.auth_provider.authenticate()
                if not auth_result.success:
                    return IntegrationResult.error_result(
                        f"Failed to authenticate: {auth_result.error}"
                    )

            self._initialized = True
            return IntegrationResult.success_result(
                message=f"{self.name} integration initialized successfully"
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize integration: {e}")
            return IntegrationResult.error_result(
                f"Failed to initialize integration: {str(e)}"
            )

    def is_available(self) -> bool:
        """
        Check if the integration is available.

        Returns:
            bool: True if integration is available
        """
        return self._initialized

    def _ensure_initialized(self) -> IntegrationResult | None:
        """
        Ensure the integration is initialized.

        Returns:
            IntegrationResult | None: Error result if initialization fails, None if initialized
        """
        if not self._initialized:
            init_result = self.initialize()
            if not init_result.success:
                return init_result
        return None