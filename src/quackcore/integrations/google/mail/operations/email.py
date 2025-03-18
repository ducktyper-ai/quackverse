# src/quackcore/integrations/google/mail/operations/email.py
"""
Email operations for Google Mail integration.

This module provides functions for listing and downloading emails from Gmail,
including handling message formats and content extraction.
"""

import logging
import os
import re
import time
from datetime import datetime, timedelta
from typing import Protocol, TypeVar, cast

from googleapiclient.errors import HttpError

from quackcore.integrations.google.mail.utils.api import APIRequest, execute_api_request
from quackcore.integrations.results import IntegrationResult

T = TypeVar("T")


class MessagesRequest(APIRequest, Protocol):
    """Protocol for Gmail messages request object."""

    pass


class MessagesResource(Protocol):
    """Protocol for Gmail messages resource."""

    def list(self, user_id: str, q: str, max_results: int) -> MessagesRequest:
        """
        List messages.

        Args:
            user_id: Gmail user ID.
            q: Query string.
            max_results: Maximum number of results.

        Returns:
            MessagesRequest: Request object.
        """
        ...

    def get(
        self, user_id: str, message_id: str, message_format: str
    ) -> MessagesRequest:
        """
        Get a message.

        Args:
            user_id: Gmail user ID.
            message_id: Message ID.
            message_format: Message format.

        Returns:
            MessagesRequest: Request object.
        """
        ...


class UsersResource(Protocol):
    """Protocol for Gmail users resource."""

    def messages(self) -> MessagesResource:
        """Get messages resource."""
        ...


class GmailService(Protocol):
    """Protocol for Gmail service object."""

    def users(self) -> UsersResource:
        """Get users resource."""
        ...


class GmailResponse(Protocol):
    """Protocol for Gmail API response."""

    def get(self, key: str, default: T) -> T:
        """Get a value from the response."""
        ...


def build_query(days_back: int = 7, labels: list[str] | None = None) -> str:
    """
    Build a Gmail search query based on provided parameters.

    Args:
        days_back: Number of days to look back for emails.
        labels: List of Gmail labels to filter by.

    Returns:
        str: Gmail search query string.
    """
    after_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y/%m/%d")
    query_parts = []

    if labels:
        query_parts.extend(f"label:{label}" for label in labels)

    query_parts.append(f"after:{after_date}")
    return " ".join(query_parts)


def list_emails(
    gmail_service: GmailService,
    user_id: str = "me",
    query: str = "",
    logger: logging.Logger | None = None,
) -> IntegrationResult[list[dict]]:
    """
    List emails matching the provided query.

    Args:
        gmail_service: Gmail API service object.
        user_id: Gmail user ID.
        query: Gmail search query.
        logger: Optional logger instance.

    Returns:
        IntegrationResult containing a list of email message dictionaries.
    """
    logger = logger or logging.getLogger(__name__)

    try:
        # Explicit parameter names to avoid shadowing Python builtins
        response_obj = execute_api_request(
            gmail_service.users()
            .messages()
            .list(user_id=user_id, q=query, max_results=100),
            "Failed to list emails from Gmail",
            "users.messages.list",
        )
        # Cast to protocol to satisfy type checker
        response = cast(GmailResponse, response_obj)

        messages = response.get("messages", [])
        return IntegrationResult.success_result(
            content=messages,
            message=f"Listed {len(messages)} emails",
        )

    except HttpError as e:
        logger.error(f"Gmail API error during listing emails: {e}")
        return IntegrationResult.error_result(
            f"Gmail API error during listing emails: {e}"
        )
    except Exception as e:
        logger.error(f"Failed to list emails: {e}")
        return IntegrationResult.error_result(f"Failed to list emails: {e}")


