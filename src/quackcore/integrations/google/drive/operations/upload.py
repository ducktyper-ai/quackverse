# src/quackcore/integrations/google/drive/operations/upload.py
"""
Upload operations for Google Drive integration.

This module provides functions for uploading files to Google Drive,
including file metadata handling and media upload.
"""

import logging
from pathlib import Path
from typing import Any

from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload

from quackcore.errors import QuackApiError, QuackIntegrationError
from quackcore.fs import service as fs
from quackcore.integrations.google.drive.operations.permissions import (
    set_file_permissions,
)
from quackcore.integrations.google.drive.protocols import (
    DriveService,
    GoogleCredentials,
)
from quackcore.integrations.google.drive.utils.api import execute_api_request
from quackcore.integrations.core.results import IntegrationResult
from quackcore.paths import resolver


def initialize_drive_service(credentials: GoogleCredentials) -> DriveService:
    """
    Initialize the Google Drive service with provided credentials.

    Args:
        credentials: Google API credentials.

    Returns:
        DriveService: Initialized Drive service object.

    Raises:
        QuackApiError: If service initialization fails.
    """
    try:
        return build("drive", "v3", credentials=credentials)
    except Exception as api_error:
        raise QuackApiError(
            f"Failed to initialize Google Drive API: {api_error}",
            service="Google Drive",
            api_method="build",
            original_error=api_error,
        ) from api_error


def resolve_file_details(
        file_path: str, remote_path: str | None, parent_folder_id: str | None
) -> tuple[str | Path, str, str | None, str]:
    """
    Resolve file details for upload.

    Args:
        file_path: Path to the file to upload.
        remote_path: Optional remote path or name.
        parent_folder_id: Optional parent folder ID.

    Returns:
        tuple: A tuple containing the resolved path, filename, folder ID, and MIME type.

    Raises:
        QuackIntegrationError: If the file does not exist.
    """
    path_obj = resolver.resolve_project_path(file_path)
    file_info = fs.get_file_info(path_obj)
    if not file_info.success or not file_info.exists:
        raise QuackIntegrationError(f"File not found: {file_path}")

    filename = (
        remote_path
        if remote_path and not remote_path.startswith("/")
        else fs.split_path(path_obj)[-1]
    )
    mime_type = fs.get_mime_type(path_obj) or "application/octet-stream"
    return path_obj, filename, parent_folder_id, mime_type


def upload_file(
        drive_service: DriveService,
        file_path: str,
        remote_path: str | None = None,
        description: str | None = None,
        parent_folder_id: str | None = None,
        make_public: bool = True,
        logger: logging.Logger | None = None,
) -> IntegrationResult[str]:
    """
    Upload a file to Google Drive.

    Args:
        drive_service: Google Drive service object.
        file_path: Path to the file to upload.
        remote_path: Optional remote path or name.
        description: Optional file description.
        parent_folder_id: Optional parent folder ID.
        make_public: Whether to make the file publicly accessible.
        logger: Optional logger instance.

    Returns:
        IntegrationResult with the file ID or sharing link.
    """
    logger = logger or logging.getLogger(__name__)

    try:
        # Resolve file details
        path_obj, filename, folder_id, mime_type = resolve_file_details(
            file_path, remote_path, parent_folder_id
        )

        # Prepare file metadata
        file_metadata: dict[str, object] = {
            "name": filename,
            "mimeType": mime_type,
        }

        if description is not None:
            file_metadata["description"] = description

        if folder_id:
            file_metadata["parents"] = [folder_id]

        # Read file content
        media_content = fs.read_binary(path_obj)
        if not media_content.success:
            return IntegrationResult.error_result(
                f"Failed to read file: {media_content.error}"
            )

        # Create media upload object
        media = MediaInMemoryUpload(
            media_content.content, mimetype=mime_type, resumable=True
        )

        # Execute upload
        file = execute_api_request(
            drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id, webViewLink, webContentLink",
            ),
            "Failed to upload file to Google Drive",
            "files.create",
        )

        # Get the file ID as a string
        file_id = str(file["id"])

        # Set permissions if needed
        if make_public:
            perm_result = set_file_permissions(
                drive_service, file_id, "reader", "anyone", logger
            )
            if not perm_result.success:
                logger.warning(f"Failed to set permissions: {perm_result.error}")

        # Extract link with explicit type annotation
        link: str = (
                str(file.get("webViewLink", ""))
                or str(file.get("webContentLink", ""))
                or f"https://drive.google.com/file/d/{file_id}/view"
        )

        # Now the type checker knows link is a string
        return IntegrationResult.success_result(
            content=link,
            message=f"File uploaded successfully with ID: {file_id}",
        )

    except QuackApiError as e:
        logger.error(f"API error during file upload: {e}")
        return IntegrationResult.error_result(f"API error: {e}")
    except QuackIntegrationError as e:
        logger.error(f"Integration error during file upload: {e}")
        return IntegrationResult.error_result(str(e))
    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        return IntegrationResult.error_result(
            f"Failed to upload file to Google Drive: {e}"
        )