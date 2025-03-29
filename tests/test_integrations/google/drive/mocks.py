# tests/test_integrations/google/drive/mocks.py
"""
Mock objects for Google Drive service testing.

This module provides mock implementations of Google Drive service objects
that can be used across different test modules.
"""

import io
from typing import Any, TypeVar, cast

from quackcore.integrations.google.drive.protocols import (
    DriveFilesResource,
    DrivePermissionsResource,
    DriveRequest,
    DriveService,
    GoogleCredentials,
)

T = TypeVar("T")  # Generic type for content
R = TypeVar("R")  # Generic type for return values


class MockDriveRequest(DriveRequest[R]):
    """Mock request object with configurable response."""

    def __init__(self, return_value: R, error: Exception | None = None):
        """
        Initialize a mock request with a return value or error.

        Args:
            return_value: Value to return on execute()
            error: Exception to raise on execute(), if any
        """
        self.return_value = return_value
        self.error = error
        self.call_count = 0

        # Add attributes that MediaIoBaseDownload requires
        self.uri = "https://www.googleapis.com/drive/v3/files/mock-file-id?alt=media"
        self.headers = {"Content-Type": "application/octet-stream"}
        self._body = {}  # Add _body attribute to simulate the body property

    def execute(self) -> R:
        """
        Execute the request and return the result or raise configured error.

        Returns:
            The configured return value

        Raises:
            Exception: The configured error, if any
        """
        self.call_count += 1
        if self.error:
            raise self.error
        return self.return_value


class MockDrivePermissionsResource(DrivePermissionsResource):
    """Mock permissions resource with configurable behavior."""

    def __init__(self, permission_id: str = "perm123", error: Exception | None = None):
        """
        Initialize mock permissions resource.

        Args:
            permission_id: ID to return for created permissions
            error: Exception to raise on API calls, if any
        """
        self.permission_id = permission_id
        self.error = error

        # Tracking attributes for assertions
        self.last_file_id: str | None = None
        self.last_permission_body: dict[str, object] | None = None
        self.last_fields: str | None = None
        self.create_call_count = 0

    def create(
            self, file_id: str, body: dict[str, object], fields: str
    ) -> DriveRequest[dict[str, object]]:
        """
        Mock create method for creating a permission.

        Args:
            file_id: ID of the file
            body: Permission data
            fields: Fields to include in the response

        Returns:
            A mock request that will return the permission data
        """
        self.create_call_count += 1
        self.last_file_id = file_id
        self.last_permission_body = body
        self.last_fields = fields

        request = MockDriveRequest({"id": self.permission_id}, self.error)
        request._body = body
        return request


