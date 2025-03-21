# src/quackcore/integrations/google/mail/operations/attachments.py
import base64
import logging
from pathlib import Path

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
        storage_path: Path to save attachments.
        logger: Logger instance.

    Returns:
        tuple: HTML content (or None) and list of attachment paths.
    """
    html_content = None
    attachments = []
    parts_stack = parts.copy()

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
        file_path = fs.join_path(storage_path, clean_name)

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
            file_path = fs.join_path(storage_path, new_filename)
            file_info = fs.get_file_info(file_path)
            counter += 1

        # First, ensure the directory exists
        dir_path = Path(file_path).parent
        dir_result = fs.create_directory(dir_path, exist_ok=True)
        if not dir_result.success:
            logger.error(f"Failed to create directory: {dir_result.error}")
            return None

        # Use the FileSystemService instance to write binary content
        # Note: The service has a 'write_binary' method, not the module directly
        write_result = fs.service.write_binary(file_path, content)
        if not write_result.success:
            logger.error(f"Failed to write attachment: {write_result.error}")
            return None

        return str(file_path)

    except Exception as e:
        logger.error(f"Error handling attachment: {e}")
        return None
