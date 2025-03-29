# tests/test_integrations/google/drive/operations/test_operations_upload.py
"""
Tests for Google Drive operations upload module.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from quackcore.errors import QuackApiError, QuackIntegrationError
from quackcore.integrations.google.drive.operations import upload
from quackcore.integrations.core.results import IntegrationResult
from tests.test_integrations.google.drive.mocks import (
    MockDriveFilesResource,
    MockDriveService,
    create_credentials,
    create_error_drive_service,
    create_mock_drive_service,
)


class TestDriveOperationsUpload:
    """Tests for the Google Drive operations upload functions."""

    def test_initialize_drive_service(self) -> None:
        """Test initializing the Drive service."""
        # Create mock credentials using our factory
        mock_credentials = create_credentials()

        # Create the mock service we expect to be returned
        mock_drive_service = create_mock_drive_service()

        # Patch the build function where it's imported in upload.py
        with patch(
                "quackcore.integrations.google.drive.operations.upload.build") as mock_build:
            # Configure the mock to return our mock service
            mock_build.return_value = mock_drive_service

            # Test successful initialization
            result = upload.initialize_drive_service(mock_credentials)

            # Assertions
            assert result == mock_drive_service
            mock_build.assert_called_once_with(
                "drive", "v3", credentials=mock_credentials
            )

    def test_initialize_drive_service_error(self) -> None:
        """Test error handling during Drive service initialization."""
        # Create mock credentials using our factory
        mock_credentials = create_credentials()

        # Patch the build function where it's imported in upload.py
        with patch(
                "quackcore.integrations.google.drive.operations.upload.build") as mock_build:
            # Configure the mock to raise an exception
            mock_build.side_effect = Exception("API error")

            # Test error handling
            with pytest.raises(QuackApiError) as excinfo:
                upload.initialize_drive_service(mock_credentials)

            assert "Failed to initialize Google Drive API" in str(excinfo.value)
            assert excinfo.value.service == "Google Drive"
            assert excinfo.value.api_method == "build"

    def test_resolve_file_details(self, tmp_path: Path) -> None:
        """Test resolving file details for upload."""
        # Create a test file
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("test content")

        # Mock resolver
        with patch("quackcore.paths.resolver.resolve_project_path") as mock_resolve:
            mock_resolve.return_value = test_file

            # Mock file info
            with patch("quackcore.fs.service.get_file_info") as mock_info:
                mock_info.return_value.success = True
                mock_info.return_value.exists = True

                # Mock split_path
                with patch("quackcore.fs.service.split_path") as mock_split:
                    mock_split.return_value = ["test_file.txt"]

                    # Mock get_mime_type
                    with patch("quackcore.fs.service.get_mime_type") as mock_mime:
                        mock_mime.return_value = "text/plain"

                        # Test with default parameters
                        path_obj, filename, folder_id, mime_type = (
                            upload.resolve_file_details(str(test_file), None, None)
                        )

                        assert path_obj == test_file
                        assert filename == "test_file.txt"
                        assert folder_id is None
                        assert mime_type == "text/plain"

                        # Test with custom parameters
                        path_obj, filename, folder_id, mime_type = (
                            upload.resolve_file_details(
                                str(test_file), "remote_name.txt", "folder123"
                            )
                        )

                        assert path_obj == test_file
                        assert filename == "remote_name.txt"
                        assert folder_id == "folder123"
                        assert mime_type == "text/plain"

    def test_resolve_file_details_not_found(self, tmp_path: Path) -> None:
        """Test error handling when file is not found."""
        # Create a non-existent file path
        test_file = tmp_path / "nonexistent.txt"

        # Mock resolver
        with patch("quackcore.paths.resolver.resolve_project_path") as mock_resolve:
            mock_resolve.return_value = test_file

            # Mock file info to show file doesn't exist
            with patch("quackcore.fs.service.get_file_info") as mock_info:
                mock_info.return_value.success = True
                mock_info.return_value.exists = False

                # Test error handling
                with pytest.raises(QuackIntegrationError) as excinfo:
                    upload.resolve_file_details(str(test_file), None, None)

                assert "File not found" in str(excinfo.value)

    def test_upload_file(self, tmp_path: Path) -> None:
        """Test uploading a file to Google Drive."""
        # Create a test file
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("test content")

        # Create mock drive service using our factory
        mock_drive_service = create_mock_drive_service(
            file_id="file123",
            file_metadata={
                "id": "file123",
                "name": "test_file.txt",
                "mimeType": "text/plain",
                "webViewLink": "https://drive.google.com/file/d/file123/view",
            },
        )

        # Mock resolve_file_details
        with patch.object(upload, "resolve_file_details") as mock_resolve:
            mock_resolve.return_value = (
                test_file,
                "test_file.txt",
                "folder123",
                "text/plain",
            )

            # Use the correct import path for fs module in upload.py
            with patch(
                    "quackcore.integrations.google.drive.operations.upload.fs") as mock_fs:
                # Configure the mock fs module's read_binary method
                mock_fs.read_binary.return_value.success = True
                mock_fs.read_binary.return_value.content = b"test content"

                # Create a proper mock class for MediaInMemoryUpload instead of just returning a MagicMock
                class MockMediaInMemoryUpload:
                    def __init__(self, content, mimetype=None, resumable=False):
                        self.content = content
                        self.mimetype = mimetype
                        self.resumable = resumable

                # Patch the MediaInMemoryUpload class with our mock implementation
                with patch("googleapiclient.http.MediaInMemoryUpload",
                           MockMediaInMemoryUpload):
                    # Mock execute_api_request
                    with patch(
                            "quackcore.integrations.google.drive.utils.api.execute_api_request"
                    ) as mock_execute:
                        mock_execute.return_value = {
                            "id": "file123",
                            "webViewLink": "https://drive.google.com/file/d/file123/view",
                        }

                        # Mock set_file_permissions
                        with patch(
                                "quackcore.integrations.google.drive.operations.permissions.set_file_permissions"
                        ) as mock_permissions:
                            mock_permissions.return_value = IntegrationResult(
                                success=True
                            )

                            # Test successful upload
                            result = upload.upload_file(
                                mock_drive_service,
                                str(test_file),
                                description="Test file",
                                parent_folder_id="folder123",
                                make_public=True,
                            )

                            assert result.success is True
                            assert (
                                    result.content
                                    == "https://drive.google.com/file/d/file123/view"
                            )

                            # Check that execute_api_request was called correctly
                            mock_execute.assert_called_once()

                            # Check that set_file_permissions was called
                            mock_permissions.assert_called_once_with(
                                mock_drive_service, "file123", "reader", "anyone", None
                            )

                            # Verify our mock service was used correctly
                            mock_service = mock_drive_service
                            assert isinstance(mock_service, MockDriveService)
                            assert mock_service.files_call_count == 1

                            # Check file resource calls
                            files_resource = mock_service.files()
                            assert isinstance(files_resource, MockDriveFilesResource)
                            assert files_resource.create_call_count == 1

    def test_upload_file_read_error(self, tmp_path: Path) -> None:
        """Test error handling when reading file fails."""
        # Create a test file
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("test content")

        # Create mock drive service
        mock_drive_service = create_mock_drive_service()

        # Mock resolve_file_details
        with patch.object(upload, "resolve_file_details") as mock_resolve:
            mock_resolve.return_value = (
                test_file,
                "test_file.txt",
                "folder123",
                "text/plain",
            )

            # Mock read_binary to fail using the correct import path
            with patch(
                    "quackcore.integrations.google.drive.operations.upload.fs") as mock_fs:
                mock_fs.read_binary.return_value.success = False
                mock_fs.read_binary.return_value.error = "Read error"

                # Test error handling
                result = upload.upload_file(mock_drive_service, str(test_file))

                assert result.success is False
                assert "Failed to read file: Read error" in result.error

    def test_upload_file_api_error(self, tmp_path: Path) -> None:
        """Test error handling when API call fails."""
        # Create a test file
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("test content")

        # Create error-raising mock drive service
        mock_drive_service = create_error_drive_service(
            create_error=QuackApiError(
                "API error", service="Google Drive", api_method="files.create"
            )
        )

        # Mock resolve_file_details
        with patch.object(upload, "resolve_file_details") as mock_resolve:
            mock_resolve.return_value = (
                test_file,
                "test_file.txt",
                "folder123",
                "text/plain",
            )

            # Mock read_binary
            with patch(
                    "quackcore.integrations.google.drive.operations.upload.fs") as mock_fs:
                mock_fs.read_binary.return_value.success = True
                mock_fs.read_binary.return_value.content = b"test content"

                # Create a proper mock class for MediaInMemoryUpload
                class MockMediaInMemoryUpload:
                    def __init__(self, content, mimetype=None, resumable=False):
                        self.content = content
                        self.mimetype = mimetype
                        self.resumable = resumable

                # Patch MediaInMemoryUpload with our custom implementation
                with patch("googleapiclient.http.MediaInMemoryUpload",
                           MockMediaInMemoryUpload):
                    # Mock execute_api_request to raise an error
                    with patch(
                            "quackcore.integrations.google.drive.utils.api.execute_api_request"
                    ) as mock_execute:
                        mock_execute.side_effect = QuackApiError(
                            "API error",
                            service="Google Drive",
                            api_method="files.create",
                        )

                        # Test error handling
                        result = upload.upload_file(mock_drive_service, str(test_file))

                        assert result.success is False
                        assert "API error" in result.error

    def test_upload_file_with_specific_metadata(self, tmp_path: Path) -> None:
        """Test uploading a file with specific metadata configuration."""
        # Create a test file
        test_file = tmp_path / "document.pdf"
        test_file.write_text("PDF content")

        # Create a custom mock service with specific file metadata
        mock_drive_service = create_mock_drive_service(
            file_id="doc123",
            file_metadata={
                "id": "doc123",
                "name": "document.pdf",
                "mimeType": "application/pdf",
                "webViewLink": "https://drive.google.com/file/d/doc123/view",
                "description": "Important document",
            },
        )

        # Mock resolve_file_details
        with patch.object(upload, "resolve_file_details") as mock_resolve:
            mock_resolve.return_value = (
                test_file,
                "document.pdf",
                "folder456",
                "application/pdf",
            )

            # Mock read_binary
            with patch(
                    "quackcore.integrations.google.drive.operations.upload.fs") as mock_fs:
                mock_fs.read_binary.return_value.success = True
                mock_fs.read_binary.return_value.content = b"PDF content"

                # Create a proper mock class for MediaInMemoryUpload
                class MockMediaInMemoryUpload:
                    def __init__(self, content, mimetype=None, resumable=False):
                        self.content = content
                        self.mimetype = mimetype
                        self.resumable = resumable

                # Patch MediaInMemoryUpload with our custom implementation
                with patch("googleapiclient.http.MediaInMemoryUpload",
                           MockMediaInMemoryUpload):
                    # Mock execute_api_request
                    with patch(
                            "quackcore.integrations.google.drive.utils.api.execute_api_request"
                    ) as mock_execute:
                        mock_execute.return_value = {
                            "id": "doc123",
                            "name": "document.pdf",
                            "mimeType": "application/pdf",
                            "webViewLink": "https://drive.google.com/file/d/doc123/view",
                            "description": "Important document",
                        }

                        # Mock permissions but disable public sharing
                        with patch(
                                "quackcore.integrations.google.drive.operations.permissions.set_file_permissions"
                        ):
                            # Test upload with specific metadata
                            result = upload.upload_file(
                                mock_drive_service,
                                str(test_file),
                                description="Important document",
                                parent_folder_id="folder456",
                                make_public=False,  # Don't make it public
                            )

                            assert result.success is True
                            assert (
                                    result.content
                                    == "https://drive.google.com/file/d/doc123/view"
                            )

                            # Verify the file metadata was constructed correctly
                            mock_service = mock_drive_service
                            assert isinstance(mock_service, MockDriveService)
                            files_resource = mock_service.files()
                            assert isinstance(files_resource, MockDriveFilesResource)

                            # Check the body passed to create
                            assert files_resource.create_call_count == 1
                            assert (
                                    files_resource.last_create_body["name"]
                                    == "document.pdf"
                            )
                            assert (
                                    files_resource.last_create_body["mimeType"]
                                    == "application/pdf"
                            )
                            assert (
                                    files_resource.last_create_body["description"]
                                    == "Important document"
                            )
                            assert files_resource.last_create_body["parents"] == [
                                "folder456"
                            ]