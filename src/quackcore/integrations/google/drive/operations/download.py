# src/quackcore/integrations/google/drive/operations/download.py
"""
Download operations for Google Drive integration.

This module provides robust file download functionality with improved error handling.
"""

import io
import logging
from collections.abc import Mapping

from quackcore.errors import QuackApiError
from quackcore.fs import service as fs
from quackcore.integrations.core.results import IntegrationResult
from quackcore.integrations.google.drive.protocols import DriveService
from quackcore.integrations.google.drive.utils.api import execute_api_request
from quackcore.paths import resolver


def resolve_download_path(
    file_metadata: Mapping[str, object], local_path: str | None = None
) -> str:
    """
    Resolve the local path for file download with enhanced path handling.

    Args:
        file_metadata: File metadata from Google Drive.
        local_path: Optional local path to save the file.

    Returns:
        str: The resolved download path.
    """
    file_name = str(file_metadata.get("name", "downloaded_file"))

    if local_path is None:
        # Create a temp directory using fs.create_temp_directory
        temp_dir = fs._create_temp_directory(prefix="gdrive_download_")
        # Use fs.join_path for path joining
        return str(fs._join_path(temp_dir, file_name))

    # Resolve the local path
    local_path_obj = resolver.resolve_project_path(local_path)
    file_info = fs._get_file_info(local_path_obj)

    if file_info.success and file_info.exists:
        # Handle different cases depending on whether local_path is a directory or file
        if file_info.is_dir:
            # If it's a directory, join the file name to it
            joined_path = fs._join_path(local_path_obj, file_name)
            return str(joined_path)
        else:
            # If it's a file, use the path as is
            return str(local_path_obj)

    # If the path doesn't exist, assume it's a file path the user wants to create
    return str(local_path_obj)


def download_file(
    drive_service: DriveService,
    remote_id: str,
    local_path: str | None = None,
    logger: logging.Logger | None = None,
) -> IntegrationResult[str]:
    """
    Download a file from Google Drive.

    Args:
        drive_service: Google Drive service object.
        remote_id: ID of the file to download.
        local_path: Optional local path to save the file.
        logger: Optional logger instance.

    Returns:
        IntegrationResult with the local file path.
    """
    local_logger = logger or logging.getLogger(__name__)

    try:
        # Get file metadata
        try:
            file_metadata = execute_api_request(
                drive_service.files().get(file_id=remote_id, fields="name, mimeType"),
                "Failed to get file metadata from Google Drive",
                "files.get",
            )
        except QuackApiError as metadata_error:
            local_logger.error(f"Metadata retrieval failed: {metadata_error}")
            return IntegrationResult.error_result(
                f"Failed to get file metadata: {metadata_error}"
            )

        # Resolve the download path
        download_path = resolve_download_path(file_metadata, local_path)

        # Ensure parent directory exists
        parent_dir = fs._join_path(download_path).parent
        parent_result = fs.create_directory(parent_dir, exist_ok=True)
        if not parent_result.success:
            return IntegrationResult.error_result(
                f"Failed to create directory: {parent_result.error}"
            )

        # Download the file content
        try:
            request = drive_service.files().get_media(file_id=remote_id)
            from googleapiclient.http import MediaIoBaseDownload

            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()
                local_logger.debug(
                    f"Download progress: {int(status.progress() * 100)}%"
                )
        except Exception as download_error:
            local_logger.error(f"Failed to download file: {download_error}")
            return IntegrationResult.error_result(
                f"Failed to download file from Google Drive: {download_error}"
            )

        # Reset pointer to beginning of the buffer and read content
        fh.seek(0)
        file_content = fh.read()

        # Write file to disk
        write_result = fs.write_binary(download_path, file_content)
        if not write_result.success:
            return IntegrationResult.error_result(
                f"Failed to write file: {write_result.error}"
            )

        return IntegrationResult.success_result(
            content=download_path,
            message=f"File downloaded successfully to {download_path}",
        )

    except Exception as e:
        local_logger.error(f"Unexpected error during file download: {e}")
        return IntegrationResult.error_result(
            f"Failed to download file from Google Drive: {e}"
        )
