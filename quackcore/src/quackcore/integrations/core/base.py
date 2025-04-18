# quackcore/src/quackcore/integrations/core/base.py
"""
Base classes for QuackCore integrations.

This module provides abstract base classes that integration implementations
can inherit from, providing common functionality and ensuring
consistent behavior.
"""

import os
from abc import ABC, abstractmethod
from typing import Any

from quackcore.errors import QuackConfigurationError, QuackFileNotFoundError
from quackcore.fs import expand_user_vars
from quackcore.fs import service as fs
from quackcore.integrations.core.protocols import (
    AuthProviderProtocol,
    ConfigProviderProtocol,
    IntegrationProtocol,
)
from quackcore.integrations.core.results import (
    AuthResult,
    ConfigResult,
    IntegrationResult,
)
from quackcore.logging import LOG_LEVELS, LogLevel, get_logger
from quackcore.paths import service as paths


class BaseAuthProvider(ABC, AuthProviderProtocol):
    """Base class for authentication providers."""

    def __init__(
        self,
        credentials_file: str | None = None,
        log_level: int = LOG_LEVELS[LogLevel.INFO],
    ) -> None:
        """
        Initialize the base authentication provider.

        Args:
            credentials_file: Path to credentials file
            log_level: Logging level
        """
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.logger.setLevel(log_level)

        self.credentials_file = (
            self._resolve_path(credentials_file) if credentials_file else None
        )
        self.authenticated = False

    def _resolve_path(self, file_path: str) -> str:
        """
        Resolve a path relative to the project root if needed.

        Args:
            file_path: Path to resolve

        Returns:
            str: Resolved absolute path
        """
        try:
            resolved_path = paths.resolve_project_path(file_path)
            return str(resolved_path)
        except Exception as e:
            self.logger.warning(f"Could not resolve project path: {e}")
            # Import the global service instance as recommended in best practices
            from quackcore.fs import service as fs

            normalized_path = fs.normalize_path(file_path)
            return str(normalized_path)

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
            from quackcore.fs import service as fs

            parent_path = fs.split_path(self.credentials_file)[:-1]
            parent_dir = fs.join_path(*parent_path)
            result = fs.create_directory(parent_dir, exist_ok=True)
            return result.success
        except Exception as e:
            self.logger.error(f"Unexpected error creating credentials directory: {e}")
            return False