def download_email(
    gmail_service: GmailService,
    user_id: str,
    msg_id: str,
    storage_path: str,
    include_subject: bool = False,
    include_sender: bool = False,
    max_retries: int = 5,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    logger: logging.Logger | None = None,
) -> IntegrationResult[str]:
    """
    Download a Gmail message and save it as an HTML file.

    Args:
        gmail_service: Gmail API service object.
        user_id: Gmail user ID.
        msg_id: The Gmail message ID.
        storage_path: Directory where to save the email.
        include_subject: Whether to include the email subject in the output.
        include_sender: Whether to include the sender in the output.
        max_retries: Maximum number of retries for API calls.
        initial_delay: Initial delay in seconds before the first retry.
        max_delay: Maximum delay in seconds before any retry.
        logger: Optional logger instance.

    Returns:
        IntegrationResult containing the path to the saved email file.
    """
    logger = logger or logging.getLogger(__name__)

    try:
        # Get message with retry logic
        message = _get_message_with_retry(
            gmail_service,
            user_id,
            msg_id,
            max_retries,
            initial_delay,
            max_delay,
            logger,
        )

        if not message:
            return IntegrationResult.error_result(
                f"Message {msg_id} could not be retrieved"
            )

        # Extract headers
        payload = cast(GmailResponse, message).get("payload", {})
        headers = cast(GmailResponse, payload).get("headers", [])
        subject = _extract_header(headers, "subject", "No Subject")
        sender = _extract_header(headers, "from", "unknown@sender")

        # Generate filename
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        clean_sender = clean_filename(sender)
        filename = f"{timestamp}-{clean_sender}.html"
        file_path = os.path.join(storage_path, filename)

        # Process message parts
        html_content, attachments = process_message_parts(
            gmail_service, user_id, [payload], msg_id, storage_path, logger
        )

        if not html_content:
            logger.warning(f"No HTML content found in message {msg_id}")
            return IntegrationResult.error_result(
                f"No HTML content found in message {msg_id}"
            )

        # Prepare HTML content with optional headers
        content = html_content
        header_parts = []

        if include_subject:
            header_parts.append(f"<h1>Subject: {subject}</h1>")
        if include_sender:
            header_parts.append(f"<h2>From: {sender}</h2>")

        if header_parts:
            content = f"{''.join(header_parts)}<hr/>{content}"

        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return IntegrationResult.success_result(
            content=file_path, message=f"Email downloaded successfully to {file_path}"
        )

    except Exception as e:
        logger.error(f"Failed to download email {msg_id}: {e}")
        return IntegrationResult.error_result(f"Failed to download email {msg_id}: {e}")


def _get_message_with_retry(
    gmail_service: GmailService,
    user_id: str,
    msg_id: str,
    max_retries: int,
    initial_delay: float,
    max_delay: float,
    logger: logging.Logger,
) -> dict | None:
    """
    Get a Gmail message with retry logic.

    Args:
        gmail_service: Gmail API service object.
        user_id: Gmail user ID.
        msg_id: The Gmail message ID.
        max_retries: Maximum number of retries.
        initial_delay: Initial delay before first retry.
        max_delay: Maximum delay between retries.
        logger: Logger instance.

    Returns:
        dict | None: The message data if successful, None otherwise.
    """
    retry_count = 0
    delay = initial_delay

    while retry_count < max_retries:
        try:
            # Use explicit keyword arguments to avoid shadowing builtins
            result = execute_api_request(
                gmail_service.users()
                .messages()
                .get(user_id=user_id, message_id=msg_id, message_format="full"),
                "Failed to get message from Gmail",
                "users.messages.get",
            )
            # We need to cast here to satisfy the type checker
            # The return type is actually a dict
            return cast(dict, result)
        except HttpError as e:
            retry_count += 1
            if retry_count == max_retries:
                logger.error(
                    f"Failed to download message {msg_id} after {max_retries} attempts"
                )
                return None

            logger.debug(
                f"Retry {retry_count}/{max_retries} for message {msg_id} "
                f"after error: {e}"
            )
            time.sleep(delay)
            delay = min(delay * 2, max_delay)

    return None


def _extract_header(headers: list[dict], name: str, default: str) -> str:
    """
    Extract a header value from a list of headers.

    Args:
        headers: List of header dictionaries.
        name: Header name to extract.
        default: Default value if header not found.

    Returns:
        str: The header value or default.
    """
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value", default)
    return default


def clean_filename(text: str) -> str:
    """
    Clean a string to be safely used as a filename.

    Args:
        text: Input text.

    Returns:
        str: A safe filename string.
    """
    return re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")


def process_message_parts(
    gmail_service: GmailService,
    user_id: str,
    parts: list[dict],
    msg_id: str,
    storage_path: str,
    logger: logging.Logger,
) -> tuple[str | None, list[str]]:
    """
    Process message parts to extract HTML content and attachments.

    Args:
        gmail_service: Gmail API service object.
        user_id: Gmail user ID.
        parts: List of message part dictionaries.
        msg_id: The Gmail message ID.
        storage_path: Path to save attachments.
        logger: Logger instance.

    Returns:
        tuple: HTML content (or None) and list of attachment paths.
    """
    from quackcore.integrations.google.mail.operations.attachments import (
        process_message_parts as process_parts,
    )

    return process_parts(gmail_service, user_id, parts, msg_id, storage_path, logger)
