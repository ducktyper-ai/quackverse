# src/quackcore/integrations/google/auth.py
"""
Google authentication provider for QuackCore.

This module handles authentication with Google services, managing
credentials and authorization flows for secure API access.
"""

import logging
import json
from typing import Any

from quackcore.errors import QuackIntegrationError
from quackcore.integrations.base import BaseAuthProvider
from quackcore.integrations.results import AuthResult
from quackcore.fs import service as fs
from quackcore.paths import resolver


class GoogleAuthProvider(BaseAuthProvider):
    """Authentication provider for Google integrations."""

    def __init__(
            self,
            client_secrets_file: str,
            credentials_file: str | None = None,
            scopes: list[str] | None = None,
            log_level: int = logging.INFO,
    ) -> None:
        """
        Initialize the Google authentication provider.

        Args:
            client_secrets_file: Path to Google API client secrets file
            credentials_file: Path where credentials should be stored
            scopes: OAuth scopes for API access
            log_level: Logging level
        """
        super().__init__(credentials_file, log_level)

        self.client_secrets_file = resolver.resolve_project_path(client_secrets_file)
        self.scopes = scopes or []

        # Verify the client secrets file exists
        self._verify_client_secrets_file()

        # Initialize auth object
        self.auth: Any = None
        self.authenticated = False

    @property
    def name(self) -> str:
        """Get the name of the authentication provider."""
        return "GoogleAuth"

    def _verify_client_secrets_file(self) -> None:
        """
        Verify that the client secrets file exists.

        Raises:
            QuackIntegrationError: If the file doesn't exist
        """
        file_info = fs.get_file_info(self.client_secrets_file)
        if not file_info.success or not file_info.exists:
            raise QuackIntegrationError(
                f"Client secrets file not found: {self.client_secrets_file}",
                {"path": str(self.client_secrets_file)},
            )

    def authenticate(self) -> AuthResult:
        """
        Authenticate with Google using configured credentials.

        This method performs the OAuth flow for Google API authentication.
        If credentials already exist, it tries to load them; otherwise,
        it initiates a new authorization flow.

        Returns:
            AuthResult: Result of authentication
        """
        try:
            # Lazy import to avoid dependency if not used
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow

            creds = None

            # Try to load existing credentials
            if self.credentials_file:
                file_info = fs.get_file_info(self.credentials_file)
                if file_info.exists:
                    try:
                        json_result = fs.read_json(self.credentials_file)
                        if json_result.success:
                            creds = Credentials.from_authorized_user_info(
                                json_result.data,
                                self.scopes,
                            )
                        else:
                            self.logger.warning(
                                f"Failed to load credentials: {json_result.error}"
                            )
                    except Exception as e:
                        self.logger.warning(f"Failed to load credentials: {e}")

            # Refresh token if expired
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                self._save_credentials_to_file(creds)
                self.auth = creds
                self.authenticated = True

                return AuthResult(
                    success=True,
                    message="Successfully refreshed credentials",
                    token=creds.token if hasattr(creds, "token") else None,
                    expiry=int(creds.expiry.timestamp())
                    if hasattr(creds, "expiry")
                    else None,
                    credentials_path=str(self.credentials_file),
                )

            # If no valid credentials, authenticate using flow
            if not creds or not creds.valid:
                self.logger.info(
                    "No valid credentials found, starting authentication flow"
                )

                # Create the flow
                # Convert Path to string for InstalledAppFlow.from_client_secrets_file
                client_secrets_path = str(self.client_secrets_file)
                flow = InstalledAppFlow.from_client_secrets_file(
                    client_secrets_path,
                    self.scopes,
                )

                # Run the flow - this will open a browser window
                creds = flow.run_local_server(port=0)

                # Save the credentials
                self._save_credentials_to_file(creds)

            self.auth = creds
            self.authenticated = True

            return AuthResult(
                success=True,
                message="Successfully authenticated with Google",
                token=creds.token if hasattr(creds, "token") else None,
                expiry=int(creds.expiry.timestamp())
                if hasattr(creds, "expiry")
                else None,
                credentials_path=str(self.credentials_file),
            )

        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            self.authenticated = False
            return AuthResult(
                success=False,
                message=None,
                error=f"Failed to authenticate with Google: {str(e)}",
            )

    def refresh_credentials(self) -> AuthResult:
        """
        Refresh authentication credentials if expired.

        Returns:
            AuthResult: Result of refresh operation
        """
        try:
            if not self.auth:
                return self.authenticate()

            # Check if credentials need refresh
            if hasattr(self.auth, "expired") and self.auth.expired:
                from google.auth.transport.requests import Request

                self.auth.refresh(Request())
                self._save_credentials_to_file(self.auth)

                return AuthResult(
                    success=True,
                    message="Successfully refreshed credentials",
                    token=self.auth.token if hasattr(self.auth, "token") else None,
                    expiry=int(self.auth.expiry.timestamp())
                    if hasattr(self.auth, "expiry")
                    else None,
                    credentials_path=str(self.credentials_file),
                )

            # Credentials are still valid
            return AuthResult(
                success=True,
                message="Credentials are valid, no refresh needed",
                token=self.auth.token if hasattr(self.auth, "token") else None,
                expiry=int(self.auth.expiry.timestamp())
                if hasattr(self.auth, "expiry")
                else None,
                credentials_path=str(self.credentials_file),
            )

        except Exception as e:
            self.logger.error(f"Failed to refresh credentials: {e}")
            self.authenticated = False
            return AuthResult(
                success=False,
                message=None,
                error=f"Failed to refresh Google credentials: {str(e)}",
            )

    def get_credentials(self) -> Any:
        """
        Get the current authentication credentials.

        Returns:
            Any: The Google authentication credentials

        Raises:
            QuackIntegrationError: If no valid credentials are available
        """
        if self.auth is None or not self.authenticated:
            result = self.authenticate()
            if not result.success:
                context = {
                    "service": "Google",
                    "credentials_path": str(
                        self.credentials_file) if self.credentials_file else None
                }
                raise QuackIntegrationError(
                    "No valid Google credentials available",
                    context=context
                )

        return self.auth

    def save_credentials(self) -> bool:
        """
        Save the current authentication credentials.

        Returns:
            bool: True if saving was successful
        """
        if self.auth is None:
            return False

        return self._save_credentials_to_file(self.auth)

    def _save_credentials_to_file(self, credentials: Any) -> bool:
        """
        Save credentials to file.

        Args:
            credentials: Google auth credentials

        Returns:
            bool: True if saving was successful
        """
        if not self.credentials_file:
            self.logger.warning("No credentials file specified, cannot save")
            return False

        # Ensure directory exists
        directory_result = fs.create_directory(
            fs.join_path(self.credentials_file).parent,
            exist_ok=True
        )

        if not directory_result.success:
            self.logger.error(
                f"Failed to create credentials directory: {directory_result.error}")
            return False

        # Get credentials data as JSON
        if hasattr(credentials, "to_json") and callable(credentials.to_json):
            try:
                # to_json() returns a JSON string, we need to parse it to a dict
                creds_data = json.loads(credentials.to_json())
            except (json.JSONDecodeError, TypeError) as e:
                self.logger.error(f"Failed to parse credentials JSON: {e}")
                return False
        else:
            # For older credential formats
            try:
                creds_data = {
                    "token": credentials.token,
                    "refresh_token": credentials.refresh_token,
                    "token_uri": credentials.token_uri,
                    "client_id": credentials.client_id,
                    "client_secret": credentials.client_secret,
                    "scopes": credentials.scopes,
                }
            except AttributeError:
                self.logger.error("Credentials object missing required attributes")
                return False

        # Save credentials
        result = fs.write_json(self.credentials_file, creds_data)
        if not result.success:
            self.logger.error(f"Failed to write credentials: {result.error}")
            return False

        return True