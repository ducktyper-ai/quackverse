# src/quackcore/integrations/google/mail/operations/auth.py
"""
Authentication operations for Google Mail integration.

This module provides functions for authenticating with the Gmail API
and initializing the service.
"""

from typing import Protocol

from quackcore.errors import QuackApiError
from quackcore.integrations.google.mail.operations.email import GmailService


class GoogleCredentials(Protocol):
    """Protocol for Google API credentials."""

    # Credentials must have these attributes used by the googleapiclient
    token: str
    refresh_token: str
    token_uri: str
    client_id: str
    client_secret: str
    scopes: list[str]


def initialize_gmail_service(credentials: GoogleCredentials) -> GmailService:
    """
    Initialize the Gmail API service with provided credentials.

    Args:
        credentials: Google API credentials.

    Returns:
        GmailService: Initialized Gmail service object.

    Raises:
        QuackApiError: If service initialization fails.
    """
    try:
        from googleapiclient.discovery import build

        return build("gmail", "v1", credentials=credentials)
    except Exception as api_error:
        raise QuackApiError(
            f"Failed to initialize Gmail API: {api_error}",
            service="Gmail",
            api_method="build",
            original_error=api_error,
        ) from api_error
