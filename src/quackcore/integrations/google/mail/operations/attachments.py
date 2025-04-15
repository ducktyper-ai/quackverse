# src/quackcore/integrations/google/mail/_operations/attachments.py
"""
Upload _operations for Google Mail attachments.

This module provides functions for processing email message parts to extract
HTML content and download attachments, saving them to a given storage path.
All file path values are handled as strings. Filesystem _operations
(like joining paths, checking file existence, creating directories, writing files, etc.)
are delegated to the QuackCore FS layer or Python’s os.path utilities.
"""

import base64
import logging
import os

from quackcore.fs import service as fs
from quackcore.integrations.google.mail.operations.email import clean_filename
from quackcore.integrations.google.mail.protocols import GmailService
from quackcore.integrations.google.mail.utils.api import execute_api_request


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
        storage_path: Path (as a string) where attachments should be saved.
        logger: Logger instance.

    Returns:
        A tuple of HTML content (or None) and a list of attachment file paths (as strings).
    """
    html_content = None
    attachments: list[str] = []
    parts_stack = parts.copy()

    while parts_stack:
        part = parts_stack.pop()

        # Process nested parts
        if "parts" in part:
            parts_stack.extend(part["parts"])
            continue

        mime_type = part.get("mimeType", "")

        # Extract HTML content if not already found
        if mime_type == "text/html" and html_content is None:
            data = part.get("body", {}).get("data")
            if data is not None:
                # Ensure data is a string before encoding
                data_str = str(data)
                html_content = base64.urlsafe_b64decode(
                    data_str.encode("UTF-8")
                ).decode("UTF-8")

        # Process attachments if a filename is present
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
    part: dict,
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
        storage_path: Directory path (as a string) to save the attachment.
        logger: Logger instance.

    Returns:
        The file path (as a string) to the saved attachment, or None if failed.
    """
    try:
        filename = part.get("filename")
        if not filename:
            return None

        # Get attachment data from body or via a separate API call if needed
        body = part.get("body", {})
        data = body.get("data")
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

        # Ensure that data is a string prior to decoding
        data_str = str(data)
        try:
            content = base64.urlsafe_b64decode(data_str)
        except Exception as e:
            logger.error(f"Failed to decode attachment data: {e}")
            return None

        # Process the filename using a helper function
        clean_name = clean_filename(filename)

        # Use the FS service's join_path to create a file path string
        file_path = fs.join_path(storage_path, clean_name)  # file_path is now a string

        # Handle filename collisions: if the file already exists, append a counter
        counter = 1
        file_info = fs.get_file_info(file_path)
        while file_info.success and file_info.exists:
            # Split file_path into directory and filename components using fs.split_path
            path_parts = fs.split_path(file_path)
            # Get last part (the filename) and separate base and extension
            filename_parts = path_parts[-1].rsplit(".", 1)
            base_name = filename_parts[0]
            ext = f".{filename_parts[1]}" if len(filename_parts) > 1 else ""
            new_filename = f"{base_name}-{counter}{ext}"
            file_path = fs.join_path(storage_path, new_filename)
            file_info = fs.get_file_info(file_path)
            counter += 1

        # Ensure the directory where the file should be saved exists.
        dir_path = os.path.dirname(file_path)
        dir_result = fs.create_directory(dir_path, exist_ok=True)
        if not (dir_result.success if hasattr(dir_result, "success") else False):
            logger.error(f"Failed to create directory: {dir_result.error}")
            return None

        # Write binary content to file using the FS service’s write_binary method.
        write_result = fs.write_binary(file_path, content)
        if not (write_result.success if hasattr(write_result, "success") else False):
            logger.error(f"Failed to write attachment: {write_result.error}")
            return None

        return file_path

    except Exception as e:
        logger.error(f"Error handling attachment: {e}")
        return None
