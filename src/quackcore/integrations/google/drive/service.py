"""
Google Drive integration service for QuackCore.

This module provides the main service class for Google Drive integration,
handling file operations, folder management, and permissions.
"""

import io
import logging
from collections.abc import Mapping
from typing import Any, TypeVar

from quackcore.errors import (
    QuackApiError,
    QuackBaseAuthError,
    QuackIntegrationError,
)
from quackcore.fs import service as fs
from quackcore.integrations.base import BaseIntegrationService
from quackcore.integrations.google.auth import GoogleAuthProvider
from quackcore.integrations.google.config import GoogleConfigProvider
from quackcore.integrations.google.drive.models import DriveFile, DriveFolder
from quackcore.integrations.protocols import StorageIntegrationProtocol
from quackcore.integrations.results import IntegrationResult
from quackcore.paths import resolver

NoneType = type(None)
T = TypeVar("T")  # Generic type for result content


class GoogleDriveService(BaseIntegrationService, StorageIntegrationProtocol):
    """Integration service for Google Drive."""

    SCOPES: list[str] = [
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive.metadata.readonly",
    ]

    def __init__(
        self,
        client_secrets_file: str | None = None,
        credentials_file: str | None = None,
        shared_folder_id: str | None = None,
        config_path: str | None = None,
        scopes: list[str] | None = None,
        log_level: int = logging.INFO,
    ) -> None:
        """
        Initialize the Google Drive integration service.

        Args:
            client_secrets_file: Path to client secrets file.
            credentials_file: Path to credentials file.
            shared_folder_id: ID of shared folder.
            config_path: Path to configuration file.
            scopes: OAuth scopes for API access.
            log_level: Logging level.
        """
        config_provider = GoogleConfigProvider("drive", log_level)
        super().__init__(config_provider, None, config_path, log_level)

        self.config: dict[str, Any] = self._initialize_config(
            client_secrets_file, credentials_file, shared_folder_id
        )
        self.scopes: list[str] = scopes or self.SCOPES
        self.auth_provider = GoogleAuthProvider(
            client_secrets_file=self.config["client_secrets_file"],
            credentials_file=self.config["credentials_file"],
            scopes=self.scopes,
            log_level=log_level,
        )
        self.drive_service: Any = None
        self.shared_folder_id: str | None = self.config.get("shared_folder_id")

    @property
    def name(self) -> str:
        """Get the name of the integration."""
        return "GoogleDrive"

    def _initialize_config(
        self,
        client_secrets_file: str | None,
        credentials_file: str | None,
        shared_folder_id: str | None,
    ) -> dict[str, Any]:
        """
        Initialize configuration from parameters or config file.

        Raises:
            QuackIntegrationError: If configuration initialization fails.
        """
        if client_secrets_file and credentials_file:
            return {
                "client_secrets_file": client_secrets_file,
                "credentials_file": credentials_file,
                "shared_folder_id": shared_folder_id,
            }

        config_result = self.config_provider.load_config(self.config_path)
        if not config_result.success or not config_result.content:
            default_config = self.config_provider.get_default_config()
            if not self.config_provider.validate_config(default_config):
                raise QuackIntegrationError(
                    "Failed to load configuration and default configuration is invalid",
                    {"provider": self.config_provider.name},
                )
            return default_config

        config = config_result.content
        if client_secrets_file:
            config["client_secrets_file"] = client_secrets_file
        if credentials_file:
            config["credentials_file"] = credentials_file
        if shared_folder_id:
            config["shared_folder_id"] = shared_folder_id
        return config

    def initialize(self) -> IntegrationResult[NoneType]:
        """
        Initialize the Google Drive service.

        Returns:
            IntegrationResult: Result of initialization.
        """
        try:
            init_result = super().initialize()
            if not init_result.success:
                return init_result

            try:
                credentials = self.auth_provider.get_credentials()
            except QuackBaseAuthError as auth_error:
                self.logger.error(f"Authentication failed: {auth_error}")
                return IntegrationResult.error_result(
                    f"Failed to authenticate with Google Drive: {auth_error}"
                )

            try:
                from googleapiclient.discovery import build

                self.drive_service = build("drive", "v3", credentials=credentials)
            except Exception as api_error:
                raise QuackApiError(
                    f"Failed to initialize Google Drive API: {api_error}",
                    service="Google Drive",
                    api_method="build",
                    original_error=api_error,
                ) from api_error

            self._initialized = True
            return IntegrationResult.success_result(
                message="Google Drive service initialized successfully"
            )

        except QuackApiError as e:
            self.logger.error(f"API error during initialization: {e}")
            return IntegrationResult.error_result(f"API error: {e}")
        except QuackBaseAuthError as e:
            self.logger.error(f"Authentication error during initialization: {e}")
            return IntegrationResult.error_result(f"Authentication error: {e}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Google Drive service: {e}")
            return IntegrationResult.error_result(
                f"Failed to initialize Google Drive service: {e}"
            )

    # --- Helper Methods for Refactoring ---

    def _resolve_file_details(
        self, file_path: str, remote_path: str | None, parent_folder_id: str | None
    ) -> tuple[Any, str, str | None, str]:
        """
        Resolve file details for upload.

        Returns:
            A tuple containing the resolved path object,
            filename, folder ID, and MIME type.

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
        folder_id = parent_folder_id or self.shared_folder_id
        mime_type = fs.get_mime_type(path_obj) or "application/octet-stream"
        return path_obj, filename, folder_id, mime_type

    def _resolve_download_path(
        self, file_metadata: dict[str, Any], local_path: str | None
    ) -> str:
        """
        Resolve the local path for file download.

        Returns:
            The resolved download path.
        """
        if not local_path:
            temp_dir = fs.create_temp_directory(prefix="quackcore_gdrive_")
            return fs.join_path(temp_dir, file_metadata["name"])
        local_path_obj = resolver.resolve_project_path(local_path)
        file_info = fs.get_file_info(local_path_obj)
        if file_info.success and file_info.exists and file_info.is_dir:
            return fs.join_path(local_path_obj, file_metadata["name"])
        return local_path_obj

    def _build_query(self, remote_path: str | None, pattern: str | None) -> str:
        """
        Build the query string for listing files.

        Returns:
            The query string.
        """
        query_parts: list[str] = []
        folder_id = remote_path or self.shared_folder_id
        if folder_id:
            query_parts.append(f"'{folder_id}' in parents")
        query_parts.append("trashed = false")
        if pattern:
            if "*" in pattern:
                name_pattern = pattern.replace("*", "")
                if name_pattern:
                    query_parts.append(f"name contains '{name_pattern}'")
            else:
                query_parts.append(f"name = '{pattern}'")
        return " and ".join(query_parts)

    def _execute_upload(
        self, file_metadata: dict[str, Any], media: T
    ) -> dict[str, Any]:
        """
        Execute the file upload to Google Drive.

        Returns:
            The API response as a dict.
        """
        try:
            file = (
                self.drive_service.files()
                .create(
                    body=file_metadata,
                    media_body=media,
                    fields="id, webViewLink, webContentLink",
                )
                .execute()
            )
            return file
        except Exception as api_error:
            raise QuackApiError(
                f"Failed to upload file to Google Drive: {api_error}",
                service="Google Drive",
                api_method="files.create",
                original_error=api_error,
            ) from api_error

    # --- End of Helper Methods ---

    def upload_file(
        self,
        file_path: str,
        remote_path: str | None = None,
        description: str | None = None,
        parent_folder_id: str | None = None,
        public: bool | None = None,
    ) -> IntegrationResult[str]:
        """
        Upload a file to Google Drive.

        Returns:
            IntegrationResult with the file ID or sharing link.
        """
        if init_error := self._ensure_initialized():
            return init_error

        try:
            try:
                path_obj, filename, folder_id, mime_type = self._resolve_file_details(
                    file_path, remote_path, parent_folder_id
                )
            except QuackIntegrationError as e:
                return IntegrationResult.error_result(str(e))

            file_metadata: dict[str, Any] = {
                "name": filename,
                "description": description,
                "mimeType": mime_type,
            }
            if folder_id:
                file_metadata["parents"] = [folder_id]

            media_content = fs.read_binary(path_obj)
            if not media_content.success:
                return IntegrationResult.error_result(
                    f"Failed to read file: {media_content.error}"
                )

            from googleapiclient.http import MediaInMemoryUpload

            media = MediaInMemoryUpload(
                media_content.content, mimetype=mime_type, resumable=True
            )
            file = self._execute_upload(file_metadata, media)

            config_public = self.config.get("public_sharing", True)
            make_public = public if public is not None else config_public
            if make_public:
                # file["id"] is expected to be a str here.
                perm_result = self.set_file_permissions(file["id"])
                if not perm_result.success:
                    self.logger.warning(
                        f"Failed to set permissions: {perm_result.error}"
                    )

            link = (
                file.get("webViewLink")
                or file.get("webContentLink")
                or f"https://drive.google.com/file/d/{file['id']}/view"
            )
            return IntegrationResult.success_result(
                content=link,
                message=f"File uploaded successfully with ID: {file['id']}",
            )

        except QuackApiError as e:
            self.logger.error(f"API error during file upload: {e}")
            return IntegrationResult.error_result(f"API error: {e}")
        except QuackBaseAuthError as e:
            self.logger.error(f"Authentication error during file upload: {e}")
            return IntegrationResult.error_result(f"Authentication error: {e}")
        except Exception as e:
            self.logger.error(f"Failed to upload file: {e}")
            return IntegrationResult.error_result(
                f"Failed to upload file to Google Drive: {e}"
            )

    def download_file(
        self, remote_id: str, local_path: str | None = None
    ) -> IntegrationResult[str]:
        """
        Download a file from Google Drive.

        Returns:
            IntegrationResult with the local file path.
        """
        if init_error := self._ensure_initialized():
            return init_error

        try:
            try:
                file_metadata = (
                    self.drive_service.files()
                    .get(fileId=remote_id, fields="name, mimeType")
                    .execute()
                )
            except Exception as api_error:
                raise QuackApiError(
                    f"Failed to get file metadata from Google Drive: {api_error}",
                    service="Google Drive",
                    api_method="files.get",
                    original_error=api_error,
                ) from api_error

            download_path = self._resolve_download_path(file_metadata, local_path)
            parent_dir = fs.join_path(download_path).parent
            parent_result = fs.create_directory(parent_dir, exist_ok=True)
            if not parent_result.success:
                return IntegrationResult.error_result(
                    f"Failed to create directory: {parent_result.error}"
                )

            try:
                request = self.drive_service.files().get_media(fileId=remote_id)
                from googleapiclient.http import MediaIoBaseDownload

                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    self.logger.debug(
                        f"Download progress: {int(status.progress() * 100)}%"
                    )
            except Exception as api_error:
                raise QuackApiError(
                    f"Failed to download file from Google Drive: {api_error}",
                    service="Google Drive",
                    api_method="files.get_media",
                    original_error=api_error,
                ) from api_error

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
            self.logger.error(f"API error during file download: {e}")
            return IntegrationResult.error_result(f"API error: {e}")
        except QuackBaseAuthError as e:
            self.logger.error(f"Authentication error during file download: {e}")
            return IntegrationResult.error_result(f"Authentication error: {e}")
        except Exception as e:
            self.logger.error(f"Failed to download file: {e}")
            return IntegrationResult.error_result(
                f"Failed to download file from Google Drive: {e}"
            )

    def list_files(
        self, remote_path: str | None = None, pattern: str | None = None
    ) -> IntegrationResult[list[Mapping]]:
        """
        List files in Google Drive.

        Returns:
            IntegrationResult with the list of files.
        """
        if init_error := self._ensure_initialized():
            return init_error

        try:
            query = self._build_query(remote_path, pattern)
            try:
                response = (
                    self.drive_service.files()
                    .list(
                        q=query,
                        fields=(
                            "files(id, name, mimeType, webViewLink, webContentLink, "
                            "size, createdTime, modifiedTime, parents, shared, trashed)"
                        ),
                        pageSize=100,
                    )
                    .execute()
                )
            except Exception as api_error:
                raise QuackApiError(
                    f"Failed to list files from Google Drive: {api_error}",
                    service="Google Drive",
                    api_method="files.list",
                    original_error=api_error,
                ) from api_error

            files: list = []
            for item in response.get("files", []):
                if item["mimeType"] == "application/vnd.google-apps.folder":
                    files.append(DriveFolder.from_api_response(item))
                else:
                    files.append(DriveFile.from_api_response(item))

            return IntegrationResult.success_result(
                content=[file.model_dump() for file in files],
                message=f"Listed {len(files)} files",
            )

        except QuackApiError as e:
            self.logger.error(f"API error during listing files: {e}")
            return IntegrationResult.error_result(f"API error: {e}")
        except QuackBaseAuthError as e:
            self.logger.error(f"Authentication error during listing files: {e}")
            return IntegrationResult.error_result(f"Authentication error: {e}")
        except Exception as e:
            self.logger.error(f"Failed to list files: {e}")
            return IntegrationResult.error_result(
                f"Failed to list files from Google Drive: {e}"
            )

    def create_folder(
        self, folder_name: str, parent_path: str | None = None
    ) -> IntegrationResult[str]:
        """
        Create a folder in Google Drive.

        Returns:
            IntegrationResult with the folder ID.
        """
        if init_error := self._ensure_initialized():
            return init_error

        try:
            parent_id = parent_path or self.shared_folder_id
            folder_metadata: dict[str, Any] = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
            }
            if parent_id:
                folder_metadata["parents"] = [parent_id]

            try:
                folder = (
                    self.drive_service.files()
                    .create(body=folder_metadata, fields="id, webViewLink")
                    .execute()
                )
            except Exception as api_error:
                raise QuackApiError(
                    f"Failed to create folder in Google Drive: {api_error}",
                    service="Google Drive",
                    api_method="files.create",
                    original_error=api_error,
                ) from api_error

            if self.config.get("public_sharing", True):
                perm_result = self.set_file_permissions(folder["id"])
                if not perm_result.success:
                    self.logger.warning(
                        f"Failed to set permissions: {perm_result.error}"
                    )

            return IntegrationResult.success_result(
                content=folder["id"],
                message=f"Folder created successfully with ID: {folder['id']}",
            )

        except QuackApiError as e:
            self.logger.error(f"API error during folder creation: {e}")
            return IntegrationResult.error_result(f"API error: {e}")
        except QuackBaseAuthError as e:
            self.logger.error(f"Authentication error during folder creation: {e}")
            return IntegrationResult.error_result(f"Authentication error: {e}")
        except Exception as e:
            self.logger.error(f"Failed to create folder: {e}")
            return IntegrationResult.error_result(
                f"Failed to create folder in Google Drive: {e}"
            )

    def set_file_permissions(
        self, file_id: str, role: str | None = None, type_: str = "anyone"
    ) -> IntegrationResult[bool]:
        """
        Set permissions for a file or folder.

        Returns:
            IntegrationResult indicating success.
        """
        if init_error := self._ensure_initialized():
            return init_error

        try:
            role = role or self.config.get("default_share_access", "reader")
            permission = {"type": type_, "role": role, "allowFileDiscovery": True}
            try:
                self.drive_service.permissions().create(
                    fileId=file_id, body=permission, fields="id"
                ).execute()
            except Exception as api_error:
                raise QuackApiError(
                    f"Failed to set permissions in Google Drive: {api_error}",
                    service="Google Drive",
                    api_method="permissions.create",
                    original_error=api_error,
                ) from api_error

            return IntegrationResult.success_result(
                content=True, message=f"Permission set successfully: {role} for {type_}"
            )

        except QuackApiError as e:
            self.logger.error(f"API error during setting permissions: {e}")
            return IntegrationResult.error_result(f"API error: {e}")
        except QuackBaseAuthError as e:
            self.logger.error(f"Authentication error during setting permissions: {e}")
            return IntegrationResult.error_result(f"Authentication error: {e}")
        except Exception as e:
            self.logger.error(f"Failed to set permissions: {e}")
            return IntegrationResult.error_result(
                f"Failed to set permissions in Google Drive: {e}"
            )

    def get_sharing_link(self, file_id: str) -> IntegrationResult[str]:
        """
        Get the sharing link for a file.

        Returns:
            IntegrationResult with the sharing link.
        """
        if init_error := self._ensure_initialized():
            return init_error

        try:
            try:
                file_metadata = (
                    self.drive_service.files()
                    .get(fileId=file_id, fields="webViewLink, webContentLink")
                    .execute()
                )
            except Exception as api_error:
                raise QuackApiError(
                    f"Failed to get file metadata from Google Drive: {api_error}",
                    service="Google Drive",
                    api_method="files.get",
                    original_error=api_error,
                ) from api_error

            link = (
                file_metadata.get("webViewLink")
                or file_metadata.get("webContentLink")
                or f"https://drive.google.com/file/d/{file_id}/view"
            )
            return IntegrationResult.success_result(
                content=link, message="Got sharing link successfully"
            )

        except QuackApiError as e:
            self.logger.error(f"API error during getting sharing link: {e}")
            return IntegrationResult.error_result(f"API error: {e}")
        except QuackBaseAuthError as e:
            self.logger.error(f"Authentication error during getting sharing link: {e}")
            return IntegrationResult.error_result(f"Authentication error: {e}")
        except Exception as e:
            self.logger.error(f"Failed to get sharing link: {e}")
            return IntegrationResult.error_result(
                f"Failed to get sharing link from Google Drive: {e}"
            )

    def delete_file(
        self, file_id: str, permanent: bool = False
    ) -> IntegrationResult[bool]:
        """
        Delete a file from Google Drive.

        Returns:
            IntegrationResult indicating success.
        """
        if init_error := self._ensure_initialized():
            return init_error

        try:
            try:
                if permanent:
                    self.drive_service.files().delete(fileId=file_id).execute()
                else:
                    self.drive_service.files().update(
                        fileId=file_id, body={"trashed": True}
                    ).execute()
            except Exception as api_error:
                api_method = "files.delete" if permanent else "files.update"
                raise QuackApiError(
                    f"Failed to delete file from Google Drive: {api_error}",
                    service="Google Drive",
                    api_method=api_method,
                    original_error=api_error,
                ) from api_error

            return IntegrationResult.success_result(
                content=True, message=f"File deleted successfully: {file_id}"
            )

        except QuackApiError as e:
            self.logger.error(f"API error during file deletion: {e}")
            return IntegrationResult.error_result(f"API error: {e}")
        except QuackBaseAuthError as e:
            self.logger.error(f"Authentication error during file deletion: {e}")
            return IntegrationResult.error_result(f"Authentication error: {e}")
        except Exception as e:
            self.logger.error(f"Failed to delete file: {e}")
            return IntegrationResult.error_result(
                f"Failed to delete file from Google Drive: {e}"
            )
