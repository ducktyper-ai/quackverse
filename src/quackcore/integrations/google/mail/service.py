"""
Google Mail integration service for QuackCore.

This module provides integration with Gmail, handling OAuth2.0
authentication, email listing, and downloading emails as HTML files.
It follows best practices for Python 3.13, using native types,
explicit return types, and pydantic for configuration.
"""

import os
import re
import time
import base64
import logging
from datetime import datetime, timedelta
from types import NoneType

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from pydantic import Field

from quackcore.integrations.base import BaseIntegrationService
from quackcore.integrations.results import IntegrationResult
from quackcore.integrations.google.auth import GoogleAuthProvider
from quackcore.integrations.google.config import GoogleConfigProvider, GoogleMailConfig
from quackcore.paths import resolver
from quackcore.errors import QuackIntegrationError


# Extend the existing GoogleMailConfig to include additional settings
class GmailServiceConfig(GoogleMailConfig):
    storage_path: str = Field(..., description="Path to store downloaded emails")
    oauth_scope: list[str] = Field(
        default_factory=lambda: ["https://www.googleapis.com/auth/gmail.readonly"],
        description="OAuth scopes for Gmail API access"
    )
    max_retries: int = Field(5, description="Maximum number of retries for API calls")
    initial_delay: float = Field(1.0, description="Initial delay for exponential backoff")
    max_delay: float = Field(30.0, description="Maximum delay for exponential backoff")
    include_subject: bool = Field(False, description="Include email subject in downloaded file")
    include_sender: bool = Field(False, description="Include email sender in downloaded file")


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
            initial_delay: Initial delay for exponential backoff.
            max_delay: Maximum delay for exponential backoff.
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
        self.oauth_scope: list[str] = oauth_scope if oauth_scope is not None else ["https://www.googleapis.com/auth/gmail.readonly"]
        self.max_retries: int = max_retries
        self.initial_delay: float = initial_delay
        self.max_delay: float = max_delay
        self.include_subject: bool = include_subject
        self.include_sender: bool = include_sender

        self.auth_provider: GoogleAuthProvider = GoogleAuthProvider(
            client_secrets_file=self.custom_config.get("client_secrets_file") or "",
            credentials_file=self.custom_config.get("credentials_file") or "",
            scopes=self.oauth_scope,
            log_level=log_level,
        )
        self.gmail_service: any = None
        self.config: dict[str, any] = {}

    @property
    def name(self) -> str:
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
            if self.custom_config:
                self.config = self.custom_config
            else:
                config_result: IntegrationResult = self.config_provider.load_config(self.config_path)
                self.config = config_result.content or {}

            # Ensure storage_path is defined either via constructor or configuration
            if not self.storage_path:
                self.storage_path = self.config.get("storage_path")
            if not self.storage_path:
                raise QuackIntegrationError("Storage path not specified in configuration", {})

            # Resolve the storage path and ensure it exists
            self.storage_path = str(resolver.resolve_project_path(self.storage_path))
            if not os.path.exists(self.storage_path):
                os.makedirs(self.storage_path, exist_ok=True)

            # Authenticate and build the Gmail API service
            credentials: any = self.auth_provider.get_credentials()
            self.gmail_service = build('gmail', 'v1', credentials=credentials)

            self._initialized = True
            return IntegrationResult.success_result(message="Google Mail service initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Google Mail service: {e}")
            return IntegrationResult.error_result(f"Failed to initialize Google Mail service: {e}")

    def list_emails(self, query: str | None = None) -> IntegrationResult[list[dict]]:
        """
        List emails matching the provided query.

        Args:
            query: Gmail search query string. If not provided, a default query is built
                   using the 'gmail_days_back' and 'gmail_labels' configuration values.

        Returns:
            IntegrationResult containing a list of email message dicts.
        """
        init_error: IntegrationResult | None = self._ensure_initialized()
        if init_error:
            return init_error

        try:
            if query is None:
                days_back: int = self.config.get("gmail_days_back", 7)
                labels: list[str] = self.config.get("gmail_labels", [])
                after_date: str = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
                query_parts: list[str] = []
                if labels:
                    query_parts.extend(f"label:{label}" for label in labels)
                query_parts.append(f"after:{after_date}")
                query = " ".join(query_parts)

            response: dict = self.gmail_service.users().messages().list(
                userId=self.config.get("gmail_user_id", "me"),
                q=query,
                maxResults=100
            ).execute()
            messages: list[dict] = response.get("messages", [])
            return IntegrationResult.success_result(content=messages, message=f"Listed {len(messages)} emails")
        except HttpError as e:
            self.logger.error(f"Gmail API error during listing emails: {e}")
            return IntegrationResult.error_result(f"Gmail API error during listing emails: {e}")
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
        init_error: IntegrationResult | None = self._ensure_initialized()
        if init_error:
            return init_error

        try:
            retry_count: int = 0
            delay: float = self.initial_delay
            message: dict | None = None
            while retry_count < self.max_retries:
                try:
                    message = self.gmail_service.users().messages().get(
                        userId=self.config.get("gmail_user_id", "me"),
                        id=msg_id,
                        format="full"
                    ).execute()
                    break
                except HttpError as e:
                    retry_count += 1
                    if retry_count == self.max_retries:
                        self.logger.error(f"Failed to download message {msg_id} after {self.max_retries} attempts")
                        return IntegrationResult.error_result(f"Failed to download message {msg_id}: {e}")
                    time.sleep(delay)
                    delay = min(delay * 2, self.max_delay)

            if message is None:
                return IntegrationResult.error_result(f"Message {msg_id} could not be retrieved")

            payload: dict = message.get("payload", {})
            headers: list[dict] = payload.get("headers", [])
            subject: str = next((h.get("value", "No Subject") for h in headers if h.get("name", "").lower() == "subject"), "No Subject")
            sender: str = next((h.get("value", "unknown@sender") for h in headers if h.get("name", "").lower() == "from"), "unknown@sender")
            timestamp: str = datetime.now().strftime('%Y-%m-%d-%H%M%S')
            clean_sender: str = self._clean_filename(sender)

            html_content, _ = self._process_message_parts([payload], msg_id)
            if html_content is None:
                self.logger.warning(f"No HTML content found in message {msg_id}")
                return IntegrationResult.error_result(f"No HTML content found in message {msg_id}")

            header_parts: list[str] = []
            if self.include_subject:
                header_parts.append(f"<h1>Subject: {subject}</h1>")
            if self.include_sender:
                header_parts.append(f"<h2>From: {sender}</h2>")
            if header_parts:
                html_content = f"{''.join(header_parts)}<hr/>{html_content}"

            filename: str = f"{timestamp}-{clean_sender}.html"
            file_path: str = os.path.join(self.storage_path, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            return IntegrationResult.success_result(content=file_path, message=f"Email downloaded successfully to {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to download email {msg_id}: {e}")
            return IntegrationResult.error_result(f"Failed to download email {msg_id}: {e}")

    def _clean_filename(self, text: str) -> str:
        """
        Clean a string to be safely used as a filename.

        Args:
            text: Input text.

        Returns:
            A cleaned string.
        """
        return re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")

    def _process_message_parts(self, parts: list[dict], msg_id: str) -> tuple[str | None, list[str]]:
        """
        Process message parts to extract HTML content and attachments.

        Args:
            parts: List of message part dictionaries.
            msg_id: The Gmail message ID (used for attachment retrieval).

        Returns:
            A tuple containing the HTML content (or None) and a list of attachment file paths.
        """
        html_content: str | None = None
        attachments: list[str] = []
        parts_stack: list[dict] = parts.copy()

        while parts_stack:
            part: dict = parts_stack.pop()
            if "parts" in part:
                parts_stack.extend(part["parts"])
                continue

            mime_type: str = part.get("mimeType", "")
            if mime_type == "text/html" and html_content is None:
                data: str | None = part.get("body", {}).get("data")
                if data:
                    html_content = base64.urlsafe_b64decode(data.encode("UTF-8")).decode("UTF-8")
            elif part.get("filename"):
                attachment_path: str | None = self._handle_attachment(part, msg_id, self.storage_path)
                if attachment_path:
                    attachments.append(attachment_path)
        return html_content, attachments

    def _handle_attachment(self, part: dict, msg_id: str, base_path: str) -> str | None:
        """
        Download and save an attachment from a message part.

        Args:
            part: The message part dictionary containing attachment data.
            msg_id: The Gmail message ID.
            base_path: The directory where attachments should be saved.

        Returns:
            The file path of the saved attachment or None.
        """
        try:
            filename: str | None = part.get("filename")
            if not filename:
                return None

            data: str | None = part.get("body", {}).get("data")
            if not data and "attachmentId" in part.get("body", {}):
                attachment_id: str = part["body"]["attachmentId"]
                att: dict = self.gmail_service.users().messages().attachments().get(
                    userId=self.config.get("gmail_user_id", "me"),
                    messageId=msg_id,
                    id=attachment_id
                ).execute()
                data = att.get("data")

            if not data:
                return None

            content: bytes = base64.urlsafe_b64decode(data)
            clean_name: str = self._clean_filename(filename)
            file_path: str = os.path.join(base_path, clean_name)
            counter: int = 1
            base_file, ext = os.path.splitext(file_path)
            while os.path.exists(file_path):
                file_path = f"{base_file}-{counter}{ext}"
                counter += 1

            with open(file_path, "wb") as f:
                f.write(content)
            return file_path
        except Exception as e:
            self.logger.error(f"Error handling attachment: {e}")
            return None


def create_integration() -> GoogleMailService:
    """
    Factory function to create and configure a Google Mail integration.

    Returns:
        GoogleMailService: Configured Gmail integration service.
    """
    return GoogleMailService()
