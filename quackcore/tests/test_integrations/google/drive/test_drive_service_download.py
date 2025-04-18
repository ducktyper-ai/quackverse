# quackcore/tests/test_integrations/google/drive/test_drive_service_download.py
"""
Tests for Google Drive service download _operations.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from quackcore.errors import QuackApiError
from quackcore.fs import DataResult
from quackcore.fs.results import FileInfoResult, OperationResult, WriteResult
from quackcore.integrations.google.drive.service import GoogleDriveService
from quackcore.paths.api.public.results import PathResult


class TestGoogleDriveServiceDownload:
    """Tests for GoogleDriveService download _operations."""

    @pytest.fixture
    def drive_service(self) -> GoogleDriveService:
        """Set up a Google Drive service with mocked dependencies."""
        with patch(
                "quackcore.integrations.google.drive.service.paths"
        ) as mock_paths:
            # Setup paths service mock to return predictable PathResult objects
            mock_paths.resolve_project_path.return_value = PathResult(
                success=True,
                path=str(Path("/fake/test/dir/mock_path"))  # Convert Path to string
            )

            with patch("quackcore.fs.service.get_file_info") as mock_file_info:
                # All file info checks should return that files exist
                file_info_result = FileInfoResult(
                    success=True,
                    path="/fake/test/dir/mock_credentials.json",
                    exists=True,
                    is_file=True,
                    message="File exists",
                )
                mock_file_info.return_value = file_info_result

                # Create the service with a mocked configuration
                with patch.object(
                        GoogleDriveService, "_initialize_config"
                ) as mock_init_config:
                    mock_init_config.return_value = {
                        "client_secrets_file": "/fake/test/dir/mock_secrets.json",
                        "credentials_file": "/fake/test/dir/mock_credentials.json",
                    }

                    # Patch fs module
                    with patch(
                            "quackcore.integrations.google.drive.service.fs") as mock_fs:
                        # Configure join_path to return a DataResult
                        mock_fs.join_path.return_value = DataResult(
                            success=True,
                            path=Path("/fake/test/dir/joined_path"),
                            data="/fake/test/dir/joined_path",
                            format="path",
                            message="Successfully joined path parts"
                        )

                        # Disable verification of the client secrets file
                        with patch(
                                "quackcore.integrations.google.auth.GoogleAuthProvider._verify_client_secrets_file"
                        ):
                            service = GoogleDriveService()
                            # Mark as initialized to skip the actual initialization logic
                            service._initialized = True
                            service.drive_service = MagicMock()
                            yield service

    @patch("googleapiclient.http.MediaIoBaseDownload")
    def test_download_file(
            self, mock_download_class: MagicMock, drive_service: GoogleDriveService
    ) -> None:
        """Test downloading a file."""
        # --- Setup for successful metadata retrieval ---
        mock_get = MagicMock()
        drive_service.drive_service.files().get.return_value = mock_get
        mock_get.execute.return_value = {
            "name": "test_file.txt",
            "mimeType": "text/plain",
        }
        # Setup get_media call to return a valid request
        mock_get_media = MagicMock()
        drive_service.drive_service.files().get_media.return_value = mock_get_media

        # --- Test successful download ---
        # Configure the downloader to simulate a successful download
        mock_downloader = MagicMock()
        mock_download_class.return_value = mock_downloader
        mock_downloader.next_chunk.side_effect = [
            (MagicMock(progress=lambda: 0.5), False),
            (MagicMock(progress=lambda: 1.0), True),
        ]

        with patch(
                "quackcore.integrations.google.drive.service.io.BytesIO"
        ) as mock_bytesio:
            mock_io = MagicMock()
            mock_bytesio.return_value = mock_io
            mock_io.read.return_value = b"file content"

            with patch.object(drive_service, "_resolve_download_path") as mock_resolve:
                mock_resolve.return_value = "/tmp/test_file.txt"

                with patch("quackcore.integrations.google.drive.service.fs") as mock_fs:
                    # Setup join_path to return a DataResult
                    mock_fs.join_path.return_value = DataResult(
                        success=True,
                        path=Path("/tmp/test_file.txt"),
                        data="/tmp/test_file.txt",
                        format="path",
                        message="Successfully joined path parts"
                    )

                    # Mock create_directory to return success
                    mock_fs.create_directory.return_value = OperationResult(
                        success=True, path="/tmp", message="Directory created"
                    )

                    # Mock write_binary to return success
                    mock_fs.write_binary.return_value = WriteResult(
                        success=True,
                        path="/tmp/test_file.txt",
                        bytes_written=len(b"file content"),
                        message="File written",
                    )

                    result = drive_service.download_file(
                        "file123", "/tmp/test_file.txt"
                    )
                    assert result.success is True
                    assert result.content == "/tmp/test_file.txt"
                    drive_service.drive_service.files().get.assert_called_once_with(
                        fileId="file123", fields="name, mimeType"
                    )
                    drive_service.drive_service.files().get_media.assert_called_once_with(
                        fileId="file123"
                    )
                    mock_fs.write_binary.assert_called_once()

        # --- Test API error during metadata retrieval ---
        drive_service.drive_service.files().get.side_effect = QuackApiError(
            "API error", service="drive"
        )
        result = drive_service.download_file("file123")
        assert result.success is False
        assert "API error" in result.error

        # --- Test download error ---
        drive_service.drive_service.files().get.side_effect = None
        mock_download_class.side_effect = Exception("Download error")
        result = drive_service.download_file("file123")
        assert result.success is False
        assert "Download error" in result.error

        # --- Test write error ---
        # Reset the MediaIoBaseDownload mock to simulate a successful download loop
        mock_download_class.side_effect = None
        new_downloader = MagicMock()
        mock_download_class.return_value = new_downloader
        new_downloader.next_chunk.side_effect = [
            (MagicMock(progress=lambda: 0.5), False),
            (MagicMock(progress=lambda: 1.0), True),
        ]

        with patch.object(drive_service, "_resolve_download_path") as mock_resolve:
            mock_resolve.return_value = "/tmp/test_file.txt"

            with patch("quackcore.integrations.google.drive.service.fs") as mock_fs:
                # Setup join_path to return a DataResult
                mock_fs.join_path.return_value = DataResult(
                    success=True,
                    path=Path("/tmp/test_file.txt"),
                    data="/tmp/test_file.txt",
                    format="path",
                    message="Successfully joined path parts"
                )

                # Mock create_directory to return success
                mock_fs.create_directory.return_value = OperationResult(
                    success=True, path="/tmp", message="Directory created"
                )

                # Simulate a write error
                mock_fs.write_binary.return_value = WriteResult(
                    success=False,
                    path="/tmp/test_file.txt",
                    error="Write error",
                )

                result = drive_service.download_file("file123")
                assert result.success is False
                assert "Write error" in result.error
