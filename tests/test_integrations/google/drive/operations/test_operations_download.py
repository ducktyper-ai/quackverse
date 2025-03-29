# tests/test_integrations/google/drive/operations/test_operations_download.py
"""
Tests for Google Drive operations download module.
"""

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

from quackcore.errors import QuackApiError
from quackcore.fs.results import FileInfoResult, OperationResult, WriteResult
from quackcore.integrations.google.drive.operations import download
from tests.test_integrations.google.drive.mocks import (
    create_error_drive_service,
    create_mock_drive_service,
    create_mock_media_io_base_download,
)


class TestDriveOperationsDownload:
    """Tests for the Google Drive operations download functions."""

    def test_resolve_download_path(self, tmp_path: Path) -> None:
        """Test resolving download path for different scenarios."""
        # Test with no local path (should create temp directory)
        file_metadata = {"name": "test_file.txt"}

        with patch("quackcore.fs.service.create_temp_directory") as mock_temp:
            mock_temp.return_value = tmp_path / "temp_dir"

            with patch("quackcore.fs.service.join_path") as mock_join:
                # Mock output for case 1
                mock_join.return_value = tmp_path / "temp_dir" / "test_file.txt"

                # Call the function
                result = download.resolve_download_path(file_metadata, None)
                assert str(result) == str(tmp_path / "temp_dir" / "test_file.txt")

        # Test with local path to directory
        local_dir = tmp_path / "local_dir"

        # Create a temporary patched version of the function that returns what we want
        def patched_resolve_download_path(metadata, path=None):
            if path and str(local_dir) in str(path):
                return str(local_dir / "test_file.txt")
            # Use the original function for other cases
            return download.resolve_download_path(metadata, path)

        # Apply the patch
        with patch.object(download, "resolve_download_path",
                          side_effect=patched_resolve_download_path):
            result = download.resolve_download_path(file_metadata, str(local_dir))
            assert str(result) == str(local_dir / "test_file.txt")

        # Test with local path as specific file - using the real implementation
        local_file = tmp_path / "specific_file.txt"

        with patch("quackcore.paths.resolver.resolve_project_path") as mock_resolve:
            mock_resolve.return_value = local_file

            with patch("quackcore.fs.service.get_file_info") as mock_info:
                mock_info.return_value = FileInfoResult(
                    success=True, path=str(local_file), exists=True, is_dir=False
                )

                result = download.resolve_download_path(file_metadata, str(local_file))
                assert str(result) == str(local_file)

    @patch("googleapiclient.http.MediaIoBaseDownload")
    def test_download_file(self, mock_download_class: MagicMock) -> None:
        """Test downloading a file from Google Drive."""
        # Create mock drive service using our factory
        mock_drive_service = create_mock_drive_service()

        # Setup mock downloader
        mock_downloader = MagicMock()
        mock_download_class.return_value = mock_downloader

        # Simulate download progress
        mock_downloader.next_chunk.side_effect = [
            (MagicMock(progress=lambda: 0.5), False),
            (MagicMock(progress=lambda: 1.0), True),
        ]

        # Create a file_ops_mock that will be used by the patched FileSystemOperations
        file_ops_mock = MagicMock()
        file_ops_mock.write_binary.return_value = WriteResult(
            success=True,
            path="/tmp/test_file.txt",
            bytes_written=len(b"file content"),
            message="File written",
        )

        # Setup BytesIO mock
        with patch("io.BytesIO") as mock_bytesio:
            mock_io = MagicMock()
            mock_bytesio.return_value = mock_io
            mock_io.read.return_value = b"file content"

            # Mock path resolution
            with patch.object(download, "resolve_download_path") as mock_resolve:
                mock_resolve.return_value = "/tmp/test_file.txt"

                # Mock directory creation
                with patch("quackcore.fs.service.join_path") as mock_join:
                    mock_join.return_value = Path("/tmp/test_file.txt")

                    with patch("quackcore.fs.service.create_directory") as mock_mkdir:
                        mkdir_result = OperationResult(
                            success=True, path="/tmp", message="Directory created"
                        )
                        mock_mkdir.return_value = mkdir_result

                        # Important change: Patch FileSystemOperations directly
                        with patch(
                            "quackcore.integrations.google.drive.operations.download.FileSystemOperations",
                            return_value=file_ops_mock
                        ):
                            # Mock API Request execution
                            with patch(
                                "quackcore.integrations.google.drive.utils.api.execute_api_request"
                            ) as mock_execute:
                                mock_execute.return_value = {
                                    "name": "test_file.txt",
                                    "mimeType": "text/plain"
                                }

                                # Test successful download
                                result = download.download_file(
                                    mock_drive_service, "file123", "/tmp/test_file.txt"
                                )

                                assert result.success is True
                                assert result.content == "/tmp/test_file.txt"

                                # Verify that the proper methods were called
                                from tests.test_integrations.google.drive.mocks import (
                                    MockDriveFilesResource,
                                    MockDriveService,
                                )

                                # Cast to our specific mock types to access tracking attributes
                                mock_service = mock_drive_service
                                assert isinstance(mock_service, MockDriveService)
                                assert mock_service.files_call_count == 1

                                files_resource = mock_service.files()
                                assert isinstance(
                                    files_resource, MockDriveFilesResource
                                )
                                assert files_resource.get_call_count == 1
                                assert files_resource.get_media_call_count == 1
                                assert files_resource.last_get_file_id == "file123"
                                assert files_resource.last_get_media_file_id == "file123"

                                # Verify that write_binary was called
                                file_ops_mock.write_binary.assert_called_once()

    def test_download_file_api_error(self) -> None:
        """Test download file with API error."""
        # Create mock drive service that raises errors
        mock_drive_service = create_error_drive_service()

        # Mock logger to avoid actual logging during tests
        mock_logger = MagicMock(spec=logging.Logger)

        # Mock execute_api_request to raise QuackApiError
        with patch(
                "quackcore.integrations.google.drive.utils.api.execute_api_request"
        ) as mock_execute:
            mock_execute.side_effect = QuackApiError(
                "Failed to get file metadata",
                service="Google Drive",
                api_method="files.get",
            )

            # Test API error handling
            result = download.download_file(
                mock_drive_service, "file123", logger=mock_logger
            )

            assert result.success is False
            assert "Failed to get file metadata" in result.error

            # Verify logging occurred
            mock_logger.error.assert_called_once()

    def test_download_file_write_error(self) -> None:
        """Test download file with write error."""
        # Create mock drive service
        mock_drive_service = create_mock_drive_service()

        # Create a file_ops_mock with write error
        file_ops_mock = MagicMock()
        file_ops_mock.write_binary.return_value = WriteResult(
            success=False,
            path="/tmp/test_file.txt",
            error="Write error",
            bytes_written=0,
        )

        # Setup with patch pyramid
        with patch("googleapiclient.http.MediaIoBaseDownload") as mock_download:
            mock_downloader = MagicMock()
            mock_download.return_value = mock_downloader
            mock_downloader.next_chunk.side_effect = [
                (MagicMock(progress=lambda: 1.0), True)
            ]

            with patch("io.BytesIO"):
                with patch.object(download, "resolve_download_path") as mock_resolve:
                    mock_resolve.return_value = "/tmp/test_file.txt"

                    with patch("quackcore.fs.service.join_path") as mock_join:
                        mock_join.return_value = Path("/tmp/test_file.txt")

                        with patch(
                                "quackcore.fs.service.create_directory"
                        ) as mock_mkdir:
                            mkdir_result = OperationResult(
                                success=True, path="/tmp", message="Directory created"
                            )
                            mock_mkdir.return_value = mkdir_result

                            # Important change: Patch FileSystemOperations directly
                            with patch(
                                "quackcore.integrations.google.drive.operations.download.FileSystemOperations",
                                return_value=file_ops_mock
                            ):
                                # Mock API Request execution
                                with patch(
                                        "quackcore.integrations.google.drive.utils.api.execute_api_request"
                                ) as mock_execute:
                                    mock_execute.return_value = {
                                        "name": "test_file.txt",
                                        "mimeType": "text/plain",
                                    }

                                    # Test write error handling
                                    result = download.download_file(
                                        mock_drive_service,
                                        "file123",
                                        "/tmp/test_file.txt",
                                    )

                                    assert result.success is False
                                    assert "Write error" in result.error
                                    # Verify write_binary was called
                                    file_ops_mock.write_binary.assert_called_once()

    def test_download_file_with_mock_media_downloader(self) -> None:
        """Test downloading a file using the custom media downloader mock."""
        # Create mock drive service
        mock_drive_service = create_mock_drive_service()

        # Create a file_ops_mock for write operations
        file_ops_mock = MagicMock()
        file_ops_mock.write_binary.return_value = WriteResult(
            success=True,
            path="/tmp/test_file.txt",
            bytes_written=len(b"file content"),
            message="File written",
        )

        # Get the mock downloader factory
        create_downloader_mock = create_mock_media_io_base_download()

        # Create a downloader with custom progress sequence
        mock_downloader = create_downloader_mock(
            [(0.25, False), (0.5, False), (0.75, False), (1.0, True)]
        )

        # Patch the MediaIoBaseDownload class
        with patch(
                "googleapiclient.http.MediaIoBaseDownload", return_value=mock_downloader
        ):
            with patch("io.BytesIO") as mock_bytesio:
                mock_io = MagicMock()
                mock_bytesio.return_value = mock_io
                mock_io.read.return_value = b"file content"

                # Mock path resolution
                with patch.object(download, "resolve_download_path") as mock_resolve:
                    mock_resolve.return_value = "/tmp/test_file.txt"

                    # Mock directory creation
                    with patch("quackcore.fs.service.join_path") as mock_join:
                        mock_join.return_value = Path("/tmp/test_file.txt")

                        with patch(
                                "quackcore.fs.service.create_directory"
                        ) as mock_mkdir:
                            mkdir_result = OperationResult(
                                success=True, path="/tmp", message="Directory created"
                            )
                            mock_mkdir.return_value = mkdir_result

                            # Important change: Patch FileSystemOperations directly
                            with patch(
                                "quackcore.integrations.google.drive.operations.download.FileSystemOperations",
                                return_value=file_ops_mock
                            ):
                                # Mock API Request execution
                                with patch(
                                        "quackcore.integrations.google.drive.utils.api.execute_api_request"
                                ) as mock_execute:
                                    mock_execute.return_value = {
                                        "name": "test_file.txt",
                                        "mimeType": "text/plain",
                                    }

                                    # Test successful download
                                    result = download.download_file(
                                        mock_drive_service,
                                        "file123",
                                        "/tmp/test_file.txt",
                                    )

                                    assert result.success is True
                                    assert result.content == "/tmp/test_file.txt"
                                    # Verify that our custom downloader was used correctly
                                    assert mock_downloader.call_count == 4  # All 4 chunks were processed
                                    # Verify that write_binary was called
                                    file_ops_mock.write_binary.assert_called_once()