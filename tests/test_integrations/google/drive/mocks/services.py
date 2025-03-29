# tests/test_integrations/google/drive/mocks/services.py
"""
Mock service objects for Google Drive testing.
"""

from typing import Any

from quackcore.integrations.google.drive.protocols import (
    DriveFilesResource,
    DriveService,
)
from tests.test_integrations.google.drive.mocks.resources import (
    MockDriveFilesResource,
    MockDrivePermissionsResource,
)


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