class MockDriveFilesResource(DriveFilesResource):
    """Mock files resource with configurable behavior."""

    def __init__(
            self,
            file_id: str = "file123",
            file_metadata: dict[str, Any] | None = None,
            file_list: list[dict[str, Any]] | None = None,
            permissions_resource: DrivePermissionsResource | None = None,
            create_error: Exception | None = None,
            get_error: Exception | None = None,
            get_media_error: Exception | None = None,
            list_error: Exception | None = None,
            update_error: Exception | None = None,
            delete_error: Exception | None = None,
    ):
        """
        Initialize mock files resource.

        Args:
            file_id: ID to return for created files
            file_metadata: Metadata to return for file operations
            file_list: List of files to return in list operation
            permissions_resource: Mock permissions resource to use
            create_error: Exception to raise on create operation, if any
            get_error: Exception to raise on get operation, if any
            get_media_error: Exception to raise on get_media operation, if any
            list_error: Exception to raise on list operation, if any
            update_error: Exception to raise on update operation, if any
            delete_error: Exception to raise on delete operation, if any
        """
        self._permissions = permissions_resource or MockDrivePermissionsResource()
        self.file_id = file_id
        self.file_metadata = file_metadata or {
            "id": self.file_id,
            "name": "test_file.txt",
            "mimeType": "text/plain",
            "webViewLink": f"https://drive.google.com/file/d/{self.file_id}/view",
            "webContentLink": f"https://drive.google.com/uc?id={self.file_id}",
        }
        self.file_list = file_list or [
            {
                "id": "file1",
                "name": "test1.txt",
                "mimeType": "text/plain",
            },
            {
                "id": "folder1",
                "name": "Test Folder",
                "mimeType": "application/vnd.google-apps.folder",
            },
        ]

        # Store error configurations
        self.create_error = create_error
        self.get_error = get_error
        self.get_media_error = get_media_error
        self.list_error = list_error
        self.update_error = update_error
        self.delete_error = delete_error

        # Tracking attributes for assertions
        self.create_call_count = 0
        self.get_call_count = 0
        self.get_media_call_count = 0
        self.list_call_count = 0
        self.update_call_count = 0
        self.delete_call_count = 0

        self.last_create_body: dict[str, object] | None = None
        self.last_create_media_body: Any = None
        self.last_create_fields: str | None = None

        self.last_get_file_id: str | None = None
        self.last_get_fields: str | None = None

        self.last_get_media_file_id: str | None = None

        self.last_list_query: str | None = None
        self.last_list_fields: str | None = None
        self.last_list_page_size: int | None = None

        self.last_update_file_id: str | None = None
        self.last_update_body: dict[str, object] | None = None
        self.last_update_fields: str | None = None

        self.last_delete_file_id: str | None = None

    def create(
            self,
            body: dict[str, object],
            media_body: object | None = None,
            fields: str | None = None,
    ) -> DriveRequest[dict[str, object]]:
        """
        Mock create method for creating a file.

        Args:
            body: File metadata
            media_body: File content
            fields: Fields to include in the response

        Returns:
            A mock request that will return the file data
        """
        self.create_call_count += 1
        self.last_create_body = body
        self.last_create_media_body = media_body
        self.last_create_fields = fields

        request = MockDriveRequest(self.file_metadata, self.create_error)
        request._body = body
        return request

    def get(self, file_id: str, fields: str | None = None) -> DriveRequest[dict[str, object]]:
        """
        Mock get method for retrieving a file's metadata.

        Args:
            file_id: ID of the file
            fields: Fields to include in the response

        Returns:
            A mock request that will return the file metadata
        """
        self.get_call_count += 1
        self.last_get_file_id = file_id
        self.last_get_fields = fields

        return MockDriveRequest(self.file_metadata, self.get_error)

    def get_media(self, file_id: str) -> DriveRequest[bytes]:
        """
        Mock get_media method for downloading a file's content.

        Args:
            file_id: ID of the file

        Returns:
            A mock request that will return the file content
        """
        self.get_media_call_count += 1
        self.last_get_media_file_id = file_id

        # Default file content as bytes
        file_content = b"Test file content"

        return cast(
            DriveRequest[bytes], MockDriveRequest(file_content, self.get_media_error)
        )

    def list(
            self, q: str | None = None, fields: str | None = None, page_size: int | None = None
    ) -> DriveRequest[dict[str, object]]:
        """
        Mock list method for listing files.

        Args:
            q: Query string
            fields: Fields to include in the response
            page_size: Maximum number of files to return

        Returns:
            A mock request that will return the files list
        """
        self.list_call_count += 1
        self.last_list_query = q
        self.last_list_fields = fields
        self.last_list_page_size = page_size

        # Customize response based on query
        response = {"files": self.file_list}

        return MockDriveRequest(response, self.list_error)

    def update(
            self, file_id: str, body: dict[str, object], fields: str | None = None
    ) -> DriveRequest[dict[str, object]]:
        """
        Mock update method for updating a file's metadata.

        Args:
            file_id: ID of the file
            body: Updated metadata
            fields: Fields to include in the response

        Returns:
            A mock request that will return the updated file metadata
        """
        self.update_call_count += 1
        self.last_update_file_id = file_id
        self.last_update_body = body
        self.last_update_fields = fields

        # Merge the update with existing metadata for the response
        updated_metadata = self.file_metadata.copy()
        updated_metadata.update(body)  # type: ignore

        request = MockDriveRequest(updated_metadata, self.update_error)
        request._body = body
        return request

    def delete(self, file_id: str) -> DriveRequest[None]:
        """
        Mock delete method for deleting a file.

        Args:
            file_id: ID of the file

        Returns:
            A mock request for the delete operation
        """
        self.delete_call_count += 1
        self.last_delete_file_id = file_id

        return cast(DriveRequest[None], MockDriveRequest(None, self.delete_error))

    def permissions(self) -> DrivePermissionsResource:
        """
        Get the permissions resource.

        Returns:
            DrivePermissionsResource: The permissions resource.
        """
        return self._permissions


class MockDriveService(DriveService):
    """Mock Drive service for testing."""

    def __init__(self, files_resource: DriveFilesResource | None = None):
        """
        Initialize mock Drive service.

        Args:
            files_resource: Mock files resource to use
        """
        self._files = files_resource or MockDriveFilesResource()
        self.files_call_count = 0

    def files(self) -> DriveFilesResource:
        """
        Get the files resource.

        Returns:
            DriveFilesResource: The files resource.
        """
        self.files_call_count += 1
        return self._files


