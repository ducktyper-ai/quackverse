# src/quackcore/integrations/google/mail/service.py
"""
Google Mail integration service for QuackCore.

This module provides the main service class for Google Mail integration,
serving as a thin controller that delegates to specialized operation modules.
"""

import logging
import os
from types import NoneType

from quackcore.errors import QuackIntegrationError
from quackcore.integrations.base import BaseIntegrationService
from quackcore.integrations.google.auth import GoogleAuthProvider
from quackcore.integrations.google.config import (
    GoogleConfigProvider,
)
from quackcore.integrations.google.mail.operations import auth, email
from quackcore.integrations.results import IntegrationResult
from quackcore.paths import resolver


class GoogleMailService(BaseIntegrationService):
    """Integration service for Google Mail (Gmail)."""

    def __init__(
        self,
        client_secrets_file: str | None = None,
        credentials_file: str | None = None,
        config_path: str | None = None,
        storage_path: str | None = None,
        oauth_scope: list[str] | None = None,
        max_retries: int = 5,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        include_subject: bool = False,
        include_sender: bool = False,
        log_level: int = logging.INFO,
    ) -> None:
        """
        Initialize the Google Mail integration service.

        Args:
            client_secrets_file: Path to the client secrets file.
            credentials_file: Path to the credentials file.
            config_path: Path to the configuration file.
            storage_path: Path where downloaded emails will be stored.
            oauth_scope: OAuth scopes for the Gmail API.
            max_retries: Maximum number of retries for API calls.
            initial_delay: Initial delay in seconds before the first retry.
            max_delay: Maximum delay in seconds before any retry.
            include_subject: Whether to include the email subject in the output HTML.
            include_sender: Whether to include the sender in the output HTML.
            log_level: Logging level.
        """
        # Create a configuration provider for Gmail using the "mail" service
        config_provider: GoogleConfigProvider = GoogleConfigProvider("mail", log_level)
        super().__init__(config_provider, None, config_path, log_level)

        # If explicit parameters are provided, override configuration from file.
        self.custom_config: dict[str, any] = {}
        if client_secrets_file and credentials_file:
            self.custom_config = {
                "client_secrets_file": client_secrets_file,
                "credentials_file": credentials_file,
                "storage_path": storage_path,
                "oauth_scope": oauth_scope,
                "max_retries": max_retries,
                "initial_delay": initial_delay,
                "max_delay": max_delay,
                "include_subject": include_subject,
                "include_sender": include_sender,
            }

        # Save additional settings to instance variables.
        self.storage_path: str | None = storage_path
        self.oauth_scope: list[str] = (
            oauth_scope
            if oauth_scope is not None
            else ["https://www.googleapis.com/auth/gmail.readonly"]
        )
        self.max_retries: int = max_retries
        self.initial_delay: float = initial_delay
        self.max_delay: float = max_delay
        self.include_subject: bool = include_subject
        self.include_sender: bool = include_sender

        self.auth_provider: GoogleAuthProvider | None = None
        self.gmail_service: any = None
        self.config: dict[str, any] = {}

    @property
    def name(self) -> str:
        """Get the name of the integration."""
        return "GoogleMail"

    def initialize(self) -> IntegrationResult[NoneType]:
        """
        Initialize the Google Mail service.

        Returns:
            IntegrationResult indicating success or failure.
        """
        init_result: IntegrationResult = super().initialize()
        if not init_result.success:
            return init_result

        try:
            # Merge configuration: prefer custom parameters if provided
            config = self._initialize_config()
            if not config:
                return IntegrationResult.error_result(
                    "Failed to initialize configuration"
                )

            # Create auth provider
            self.auth_provider = GoogleAuthProvider(
                client_secrets_file=config["client_secrets_file"],
                credentials_file=config["credentials_file"],
                scopes=self.oauth_scope,
                log_level=self.log_level,
            )

            # Authenticate and build the Gmail API service
            credentials = self.auth_provider.get_credentials()
            self.gmail_service = auth.initialize_gmail_service(credentials)

            self._initialized = True
            return IntegrationResult.success_result(
                message="Google Mail service initialized successfully"
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize Google Mail service: {e}")
            return IntegrationResult.error_result(
                f"Failed to initialize Google Mail service: {e}"
            )

    def _initialize_config(self) -> dict[str, any] | None:
        """
        Initialize configuration from parameters or config file.

        Returns:
            dict: The initialized configuration or None if failed.
        """
        try:
            # Use custom config if provided
            if self.custom_config:
                self.config = self.custom_config
            else:
                # Load from config file
                config_result = self.config_provider.load_config(self.config_path)
                if not config_result.success or not config_result.content:
                    raise QuackIntegrationError(
                        "Failed to load configuration from file", {}
                    )
                self.config = config_result.content

            # Ensure storage_path is defined and exists
            if not self.storage_path:
                self.storage_path = self.config.get("storage_path")
            if not self.storage_path:
                raise QuackIntegrationError(
                    "Storage path not specified in configuration", {}
                )

            # Resolve the storage path and ensure it exists
            self.storage_path = str(resolver.resolve_project_path(self.storage_path))
            os.makedirs(self.storage_path, exist_ok=True)

            return self.config
        except Exception as e:
            self.logger.error(f"Failed to initialize configuration: {e}")
            return None

    def list_emails(self, query: str | None = None) -> IntegrationResult[list[dict]]:
        """
        List emails matching the provided query.

        Args:
            query: Gmail search query string. If not provided, a default query is built
                  using the configured parameters.

        Returns:
            IntegrationResult containing a list of email message dicts.
        """
        if init_error := self._ensure_initialized():
            return init_error

        try:
            # Build default query if not provided
            if query is None:
                days_back = self.config.get("gmail_days_back", 7)
                labels = self.config.get("gmail_labels", [])
                query = email.build_query(days_back, labels)

            user_id = self.config.get("gmail_user_id", "me")
            return email.list_emails(self.gmail_service, user_id, query, self.logger)
        except Exception as e:
            self.logger.error(f"Failed to list emails: {e}")
            return IntegrationResult.error_result(f"Failed to list emails: {e}")

    def download_email(self, msg_id: str) -> IntegrationResult[str]:
        """
        Download a Gmail message and save it as an HTML file.

        Args:
            msg_id: The Gmail message ID.

        Returns:
            IntegrationResult containing the file path of the downloaded email.
        """
        if init_error := self._ensure_initialized():
            return init_error

        try:
            user_id = self.config.get("gmail_user_id", "me")
            include_subject = self.config.get("include_subject", self.include_subject)
            include_sender = self.config.get("include_sender", self.include_sender)
            max_retries = self.config.get("max_retries", self.max_retries)
            initial_delay = self.config.get("initial_delay", self.initial_delay)
            max_delay = self.config.get("max_delay", self.max_delay)

            return email.download_email(
                self.gmail_service,
                user_id,
                msg_id,
                self.storage_path,
                include_subject,
                include_sender,
                max_retries,
                initial_delay,
                max_delay,
                self.logger,
            )
        except Exception as e:
            self.logger.error(f"Failed to download email {msg_id}: {e}")
            return IntegrationResult.error_result(
                f"Failed to download email {msg_id}: {e}"
            )
