# src/quackcore/integrations/google/mail/operations/email.py
"""
Email operations for Google Mail integration.

This module provides functions for listing and downloading emails from Gmail,
including handling message formats and content extraction.
"""

import base64
import logging
import re
import time
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from typing import Protocol, TypeVar, cast

from googleapiclient.errors import HttpError

from quackcore.fs import service as fs
from quackcore.integrations.google.mail.protocols import GmailRequest, GmailService
from quackcore.integrations.google.mail.utils.api import execute_api_request
from quackcore.integrations.core.results import IntegrationResult

T = TypeVar("T")  # Generic type for result content


class MessagesRequest(GmailRequest, Protocol):
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
) -> IntegrationResult[list[Mapping]]:
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
        clean_sender_name = clean_filename(sender)
        filename = f"{timestamp}-{clean_sender_name}.html"

        # Use fs service to join paths
        filepath_obj = fs.join_path(storage_path, filename)
        filepath = str(
            filepath_obj
        )  # Ensure we get a string, not a Path or other object

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

        # Use fs service to write content
        write_result = fs.write_text(filepath, content, encoding="utf-8")
        if not write_result.success:
            logger.error(f"Failed to write email content: {write_result.error}")
            return IntegrationResult.error_result(
                f"Failed to write email content: {write_result.error}"
            )

        return IntegrationResult.success_result(
            content=filepath,  # Use the string representation of the path
            message=f"Email downloaded successfully to {filepath}",
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
) -> Mapping | None:
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
        Mapping | None: The message data if successful, None otherwise.
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
            return cast(Mapping, result)
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


def _extract_header(headers: Sequence[Mapping], name: str, default: str) -> str:
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
    parts: list[Mapping],
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
    html_content = None
    attachments = []
    parts_stack = list(parts)

    while parts_stack:
        part = parts_stack.pop()

        # Process nested parts
        if "parts" in part:
            parts_stack.extend(part["parts"])
            continue

        mime_type = part.get("mimeType", "")

        # Extract HTML content
        if mime_type == "text/html" and html_content is None:
            data = part.get("body", {}).get("data")
            if data is not None:
                # Ensure data is a string before encoding
                data_str = str(data)
                html_content = base64.urlsafe_b64decode(
                    data_str.encode("UTF-8")
                ).decode("UTF-8")

        # Process attachments
        elif part.get("filename"):
            attachment_path = handle_attachment(
                gmail_service, user_id, part, msg_id, storage_path, logger
            )
            if attachment_path:
                attachments.append(attachment_path)

    return html_content, attachments


def handle_attachment(
    gmail_service: GmailService,
    user_id: str,
    part: Mapping,
    msg_id: str,
    storage_path: str,
    logger: logging.Logger,
) -> str | None:
    """
    Download and save an attachment from a message part.

    Args:
        gmail_service: Gmail API service object.
        user_id: Gmail user ID.
        part: Message part dictionary containing attachment data.
        msg_id: The Gmail message ID.
        storage_path: Path to save the attachment.
        logger: Logger instance.

    Returns:
        str | None: Path to the saved attachment or None if failed.
    """
    try:
        filename = part.get("filename")
        if not filename:
            return None

        # Get attachment data
        body = part.get("body", {})
        data = body.get("data")

        # Check if we need to fetch the attachment separately
        if data is None and "attachmentId" in body:
            attachment_id = body["attachmentId"]
            attachment = execute_api_request(
                gmail_service.users()
                .messages()
                .attachments()
                .get(user_id=user_id, message_id=msg_id, attachment_id=attachment_id),
                "Failed to get attachment from Gmail",
                "users.messages.attachments.get",
            )
            data = attachment.get("data")

        if data is None:
            return None

        # Ensure data is a string before decoding
        data_str = str(data)

        # Decode content
        try:
            content = base64.urlsafe_b64decode(data_str)
        except Exception as e:
            logger.error(f"Failed to decode attachment data: {e}")
            return None

        # Process filename and path
        clean_name = clean_filename(filename)

        # Use fs service to join paths
        file_path_obj = fs.join_path(storage_path, clean_name)
        file_path = str(file_path_obj)

        # Handle filename collisions using our fs service
        counter = 1
        file_info = fs.get_file_info(file_path)

        while file_info.exists:
            # Use fs service to split the path and create a new filename
            path_parts = fs.split_path(file_path)
            filename_parts = path_parts[-1].rsplit(".", 1)
            base_name = filename_parts[0]
            ext = f".{filename_parts[1]}" if len(filename_parts) > 1 else ""

            new_filename = f"{base_name}-{counter}{ext}"
            new_file_path_obj = fs.join_path(storage_path, new_filename)
            file_path = str(new_file_path_obj)
            file_info = fs.get_file_info(file_path)
            counter += 1

        # First, ensure the directory exists
        from pathlib import Path

        dir_path = Path(file_path).parent
        dir_result = fs.create_directory(dir_path, exist_ok=True)
        if not dir_result.success:
            logger.error(f"Failed to create directory: {dir_result.error}")
            return None

        # Use the FileSystemService instance to write binary content
        write_result = fs.write_binary(file_path, content)
        if not write_result.success:
            logger.error(f"Failed to write attachment: {write_result.error}")
            return None

        return file_path

    except Exception as e:
        logger.error(f"Error handling attachment: {e}")
        return None
