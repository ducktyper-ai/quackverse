# src/quackcore/integrations/google/auth.py
"""
Google authentication provider for QuackCore.

This module handles authentication with Google services, managing
credentials and authorization flows for secure API access.
"""

import logging
from collections.abc import Sequence

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from quackcore.errors import QuackIntegrationError
from quackcore.fs import service as fs
from quackcore.integrations.core.base import BaseAuthProvider
from quackcore.integrations.google.serialization import serialize_credentials
from quackcore.integrations.core.results import AuthResult


class GoogleAuthProvider(BaseAuthProvider):
    """Authentication provider for Google integrations."""

    def __init__(
        self,
        client_secrets_file: str,
        credentials_file: str | None = None,
        scopes: list[str] | Sequence[str] | None = None,
        log_level: int = logging.INFO,
    ) -> None:
        super().__init__(credentials_file, log_level)

        self.client_secrets_file = self._resolve_path(client_secrets_file)
        self.scopes = list(scopes) if scopes else []

        self._verify_client_secrets_file()

        self.auth: Credentials | None = None
        self.authenticated = False

    @property
    def name(self) -> str:
        return "GoogleAuth"

    def _verify_client_secrets_file(self) -> None:
        file_info = fs.get_file_info(self.client_secrets_file)
        if not file_info.success or not file_info.exists:
            raise QuackIntegrationError(
                f"Client secrets file not found: {self.client_secrets_file}",
                {"path": str(self.client_secrets_file)},
            )

    def authenticate(self) -> AuthResult:
        try:
            creds = self._load_existing_credentials()

            if (
                creds
                and getattr(creds, "expired", False)
                and getattr(creds, "refresh_token", None)
            ):
                creds.refresh(Request())
                self._save_credentials_to_file(creds)
                self.auth = creds
                self.authenticated = True
                return self._build_auth_result(
                    creds, "Successfully refreshed credentials"
                )

            if not creds or not getattr(creds, "valid", False):
                self.logger.info(
                    "No valid credentials found, starting authentication flow"
                )

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file, self.scopes
                )
                creds = flow.run_local_server(port=0)
                self._save_credentials_to_file(creds)

            self.auth = creds
            self.authenticated = True
            return self._build_auth_result(
                creds, "Successfully authenticated with Google"
            )

        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            self.authenticated = False
            return AuthResult(
                success=False,
                message=None,
                error=f"Failed to authenticate with Google: {str(e)}",
            )

    def _load_existing_credentials(self) -> Credentials | None:
        if not self.credentials_file:
            return None

        file_info = fs.get_file_info(self.credentials_file)
        if not file_info.exists:
            return None

        json_result = fs.read_json(self.credentials_file)
        if not json_result.success:
            self.logger.warning(f"Failed to load credentials: {json_result.error}")
            return None

        try:
            return Credentials.from_authorized_user_info(json_result.data, self.scopes)
        except ValueError as e:
            self.logger.warning(f"Invalid credential data: {e}")
            return None

    def _build_auth_result(self, creds: Credentials, message: str) -> AuthResult:
        return AuthResult(
            success=True,
            message=message,
            token=str(getattr(creds, "token", None)),
            expiry=int(creds.expiry.timestamp())
            if getattr(creds, "expiry", None)
            else None,
            credentials_path=str(self.credentials_file),
        )

    def refresh_credentials(self) -> AuthResult:
        try:
            if not self.auth:
                return self.authenticate()

            if getattr(self.auth, "expired", False):
                self.auth.refresh(Request())
                self._save_credentials_to_file(self.auth)
                return self._build_auth_result(
                    self.auth, "Successfully refreshed credentials"
                )

            return self._build_auth_result(
                self.auth, "Credentials are valid, no refresh needed"
            )

        except Exception as e:
            self.logger.error(f"Failed to refresh credentials: {e}")
            self.authenticated = False
            return AuthResult(
                success=False,
                message=None,
                error=f"Failed to refresh Google credentials: {str(e)}",
            )

    def get_credentials(self) -> Credentials:
        if self.auth is None or not self.authenticated:
            result = self.authenticate()
            if not result.success:
                raise QuackIntegrationError(
                    "No valid Google credentials available",
                    {
                        "service": "Google",
                        "credentials_path": self.credentials_file,
                    },
                )
        return self.auth

    def save_credentials(self) -> bool:
        if self.auth is None:
            return False
        return self._save_credentials_to_file(self.auth)

    def _save_credentials_to_file(self, credentials: Credentials) -> bool:
        if not self.credentials_file:
            self.logger.warning("No credentials file specified, cannot save")
            return False

        parent_dir = fs.split_path(self.credentials_file)[:-1]
        if parent_dir:
            directory_path = fs.join_path(*parent_dir)
            result = fs.create_directory(directory_path, exist_ok=True)
            if not result.success:
                self.logger.error(
                    f"Failed to create credentials directory: {result.error}"
                )
                return False

        try:
            data = serialize_credentials(credentials)
            result = fs.write_json(self.credentials_file, data)
            if not result.success:
                self.logger.error(f"Failed to write credentials: {result.error}")
                return False
            return True

        except Exception as e:
            self.logger.error(f"Failed to serialize or save credentials: {e}")
            return False
