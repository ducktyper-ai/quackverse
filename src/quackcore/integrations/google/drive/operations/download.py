# src/quackcore/integrations/google/drive/operations/download.py
"""
Download operations for Google Drive integration.

This module provides functions for downloading files from Google Drive,
including handling file metadata and media download.
"""

import io
import logging
from typing import TypeVar

from googleapiclient.http import MediaIoBaseDownload

from quackcore.errors import QuackApiError
from quackcore.fs import service as fs
from quackcore.integrations.google.drive.protocols import DriveService
from quackcore.integrations.google.drive.utils.api import execute_api_request
from quackcore.integrations.core.results import IntegrationResult
from quackcore.paths import resolver

T = TypeVar("T")  # Generic type for result content


def resolve_download_path(
    file_metadata: dict[str, object], local_path: str | None
) -> str:
    """
    Resolve the local path for file download.

    Args:
        file_metadata: File metadata from Google Drive.
        local_path: Optional local path to save the file.

    Returns:
        str: The resolved download path.
    """
    if not local_path:
        temp_dir = fs.create_temp_directory(prefix="quackcore_gdrive_")
        # Use type assertion to convert from 'object' to 'str'
        file_name = str(file_metadata.get("name", "downloaded_file"))
        return fs.join_path(temp_dir, file_name)

    local_path_obj = resolver.resolve_project_path(local_path)
    file_info = fs.get_file_info(local_path_obj)
    if file_info.success and file_info.exists and file_info.is_dir:
        # Use type assertion to convert from 'object' to 'str'
        file_name = str(file_metadata.get("name", "downloaded_file"))
        return fs.join_path(local_path_obj, file_name)
    return local_path_obj


def download_file(
    drive_service: DriveService,
    file_id: str,
    local_path: str | None = None,
    logger: logging.Logger | None = None,
) -> IntegrationResult[str]:
    """
    Download a file from Google Drive.

    Args:
        drive_service: Google Drive service object.
        file_id: ID of the file to download.
        local_path: Optional local path to save the file.
        logger: Optional logger instance.

    Returns:
        IntegrationResult with the local file path.
    """
    logger = logger or logging.getLogger(__name__)

    try:
        # Get file metadata
        file_metadata = execute_api_request(
            drive_service.files().get(file_id=file_id, fields="name, mimeType"),
            "Failed to get file metadata from Google Drive",
            "files.get",
        )

        # Resolve download path
        download_path = resolve_download_path(file_metadata, local_path)

        # Ensure parent directory exists
        parent_dir = fs.join_path(download_path).parent
        parent_result = fs.create_directory(parent_dir, exist_ok=True)
        if not parent_result.success:
            return IntegrationResult.error_result(
                f"Failed to create directory: {parent_result.error}"
            )

        # Download file content
        request = drive_service.files().get_media(file_id=file_id)

        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            logger.debug(f"Download progress: {int(status.progress() * 100)}%")

        # Write content to file
        fh.seek(0)
        write_result = fs.write_binary(download_path, fh.read())
        if not write_result.success:
            return IntegrationResult.error_result(
                f"Failed to write file: {write_result.error}"
            )

        return IntegrationResult.success_result(
            content=download_path,
            message=f"File downloaded successfully to {download_path}",
        )

    except QuackApiError as e:
        logger.error(f"API error during file download: {e}")
        return IntegrationResult.error_result(f"API error: {e}")
    except Exception as e:
        logger.error(f"Failed to download file: {e}")
        return IntegrationResult.error_result(
            f"Failed to download file from Google Drive: {e}"
        )