class MockGoogleCredentials(GoogleCredentials):
    """Mock Google credentials for authentication testing."""

    def __init__(
            self,
            token: str = "test_token",
            refresh_token: str = "refresh_token",
            token_uri: str = "https://oauth2.googleapis.com/token",
            client_id: str = "client_id",
            client_secret: str = "client_secret",
            scopes: list[str] | None = None,
    ):
        """
        Initialize mock Google credentials.

        Args:
            token: The access token
            refresh_token: The refresh token
            token_uri: The token URI
            client_id: The client ID
            client_secret: The client secret
            scopes: The OAuth scopes
        """
        self.token = token
        self.refresh_token = refresh_token
        self.token_uri = token_uri
        self.client_id = client_id
        self.client_secret = client_secret
        self.scopes = scopes or ["https://www.googleapis.com/auth/drive.file"]


# Helper factory functions


def create_mock_drive_service(
        file_id: str = "file123",
        file_metadata: dict[str, Any] | None = None,
        file_list: list[dict[str, Any]] | None = None,
) -> DriveService:
    """
    Create and return a configurable mock Drive service.

    Args:
        file_id: ID to use for created files
        file_metadata: Metadata to return for file operations
        file_list: List of files to return in list operation

    Returns:
        A mock Drive service object that implements the DriveService protocol
    """
    files_resource = MockDriveFilesResource(
        file_id=file_id,
        file_metadata=file_metadata,
        file_list=file_list,
    )
    return MockDriveService(files_resource)


def create_error_drive_service(
        create_error: Exception | None = None,
        get_error: Exception | None = None,
        get_media_error: Exception | None = None,
        list_error: Exception | None = None,
        update_error: Exception | None = None,
        delete_error: Exception | None = None,
        permission_error: Exception | None = None,
) -> DriveService:
    """
    Create a Drive service mock that raises configurable exceptions.

    Args:
        create_error: Exception to raise on create operation
        get_error: Exception to raise on get operation
        get_media_error: Exception to raise on get_media operation
        list_error: Exception to raise on list operation
        update_error: Exception to raise on update operation
        delete_error: Exception to raise on delete operation
        permission_error: Exception to raise on permission operations

    Returns:
        A mock Drive service object that will raise the specified exceptions
    """
    # Use default errors if not provided
    if create_error is None:
        create_error = Exception("API Error: Failed to create file")
    if get_error is None:
        get_error = Exception("API Error: Failed to get file metadata")
    if get_media_error is None:
        get_media_error = Exception("API Error: Failed to download file")
    if list_error is None:
        list_error = Exception("API Error: Failed to list files")
    if update_error is None:
        update_error = Exception("API Error: Failed to update file")
    if delete_error is None:
        delete_error = Exception("API Error: Failed to delete file")
    if permission_error is None:
        permission_error = Exception("API Error: Failed to set permissions")

    # Create permissions resource with error
    permissions_resource = MockDrivePermissionsResource(error=permission_error)

    # Create files resource with all errors configured
    files_resource = MockDriveFilesResource(
        permissions_resource=permissions_resource,
        create_error=create_error,
        get_error=get_error,
        get_media_error=get_media_error,
        list_error=list_error,
        update_error=update_error,
        delete_error=delete_error,
    )

    return MockDriveService(files_resource)


def create_credentials() -> GoogleCredentials:
    """
    Create mock Google credentials for testing.

    Returns:
        Mock credentials that conform to the GoogleCredentials protocol
    """
    return MockGoogleCredentials()


# Additional utilities for media handling in tests

def create_mock_media_io_base_download():
    """
    Create a mock for MediaIoBaseDownload class.

    Returns:
        A factory function that produces configured download mock objects
    """

    class MockDownloader:
        """MockDownloader class with next_chunk method to simulate downloads."""

        def __init__(self, progress_sequence=None):
            """Initialize with optional progress sequence."""
            self.progress_sequence = progress_sequence or [(0.5, False), (1.0, True)]
            self.call_count = 0

        def next_chunk(self):
            """
            Get the next chunk of the download.

            Returns:
                Tuple of (status, done) where status has a progress() method
                and done is a boolean indicating if the download is complete.
            """
            if self.call_count >= len(self.progress_sequence):
                raise Exception("No more chunks available")

            progress, done = self.progress_sequence[self.call_count]
            self.call_count += 1

            # Create status object with progress method
            status = type("Status", (), {"progress": lambda: progress})()
            return status, done

    def create_downloader_factory(progress_sequence=None):
        """
        Create a mock downloader with the specified progress sequence.

        Args:
            progress_sequence: Optional sequence of (progress, done) tuples

        Returns:
            MockDownloader: A mock downloader object with next_chunk method
        """
        return MockDownloader(progress_sequence)

    return create_downloader_factory