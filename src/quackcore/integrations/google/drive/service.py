# src/quackcore/integrations/google/drive/service.py
"""
Google Drive integration service for QuackCore.

This module provides the main service class for Google Drive integration,
handling file operations, folder management, and permissions.
"""

import io
import logging
import mimetypes
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from quackcore.errors import QuackApiError, QuackAuthenticationError, \
    QuackIntegrationError
from quackcore.fs import service as fs
from quackcore.integrations.base import BaseIntegrationService
from quackcore.integrations.google.auth import GoogleAuthProvider
from quackcore.integrations.google.config import GoogleConfigProvider
from quackcore.integrations.google.drive.models import DriveFile, DriveFolder
from quackcore.integrations.protocols import StorageIntegrationProtocol
from quackcore.integrations.results import IntegrationResult


class GoogleDriveService(BaseIntegrationService, StorageIntegrationProtocol):
    """Integration service for Google Drive."""

    # Define required Google API scopes
    SCOPES = [
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive.metadata.readonly",
    ]

    def __init__(
            self,
            client_secrets_file: str | Path | None = None,
            credentials_file: str | Path | None = None,
            shared_folder_id: str | None = None,
            config_path: str | Path | None = None,
            scopes: list[str] | None = None,
            log_level: int = logging.INFO,
    ) -> None:
        """
        Initialize the Google Drive integration service.

        Args:
            client_secrets_file: Path to client secrets file
            credentials_file: Path to credentials file
            shared_folder_id: ID of shared folder
            config_path: Path to configuration file
            scopes: OAuth scopes for API access
            log_level: Logging level
        """
        # Initialize config provider
        config_provider = GoogleConfigProvider("drive", log_level)

        # Initialize base service
        super().__init__(config_provider, None, config_path, log_level)

        # Initialize components based on provided parameters or config file
        self.config = self._initialize_config(
            client_secrets_file, credentials_file, shared_folder_id
        )

        # Set up scopes
        self.scopes = scopes or self.SCOPES

        # Initialize authentication provider
        self.auth_provider = GoogleAuthProvider(
            client_secrets_file=self.config["client_secrets_file"],
            credentials_file=self.config["credentials_file"],
            scopes=self.scopes,
            log_level=log_level,
        )

        # Initialize Drive API service
        self.drive_service = None
        self.shared_folder_id = self.config.get("shared_folder_id")

    @property
    def name(self) -> str:
        """Get the name of the integration."""
        return "GoogleDrive"

    def _initialize_config(
            self,
            client_secrets_file: str | Path | None,
            credentials_file: str | Path | None,
            shared_folder_id: str | None,
    ) -> dict[str, Any]:
        """
        Initialize configuration from parameters or config file.

        Args:
            client_secrets_file: Path to client secrets file
            credentials_file: Path to credentials file
            shared_folder_id: ID of shared folder

        Returns:
            dict: Configuration dictionary

        Raises:
            QuackIntegrationError: If configuration initialization fails
        """
        # If all parameters are provided, use them directly
        if client_secrets_file and credentials_file:
            return {
                "client_secrets_file": str(client_secrets_file),
                "credentials_file": str(credentials_file),
                "shared_folder_id": shared_folder_id,
            }

        # Otherwise, load from config file
        config_result = self.config_provider.load_config(self.config_path)

        if not config_result.success or not config_result.content:
            # Try default config as a fallback
            default_config = self.config_provider.get_default_config()

            # Validate default config
            if not self.config_provider.validate_config(default_config):
                raise QuackIntegrationError(
                    "Failed to load configuration and default configuration is invalid"
                )

            return default_config

        # Add provided parameters to override config values
        config = config_result.content
        if client_secrets_file:
            config["client_secrets_file"] = str(client_secrets_file)
        if credentials_file:
            config["credentials_file"] = str(credentials_file)
        if shared_folder_id:
            config["shared_folder_id"] = shared_folder_id

        return config

    def initialize(self) -> IntegrationResult:
        """
        Initialize the Google Drive service.

        Returns:
            IntegrationResult: Result of initialization
        """
        try:
            # Call parent initialization (loads config and authenticates)
            init_result = super().initialize()
            if not init_result.success:
                return init_result

            # Get authenticated credentials
            credentials = self.auth_provider.get_credentials()

            # Initialize the Drive API service
            from googleapiclient.discovery import build

            self.drive_service = build("drive", "v3", credentials=credentials)

            self._initialized = True
            return IntegrationResult.success_result(
                message="Google Drive service initialized successfully"
            )

        except Exception as e:
            self.logger.error(f"Failed to initialize Google Drive service: {e}")
            return IntegrationResult.error_result(
                f"Failed to initialize Google Drive service: {str(e)}"
            )

    def upload_file(
            self,
            file_path: str | Path,
            remote_path: str | None = None,
            description: str | None = None,
            parent_folder_id: str | None = None,
            public: bool | None = None,
    ) -> IntegrationResult[str]:
        """
        Upload a file to Google Drive.

        Args:
            file_path: Path to the file to upload
            remote_path: Optional remote path or title for the file
            description: Optional description for the file
            parent_folder_id: Optional parent folder ID (uses shared_folder_id if not provided)
            public: Optional flag to make the file public

        Returns:
            IntegrationResult[str]: Result with the file ID or sharing link
        """
        # Ensure the service is initialized
        if init_error := self._ensure_initialized():
            return init_error

        try:
            # Resolve the file path
            path_obj = Path(file_path)

            # Verify file exists
            file_info = fs.get_file_info(path_obj)
            if not file_info.success or not file_info.exists:
                return IntegrationResult.error_result(
                    f"File not found: {file_path}"
                )

            # Determine filename
            if remote_path and not remote_path.startswith("/"):
                # If remote_path doesn't start with /, treat it as just the filename
                filename = remote_path
            else:
                # Otherwise, use the original filename
                filename = path_obj.name

            # Determine parent folder ID
            folder_id = parent_folder_id or self.shared_folder_id

            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(str(path_obj))
            if not mime_type:
                mime_type = 'application/octet-stream'

            # Prepare file metadata
            file_metadata = {
                'name': filename,
                'description': description,
                'mimeType': mime_type,
            }

            # Add parent folder if specified
            if folder_id:
                file_metadata['parents'] = [folder_id]

            # Read file content
            media_content = fs.read_binary(path_obj)
            if not media_content.success:
                return IntegrationResult.error_result(
                    f"Failed to read file: {media_content.error}"
                )

            from googleapiclient.http import MediaInMemoryUpload

            # Create media content
            media = MediaInMemoryUpload(
                media_content.content,
                mimetype=mime_type,
                resumable=True
            )

            # Upload the file
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink, webContentLink'
            ).execute()

            # Set permissions if requested
            config_public = self.config.get("public_sharing", True)
            make_public = public if public is not None else config_public

            if make_public:
                self.set_file_permissions(file['id'])

            # Return the sharing link
            if 'webViewLink' in file:
                link = file['webViewLink']
            elif 'webContentLink' in file:
                link = file['webContentLink']
            else:
                link = f"https://drive.google.com/file/d/{file['id']}/view"

            return IntegrationResult.success_result(
                content=link,
                message=f"File uploaded successfully with ID: {file['id']}"
            )

        except Exception as e:
            self.logger.error(f"Failed to upload file: {e}")
            return IntegrationResult.error_result(
                f"Failed to upload file to Google Drive: {str(e)}"
            )

    def download_file(
            self,
            remote_id: str,
            local_path: str | Path | None = None
    ) -> IntegrationResult[Path]:
        """
        Download a file from Google Drive.

        Args:
            remote_id: ID of the remote file
            local_path: Optional local path to save the file

        Returns:
            IntegrationResult[Path]: Result with the local file path
        """
        # Ensure the service is initialized
        if init_error := self._ensure_initialized():
            return init_error

        try:
            # Get file metadata
            file_metadata = self.drive_service.files().get(
                fileId=remote_id,
                fields='name, mimeType'
            ).execute()

            # Determine download path
            if not local_path:
                # Create a temporary file with the same name
                temp_dir = fs.create_temp_directory(prefix="quackcore_gdrive_")
                download_path = Path(temp_dir) / file_metadata['name']
            else:
                download_path = Path(local_path)

                # If local_path is a directory, append the filename
                if download_path.is_dir():
                    download_path = download_path / file_metadata['name']

                # Ensure parent directory exists
                fs.create_directory(download_path.parent, exist_ok=True)

            # Download the file
            request = self.drive_service.files().get_media(fileId=remote_id)
            from googleapiclient.http import MediaIoBaseDownload

            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()
                self.logger.debug(f"Download progress: {int(status.progress() * 100)}%")

            # Save the file
            fh.seek(0)
            write_result = fs.write_binary(download_path, fh.read())
            if not write_result.success:
                return IntegrationResult.error_result(
                    f"Failed to write file: {write_result.error}"
                )

            return IntegrationResult.success_result(
                content=download_path,
                message=f"File downloaded successfully to {download_path}"
            )

        except Exception as e:
            self.logger.error(f"Failed to download file: {e}")
            return IntegrationResult.error_result(
                f"Failed to download file from Google Drive: {str(e)}"
            )

    def list_files(
            self,
            remote_path: str | None = None,
            pattern: str | None = None
    ) -> IntegrationResult[list[Mapping]]:
        """
        List files in Google Drive.

        Args:
            remote_path: Optional folder ID to list files from
            pattern: Optional pattern to match filenames

        Returns:
            IntegrationResult[list[Mapping]]: Result with the list of files
        """
        # Ensure the service is initialized
        if init_error := self._ensure_initialized():
            return init_error

        try:
            # Build the query
            query_parts = []

            # Filter by parent folder if specified
            folder_id = remote_path or self.shared_folder_id
            if folder_id:
                query_parts.append(f"'{folder_id}' in parents")

            # Filter by trashed status
            query_parts.append("trashed = false")

            # Filter by filename pattern if specified
            if pattern:
                if '*' in pattern:
                    # Convert glob pattern to partial match
                    name_pattern = pattern.replace('*', '')
                    if name_pattern:
                        query_parts.append(f"name contains '{name_pattern}'")
                else:
                    # Exact match
                    query_parts.append(f"name = '{pattern}'")

            # Combine query parts
            query = " and ".join(query_parts)

            # List files
            response = self.drive_service.files().list(
                q=query,
                fields="files(id, name, mimeType, webViewLink, webContentLink, size, createdTime, modifiedTime, parents, shared, trashed)",
                pageSize=100
            ).execute()

            # Convert to model objects
            files = []
            for item in response.get('files', []):
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    files.append(DriveFolder.from_api_response(item))
                else:
                    files.append(DriveFile.from_api_response(item))

            return IntegrationResult.success_result(
                content=[file.model_dump() for file in files],
                message=f"Listed {len(files)} files"
            )

        except Exception as e:
            self.logger.error(f"Failed to list files: {e}")
            return IntegrationResult.error_result(
                f"Failed to list files from Google Drive: {str(e)}"
            )

    def create_folder(
            self,
            folder_name: str,
            parent_path: str | None = None
    ) -> IntegrationResult[str]:
        """
        Create a folder in Google Drive.

        Args:
            folder_name: Name of the folder to create
            parent_path: Optional parent folder ID (uses shared_folder_id if not provided)

        Returns:
            IntegrationResult[str]: Result with the folder ID
        """
        # Ensure the service is initialized
        if init_error := self._ensure_initialized():
            return init_error

        try:
            # Determine parent folder ID
            parent_id = parent_path or self.shared_folder_id

            # Prepare folder metadata
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
            }

            # Add parent folder if specified
            if parent_id:
                folder_metadata['parents'] = [parent_id]

            # Create the folder
            folder = self.drive_service.files().create(
                body=folder_metadata,
                fields='id, webViewLink'
            ).execute()

            # Set permissions
            if self.config.get("public_sharing", True):
                self.set_file_permissions(folder['id'])

            return IntegrationResult.success_result(
                content=folder['id'],
                message=f"Folder created successfully with ID: {folder['id']}"
            )

        except Exception as e:
            self.logger.error(f"Failed to create folder: {e}")
            return IntegrationResult.error_result(
                f"Failed to create folder in Google Drive: {str(e)}"
            )

    def set_file_permissions(
            self,
            file_id: str,
            role: str | None = None,
            type_: str = "anyone"
    ) -> IntegrationResult[bool]:
        """
        Set permissions for a file or folder.

        Args:
            file_id: ID of the file or folder
            role: Permission role (reader, writer, commenter, etc.)
            type_: Permission type (anyone, user, domain, etc.)

        Returns:
            IntegrationResult[bool]: Result of permission setting
        """
        # Ensure the service is initialized
        if init_error := self._ensure_initialized():
            return init_error

        try:
            # Use configured role if not specified
            if not role:
                role = self.config.get("default_share_access", "reader")

            # Create permission
            permission = {
                'type': type_,
                'role': role,
                'allowFileDiscovery': True,
            }

            # Set permission
            self.drive_service.permissions().create(
                fileId=file_id,
                body=permission,
                fields='id'
            ).execute()

            return IntegrationResult.success_result(
                content=True,
                message=f"Permission set successfully: {role} for {type_}"
            )

        except Exception as e:
            self.logger.error(f"Failed to set permissions: {e}")
            return IntegrationResult.error_result(
                f"Failed to set permissions in Google Drive: {str(e)}"
            )

    def get_sharing_link(self, file_id: str) -> IntegrationResult[str]:
        """
        Get the sharing link for a file.

        Args:
            file_id: ID of the file

        Returns:
            IntegrationResult[str]: Result with the sharing link
        """
        # Ensure the service is initialized
        if init_error := self._ensure_initialized():
            return init_error

        try:
            # Get file metadata
            file_metadata = self.drive_service.files().get(
                fileId=file_id,
                fields='webViewLink, webContentLink'
            ).execute()

            # Get link
            if 'webViewLink' in file_metadata:
                link = file_metadata['webViewLink']
            elif 'webContentLink' in file_metadata:
                link = file_metadata['webContentLink']
            else:
                link = f"https://drive.google.com/file/d/{file_id}/view"

            return IntegrationResult.success_result(
                content=link,
                message="Got sharing link successfully"
            )

        except Exception as e:
            self.logger.error(f"Failed to get sharing link: {e}")
            return IntegrationResult.error_result(
                f"Failed to get sharing link from Google Drive: {str(e)}"
            )

    def delete_file(self, file_id: str, permanent: bool = False) -> IntegrationResult[
        bool]:
        """
        Delete a file from Google Drive.

        Args:
            file_id: ID of the file to delete
            permanent: Whether to permanently delete the file (bypassing trash)

        Returns:
            IntegrationResult[bool]: Result of deletion
        """
        # Ensure the service is initialized
        if init_error := self._ensure_initialized():
            return init_error

        try:
            if permanent:
                # Permanently delete the file
                self.drive_service.files().delete(fileId=file_id).execute()
            else:
                # Move to trash
                self.drive_service.files().update(
                    fileId=file_id,
                    body={'trashed': True}
                ).execute()

            return IntegrationResult.success_result(
                content=True,
                message=f"File deleted successfully: {file_id}"
            )

        except Exception as e:
            self.logger.error(f"Failed to delete file: {e}")
            return IntegrationResult.error_result(
                f"Failed to delete file from Google Drive: {str(e)}"
            )