class BaseConfigProvider(ABC, ConfigProviderProtocol):
    """Base class for configuration providers."""

    DEFAULT_CONFIG_LOCATIONS = [
        "./config/integration_config.yaml",
        "./quack_config.yaml",
        "~/.quack/config.yaml",
    ]

    def __init__(self, log_level: int = LOG_LEVELS[LogLevel.INFO]) -> None:
        """
        Initialize the base configuration provider.

        Args:
            log_level: Logging level
        """
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.logger.setLevel(log_level)

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the configuration provider."""
        ...

    def load_config(self, config_path: str | None = None) -> ConfigResult:
        """
        Load configuration from a file.

        Args:
            config_path: Path to configuration file.

        Returns:
            ConfigResult: Result containing configuration data.

        Raises:
            QuackConfigurationError: If the configuration file cannot be found or
                                      if reading the YAML fails.
        """
        # Determine config path.
        if not config_path:
            config_path = self._find_config_file()
            if not config_path:
                raise QuackConfigurationError(
                    "Configuration file not found in default locations."
                )

        path_obj = self._resolve_path(config_path)

        # Import functions at runtime so that patches work.
        from quackcore.fs.service import get_file_info, read_yaml

        # Check if configuration file exists.
        file_info = get_file_info(path_obj)
        if not file_info.success or not file_info.exists:
            raise QuackConfigurationError(
                f"Configuration file not found: {path_obj}",
                config_path=str(path_obj),
            )

        # Read configuration file.
        yaml_result = read_yaml(path_obj)
        if not yaml_result.success:
            raise QuackConfigurationError(
                f"Failed to read YAML configuration: {yaml_result.error}",
                config_path=str(path_obj),
            )

        # Extract integration-specific configuration.
        config_data = yaml_result.data
        integration_config = self._extract_config(config_data)

        # Validate configuration.
        if not self.validate_config(integration_config):
            # Return an error result rather than raising.
            return ConfigResult.error_result("Configuration validation failed")

        return ConfigResult.success_result(
            content=integration_config,
            message="Successfully loaded configuration",
            config_path=str(path_obj),
        )

    def _extract_config(self, config_data: dict[str, Any]) -> dict[str, Any]:
        """
        Extract integration-specific configuration from the full config data.

        Args:
            config_data: Full configuration data

        Returns:
            dict[str, Any]: Integration-specific configuration
        """
        # Default implementation - override in subclass
        # to extract integration-specific section
        integration_name = self.name.lower().replace(" ", "_")
        return config_data.get(integration_name, {})

    def _find_config_file(self) -> str | None:
        """
        Find a configuration file in standard locations.

        Returns:
            str | None: Path to the configuration file if found, None otherwise.
        """
        # Check environment variable first.
        env_var = f"QUACK_{self.name.upper()}_CONFIG"
        if config_path := os.environ.get(env_var):
            # Import these specifically at runtime to match the patching in tests
            from quackcore.fs import service as fs

            expanded_path = expand_user_vars(config_path)
            # Convert Path to string to match test expectation
            file_info = fs.get_file_info(str(expanded_path))
            if file_info.success and file_info.exists:
                return str(expanded_path)

        # Attempt to get the project root, with graceful error handling
        project_root = None
        try:
            from quackcore.paths import service as paths

            project_root = paths.get_project_root()
        except (QuackFileNotFoundError, FileNotFoundError, OSError) as e:
            self.logger.debug(
                f"Project root not found, checking only direct paths: {e}"
            )

        # Import these here to match patching in tests
        from quackcore.fs import service as fs

        # Check default locations.
        for location in self.DEFAULT_CONFIG_LOCATIONS:
            expanded_location = expand_user_vars(location)
            # If the expanded location is relative
            # and we have a project root, join them.
            if not os.path.isabs(str(expanded_location)) and project_root:
                expanded_location = fs.join_path(project_root, expanded_location)
            # Convert Path to string for consistency with tests
            file_info = fs.get_file_info(str(expanded_location))
            if file_info.success and file_info.exists:
                return str(expanded_location)

        # Fallback: try candidate in project root.
        if project_root:
            candidate = fs.join_path(project_root, "quack_config.yaml")
            candidate = expand_user_vars(candidate)
            # Convert Path to string for consistency with tests
            file_info = fs.get_file_info(str(candidate))
            if file_info.success and file_info.exists:
                return str(candidate)

        return None

    def _resolve_path(self, file_path: str) -> str:
        """
        Resolve a path relative to the project root if needed.

        Args:
            file_path: Path to resolve.

        Returns:
            str: Resolved absolute path.
        """
        try:
            resolved_path = paths.resolve_project_path(file_path)
            return str(resolved_path)
        except Exception as e:
            self.logger.warning(f"Could not resolve project path: {e}")
            # Import normalize_path at runtime.
            from quackcore.fs import service as fs

            normalized_path = fs.normalize_path(file_path)
            return str(normalized_path)

    @abstractmethod
    def validate_config(self, config: dict[str, Any]) -> bool:
        """
        Validate configuration data.

        Args:
            config: Configuration data to validate

        Returns:
            bool: True if configuration is valid
        """
        ...

    @abstractmethod
    def get_default_config(self) -> dict[str, Any]:
        """
        Get default configuration values.

        Returns:
            dict[str, Any]: Default configuration values
        """
        ...


class BaseIntegrationService(ABC, IntegrationProtocol):
    """Base class for integration services."""

    def __init__(
        self,
        config_provider: ConfigProviderProtocol | None = None,
        auth_provider: AuthProviderProtocol | None = None,
        config_path: str | None = None,
        log_level: int = LOG_LEVELS[LogLevel.INFO],
    ) -> None:
        """
        Initialize the base integration service.

        Args:
            config_provider: Configuration provider
            auth_provider: Authentication provider
            config_path: Path to configuration file
            log_level: Logging level
        """
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.logger.setLevel(log_level)
        self.log_level = log_level

        self.config_provider = config_provider
        self.auth_provider = auth_provider

        # Use QuackCore's path resolver to normalize config path if provided
        if config_path:
            try:
                self.config_path = str(paths.resolve_project_path(config_path))
            except Exception as e:
                self.logger.warning(f"Could not resolve config path: {e}")
                self.config_path = str(fs.normalize_path(config_path))
        else:
            self.config_path = None

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
                    config_error = QuackConfigurationError(
                        f"Failed to load configuration: {config_result.error}",
                        config_path=self.config_path,
                    )
                    self.logger.error(str(config_error))
                    return IntegrationResult.error_result(str(config_error))
                self.config = config_result.content

            # Initialize authentication if not already initialized
            if self.auth_provider and not getattr(
                self.auth_provider, "authenticated", False
            ):
                auth_result = self.auth_provider.authenticate()
                if not auth_result.success:
                    return IntegrationResult.error_result(
                        f"Failed to authenticate {self.name}: {auth_result.error}"
                    )

            self._initialized = True
            return IntegrationResult.success_result(
                message=f"{self.name} integration initialized successfully"
            )
        except QuackConfigurationError as e:
            self.logger.error(f"Configuration error during initialization: {e}")
            return IntegrationResult.error_result(str(e))
        except Exception as e:
            self.logger.error(f"Failed to initialize integration: {e}")
            return IntegrationResult.error_result(
                f"Failed to initialize {self.name} integration: {str(e)}"
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
            IntegrationResult | None: Error result if initialization fails,
                                        None if initialized
        """
        if not self._initialized:
            init_result = self.initialize()
            if not init_result.success:
                return init_result
        return None
