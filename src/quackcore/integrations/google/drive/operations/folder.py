# src/quackcore/integrations/google/drive/operations/folder.py
"""
Folder operations for Google Drive integration.

This module provides functions for managing folders in Google Drive,
including creating folders and deleting files or folders.
"""

import logging

from quackcore.errors import QuackApiError
from quackcore.integrations.google.drive.operations.permissions import (
    set_file_permissions,
)
from quackcore.integrations.google.drive.protocols import DriveService
from quackcore.integrations.google.drive.utils.api import execute_api_request
from quackcore.integrations.results import IntegrationResult


def create_folder(
        drive_service: DriveService,
        folder_name: str,
        parent_id: str | None = None,
        make_public: bool = True,
        logger: logging.Logger | None = None,
) -> IntegrationResult[str]:
    """
    Create a folder in Google Drive.

    Args:
        drive_service: Google Drive service object.
        folder_name: Name of the folder to create.
        parent_id: Optional parent folder ID.
        make_public: Whether to make the folder publicly accessible.
        logger: Optional logger instance.

    Returns:
        IntegrationResult with the folder ID.
    """
    logger = logger or logging.getLogger(__name__)

    try:
        # Prepare folder metadata
        folder_metadata: dict[str, object] = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_id:
            folder_metadata["parents"] = [parent_id]

        # Create folder
        folder = execute_api_request(
            drive_service.files().create(
                body=folder_metadata, fields="id, webViewLink"
            ),
            "Failed to create folder in Google Drive",
            "files.create",
        )

        # Set permissions if needed
        if make_public:
            perm_result = set_file_permissions(
                drive_service, str(folder["id"]), "reader", "anyone", logger
            )
            if not perm_result.success:
                logger.warning(f"Failed to set permissions: {perm_result.error}")

        return IntegrationResult.success_result(
            content=str(folder["id"]),
            message=f"Folder created successfully with ID: {folder['id']}",
        )

    except QuackApiError as e:
        logger.error(f"API error during folder creation: {e}")
        return IntegrationResult.error_result(f"API error: {e}")
    except Exception as e:
        logger.error(f"Failed to create folder: {e}")
        return IntegrationResult.error_result(
            f"Failed to create folder in Google Drive: {e}"
        )


def delete_file(
        drive_service: DriveService,
        file_id: str,
        permanent: bool = False,
        logger: logging.Logger | None = None,
) -> IntegrationResult[bool]:
    """
    Delete a file or folder from Google Drive.

    Args:
        drive_service: Google Drive service object.
        file_id: ID of the file or folder to delete.
        permanent: Whether to permanently delete or move to trash.
        logger: Optional logger instance.

    Returns:
        IntegrationResult indicating success.
    """
    logger = logger or logging.getLogger(__name__)

    try:
        if permanent:
            # Permanently delete
            execute_api_request(
                drive_service.files().delete(file_id=file_id),
                "Failed to delete file from Google Drive",
                "files.delete",
            )
        else:
            # Move to trash
            execute_api_request(
                drive_service.files().update(file_id=file_id, body={"trashed": True}),
                "Failed to trash file in Google Drive",
                "files.update",
            )

        action = "permanently deleted" if permanent else "moved to trash"
        message = f"File {action} successfully: {file_id}"

        return IntegrationResult.success_result(
            content=True,
            message=message,
        )

    except QuackApiError as e:
        logger.error(f"API error during file deletion: {e}")
        return IntegrationResult.error_result(f"API error: {e}")
    except Exception as e:
        logger.error(f"Failed to delete file: {e}")
        return IntegrationResult.error_result(
            f"Failed to delete file from Google Drive: {e}"
        )