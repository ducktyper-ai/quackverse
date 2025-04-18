# quackcore/tests/test_integrations/google/drive/operations/test_operations_download.py
"""
Tests for Google Drive _operations download module.
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
)


class TestDriveOperationsDownload:
    """Tests for the Google Drive _operations download functions."""

    def test_download_file_simple(self) -> None:
        """Test downloading a file from Google Drive - simplified approach."""
        # Create mock drive service
        mock_drive_service = create_mock_drive_service()

        # Setup mocks for dependencies
        with (
            patch("googleapiclient.http.MediaIoBaseDownload") as mock_download_class,
            patch("io.BytesIO") as mock_bytesio,
            # Patch the fs module directly as it's imported as an alias
            patch(
                "quackcore.integrations.google.drive._operations.download.fs"
            ) as mock_fs,
            patch(
                "quackcore.integrations.google.drive.api.api.execute_api_request"
            ) as mock_execute,
        ):
            # Configure fs module mocks
            mock_resolve = MagicMock(return_value="/tmp/test_file.txt")
            mock_fs.join_path.return_value = Path("/tmp/test_file.txt")
            mock_fs.create_temp_directory.return_value = "/tmp"

            mock_fs.create_directory.return_value = OperationResult(
                success=True, path="/tmp", message="Directory created"
            )
            mock_execute.return_value = {
                "name": "test_file.txt",
                "mimeType": "text/plain",
            }

            # Configure downloader mock
            mock_downloader = MagicMock()
            mock_status = MagicMock()
            mock_status.progress.return_value = 1.0
            mock_downloader.next_chunk.return_value = (mock_status, True)
            mock_download_class.return_value = mock_downloader

            # Configure BytesIO mock
            mock_io = MagicMock()
            mock_bytesio.return_value = mock_io
            mock_io.read.return_value = b"file content"

            # Configure write_binary mock
            mock_fs.write_binary.return_value = WriteResult(
                success=True,
                path="/tmp/test_file.txt",
                bytes_written=12,
                message="File written",
            )

            # Mock paths resolver
            with patch(
                "quackcore.integrations.google.drive._operations.download.resolver"
            ) as mock_resolver:
                mock_resolver.resolve_project_path.return_value = "/tmp/test_file.txt"

                # Call download function
                result = download.download_file(
                    mock_drive_service, "file123", "/tmp/test_file.txt"
                )

                # Assertions
                assert result.success is True
                assert "File downloaded successfully" in result.message

    def test_resolve_download_path(self, tmp_path: Path) -> None:
        """Test resolving download path for different scenarios."""
        # Test with no local path (should create temp directory)
        file_metadata = {"name": "test_file.txt"}

        # Patch the fs module directly as it's imported as an alias
        with patch(
            "quackcore.integrations.google.drive._operations.download.fs"
        ) as mock_fs:
            # Setup the mock to return what the test expects
            mock_fs.create_temp_directory.return_value = tmp_path / "temp_dir"
            mock_fs.join_path.return_value = tmp_path / "temp_dir" / "test_file.txt"

            # Call the function
            result = download.resolve_download_path(file_metadata, None)

            # Verify the result matches our expected path
            assert mock_fs.create_temp_directory.called, (
                "create_temp_directory should be called"
            )
            assert mock_fs.join_path.called, "join_path should be called"
            assert str(result) == str(tmp_path / "temp_dir" / "test_file.txt")

        # Test with local path to directory
        local_dir = tmp_path / "local_dir"

        with patch("quackcore.paths.resolver.resolve_project_path") as mock_resolve:
            mock_resolve.return_value = local_dir

            with patch(
                "quackcore.integrations.google.drive._operations.download.fs"
            ) as mock_fs:
                # Setup mock to return a directory
                mock_fs.get_file_info.return_value = FileInfoResult(
                    success=True, path=str(local_dir), exists=True, is_dir=True
                )

                # Setup mock_join to return expected path
                mock_fs.join_path.return_value = local_dir / "test_file.txt"

                # Test function with a directory path
                result = download.resolve_download_path(file_metadata, str(local_dir))

                assert str(result) == str(local_dir / "test_file.txt")
                assert mock_fs.join_path.called, (
                    "join_path should be called for directory paths"
                )

        # Test with local path as specific file
        local_file = tmp_path / "specific_file.txt"

        with patch("quackcore.paths.resolver.resolve_project_path") as mock_resolve:
            mock_resolve.return_value = local_file

            with patch(
                "quackcore.integrations.google.drive._operations.download.fs"
            ) as mock_fs:
                # Setup mock to return a file
                mock_fs.get_file_info.return_value = FileInfoResult(
                    success=True,
                    path=str(local_file),
                    exists=True,
                    is_file=True,
                    is_dir=False,
                )

                # Test function with a file path
                result = download.resolve_download_path(file_metadata, str(local_file))

                assert str(result) == str(local_file)

    def test_download_file_api_error(self) -> None:
        """Test download file with API error."""
        # Create mock drive service that raises errors
        mock_drive_service = create_error_drive_service()

        # Mock logger to avoid actual logging during tests
        mock_logger = MagicMock(spec=logging.Logger)

        # Mock execute_api_request to raise QuackApiError
        with patch(
            "quackcore.integrations.google.drive.api.api.execute_api_request"
        ) as mock_execute:
            mock_execute.side_effect = QuackApiError(
                "Failed to get file metadata",
                service="Google Drive",
                api_method="files.get",
            )

            # Test API error handling with logger
            result = download.download_file(
                mock_drive_service, "file123", logger=mock_logger
            )

            # Verify the result is as expected
            assert not result.success
            assert "Failed to get file metadata" in result.error

    def test_download_file_write_error(self) -> None:
        """Test download file with write error."""
        # Create mock drive service
        mock_drive_service = create_mock_drive_service()

        # Setup with patch pyramid
        with (
            patch("googleapiclient.http.MediaIoBaseDownload") as mock_download,
            patch("io.BytesIO") as mock_bytesio,
            patch(
                "quackcore.integrations.google.drive._operations.download.fs"
            ) as mock_fs,
            patch("quackcore.paths.resolver.resolve_project_path") as mock_resolve,
            patch(
                "quackcore.integrations.google.drive.api.api.execute_api_request"
            ) as mock_execute,
        ):
            # Configure mocks
            mock_resolve.return_value = "/tmp/test_file.txt"
            mock_fs.join_path.return_value = Path("/tmp/test_file.txt")
            mock_fs.create_directory.return_value = OperationResult(
                success=True, path="/tmp", message="Directory created"
            )
            mock_execute.return_value = {
                "name": "test_file.txt",
                "mimeType": "text/plain",
            }

            # Configure write_binary to fail
            mock_fs.write_binary.return_value = WriteResult(
                success=False,
                path="/tmp/test_file.txt",
                error="Write error",
                bytes_written=0,
            )

            # Configure downloader
            mock_downloader = MagicMock()
            mock_status = MagicMock()
            mock_status.progress.return_value = 1.0
            mock_downloader.next_chunk.return_value = (mock_status, True)
            mock_download.return_value = mock_downloader

            # Configure BytesIO
            mock_io = MagicMock()
            mock_bytesio.return_value = mock_io
            mock_io.read.return_value = b"file content"

            # Test write error handling
            result = download.download_file(
                mock_drive_service,
                "file123",
                "/tmp/test_file.txt",
            )

            # Verify the result is as expected
            assert not result.success
            assert "Write error" in result.error
