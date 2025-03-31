# src/quackcore/integrations/google/drive/operations/download.py
"""
Download operations for Google Drive integration.

This module provides robust file download functionality with improved error handling.
"""

import io
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from googleapiclient.http import MediaIoBaseDownload

from quackcore.errors import QuackApiError
from quackcore.fs import service as fs
from quackcore.fs.operations import FileSystemOperations
from quackcore.integrations.core.results import IntegrationResult
from quackcore.integrations.google.drive.protocols import DriveService
from quackcore.integrations.google.drive.utils.api import execute_api_request
from quackcore.paths import resolver


def resolve_download_path(
    file_metadata: dict[str, Any], local_path: str | None = None
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
        # Create a temporary directory with a more descriptive prefix
        temp_dir = fs.create_temp_directory(prefix="gdrive_download_")
        return fs.join_path(temp_dir, file_name)

    # Resolve the local path with more robust handling
    local_path_obj = resolver.resolve_project_path(local_path)
    file_info = fs.get_file_info(local_path_obj)

    if file_info.success and file_info.exists:
        return (
            fs.join_path(local_path_obj, file_name)
            if file_info.is_dir
            else local_path_obj
        )

    # If path doesn't exist, assume it's a file path the user wants to create
    return local_path_obj


def download_file(
        self, remote_id: str, local_path: str | None = None
) -> IntegrationResult[str]:
    if init_error := self._ensure_initialized():
        return init_error

    try:
        try:
            # First, check file permissions and metadata
            file_metadata = execute_api_request(
                self.drive_service.files().get(
                    fileId=remote_id,
                    fields="id,name,mimeType,permissions,shared"
                ),
                "Failed to get file metadata from Google Drive",
                "files.get"
            )
        except Exception as metadata_error:
            self.logger.error(f"Metadata retrieval failed: {metadata_error}")
            return IntegrationResult.error_result(
                f"Metadata retrieval failed: {metadata_error}"
            )

        # Log permission details for debugging
        self.logger.info(f"File metadata: {file_metadata}")
        self.logger.info(f"Permissions: {file_metadata.get('permissions', [])}")

        try:
            # Attempt media download with explicit handling
            request = self.drive_service.files().get_media(fileId=remote_id)
            fh = io.BytesIO()

            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()

            fh.seek(0)
            file_content = fh.read()
        except HttpError as http_error:
            # More detailed error logging
            self.logger.error(f"HttpError during download: {http_error}")
            self.logger.error(f"Error details: {http_error.resp}")
            self.logger.error(f"Error content: {http_error.content}")

            # Specific handling for authorization errors
            if http_error.resp.status == 403:
                return IntegrationResult.error_result(
                    "Authorization failed. Ensure the file is shared and the app has permissions. "
                    f"Error details: {http_error}"
                )
            raise

        # Resolve download path
        download_path = self._resolve_download_path(file_metadata, local_path)

        # Ensure parent directory exists
        parent_dir = Path(download_path).parent
        parent_result = fs.create_directory(parent_dir, exist_ok=True)
        if not parent_result.success:
            return IntegrationResult.error_result(
                f"Directory creation failed: {parent_result.error}"
            )

        # Write file
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
        self.logger.exception("Comprehensive download error")
        return IntegrationResult.error_result(
            f"Comprehensive download failure: {e}"
        )