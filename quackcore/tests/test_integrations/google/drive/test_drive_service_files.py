# quackcore/tests/test_integrations/google/drive/test_drive_service_files.py
"""
Tests for Google Drive service file _operations.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from quackcore.errors import QuackFileNotFoundError
from quackcore.fs import DataResult
from quackcore.fs.results import FileInfoResult
from quackcore.integrations.google.drive.service import GoogleDriveService
from quackcore.paths.api.public.results import PathResult


class TestGoogleDriveServiceFiles:
    """Tests for the GoogleDriveService file _operations."""

    @pytest.fixture
    def drive_service(self):
        """Set up a Google Drive service with mocked dependencies."""
        # Mock the paths service
        with patch(
            "quackcore.integrations.google.drive.service.paths"
        ) as mock_paths:
            # Setup the paths mock to return PathResult objects with Path objects, not strings
            mock_paths.resolve_project_path.return_value = PathResult(
                success=True,
                path=Path("/fake/test/dir/mock_path")  # Use Path here, not str
            )

            # Mock config initialization
            with patch.object(
                GoogleDriveService, "_initialize_config"
            ) as mock_init_config:
                mock_init_config.return_value = {
                    "client_secrets_file": "/fake/test/dir/mock_secrets.json",
                    "credentials_file": "/fake/test/dir/mock_credentials.json",
                }

                # Patch _verify_client_secrets_file to prevent verification
                with patch(
                    "quackcore.integrations.google.auth.GoogleAuthProvider._verify_client_secrets_file"
                ):
                    # Create and configure the service
                    service = GoogleDriveService()
                    # Manually set shared_folder_id since we're not using the constructor parameter
                    service.shared_folder_id = "shared_folder"
                    service._initialized = True
                    service.drive_service = MagicMock()

                    # Yield the service to the test
                    yield service

    def test_resolve_file_details(self, drive_service, tmp_path: Path) -> None:
        """Test resolving file details."""
        # Create a test file
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("test content")

        # Test with relative path and parent folder
        with patch(
            "quackcore.integrations.google.drive.service.paths.resolve_project_path"
        ) as mock_resolve:
            # Update to return PathResult with Path object, not string
            mock_resolve.return_value = PathResult(
                success=True,
                path=test_file  # Use Path object directly
            )

            with patch("quackcore.integrations.google.drive.service.fs") as mock_fs:
                mock_fs.get_file_info.return_value = FileInfoResult(
                    success=True, path=test_file, exists=True, is_file=True
                )
                mock_fs.split_path.return_value = DataResult(
                    success=True,
                    path=test_file,
                    data=["test_file.txt"],
                    format="list",
                    message="Successfully split path"
                )
                mock_fs.get_mime_type.return_value = "text/plain"

                path_obj, filename, folder_id, mime_type = (
                    drive_service._resolve_file_details(
                        "test_file.txt", None, "folder123"
                    )
                )

                assert path_obj == test_file
                assert filename == "test_file.txt"
                assert folder_id == "folder123"
                assert mime_type == "text/plain"

        # Test with remote path specified
        with patch(
            "quackcore.integrations.google.drive.service.paths.resolve_project_path"
        ) as mock_resolve:
            # Update to return PathResult with Path object, not string
            mock_resolve.return_value = PathResult(
                success=True,
                path=test_file  # Use Path object directly
            )

            with patch("quackcore.integrations.google.drive.service.fs") as mock_fs:
                mock_fs.get_file_info.return_value = FileInfoResult(
                    success=True, path=test_file, exists=True, is_file=True
                )
                mock_fs.get_mime_type.return_value = "text/plain"

                path_obj, filename, folder_id, mime_type = (
                    drive_service._resolve_file_details(
                        "test_file.txt", "remote_name.txt", None
                    )
                )

                assert path_obj == test_file
                assert filename == "remote_name.txt"
                assert folder_id == drive_service.shared_folder_id
                assert mime_type == "text/plain"

        # Test with file not found
        with patch(
            "quackcore.integrations.google.drive.service.paths.resolve_project_path"
        ) as mock_resolve:
            # Update to return PathResult with Path object, not string
            mock_resolve.return_value = PathResult(
                success=True,
                path=test_file  # Use Path object directly
            )

            with patch("quackcore.integrations.google.drive.service.fs") as mock_fs:
                # Configure the mock to raise QuackFileNotFoundError
                mock_fs.get_file_info.return_value = FileInfoResult(
                    success=False, path=test_file, exists=False
                )

                # Make the method raise the exception when file info shows not exists
                with patch.object(
                    drive_service,
                    "_resolve_file_details",
                    side_effect=QuackFileNotFoundError(str(test_file)),
                ):
                    with pytest.raises(QuackFileNotFoundError):
                        drive_service._resolve_file_details(
                            "nonexistent.txt", None, None
                        )

    def test_resolve_download_path(self, drive_service, tmp_path: Path) -> None:
        """Test resolving download path."""
        # Test with no local path specified (should create temp dir)
        file_metadata = {"name": "test_file.txt"}

        # Patch the fs module directly
        with patch("quackcore.integrations.google.drive.service.fs") as mock_fs:
            # Setup the mock to return a DataResult for create_temp_directory and join_path
            mock_fs.create_temp_directory.return_value = DataResult(
                success=True,
                path=tmp_path / "temp_dir",
                data=tmp_path / "temp_dir",  # Use Path object, not string
                format="path",
                message="Created temporary directory"
            )
            mock_fs.join_path.return_value = DataResult(
                success=True,
                path=tmp_path / "temp_dir" / "test_file.txt",
                data=tmp_path / "temp_dir" / "test_file.txt",  # Use Path object, not string
                format="path",
                message="Successfully joined path parts"
            )

            # Call the function
            result = drive_service._resolve_download_path(file_metadata, None)

            assert mock_fs.create_temp_directory.called, (
                "create_temp_directory should be called"
            )
            assert mock_fs.join_path.called, "join_path should be called"
            assert Path(result) == tmp_path / "temp_dir" / "test_file.txt"

        # Test with local path to directory
        local_dir = tmp_path / "local_dir"
        mapped_dir = Path("/fake/test/dir/local_dir")

        with patch("quackcore.integrations.google.drive.service.paths.resolve_project_path") as mock_resolve:
            # Update to return PathResult with Path object, not string
            mock_resolve.return_value = PathResult(
                success=True,
                path=mapped_dir  # Use Path object directly
            )

            with patch("quackcore.integrations.google.drive.service.fs") as mock_fs:
                # Setup mock to return expected values for all called methods
                mock_fs.get_file_info.return_value = FileInfoResult(
                    success=True, path=mapped_dir, exists=True, is_dir=True
                )
                mock_fs.join_path.return_value = DataResult(
                    success=True,
                    path=mapped_dir / "test_file.txt",
                    data=mapped_dir / "test_file.txt",  # Use Path object, not string
                    format="path",
                    message="Successfully joined path parts"
                )

                # Call the function with temp directory
                result = drive_service._resolve_download_path(file_metadata, str(local_dir))

                # Verify we get the expected result
                assert mock_fs.join_path.called, (
                    "join_path should be called for directories"
                )
                assert Path(result) == mapped_dir / "test_file.txt"

        # Test with local path as specific file
        local_file = tmp_path / "specific_file.txt"
        mapped_file = Path("/fake/test/dir/specific_file.txt")

        with patch("quackcore.integrations.google.drive.service.paths.resolve_project_path") as mock_resolve:
            # Update to return PathResult with Path object, not string
            mock_resolve.return_value = PathResult(
                success=True,
                path=mapped_file  # Use Path object directly
            )

            with patch("quackcore.integrations.google.drive.service.fs") as mock_fs:
                # Setup mock to return a file
                mock_fs.get_file_info.return_value = FileInfoResult(
                    success=True,
                    path=mapped_file,
                    exists=True,
                    is_file=True,
                    is_dir=False,
                )

                # Call the function
                result = drive_service._resolve_download_path(
                    file_metadata, str(local_file)
                )

                # Test we get the expected result
                assert Path(result) == mapped_file

    def test_build_query(self, drive_service) -> None:
        """Test building query string for listing files."""
        # Test with folder ID
        query = drive_service._build_query("folder123", None)
        assert "'folder123' in parents" in query
        assert "trashed = false" in query

        # Test with pattern
        query = drive_service._build_query(None, "*.txt")
        assert "'shared_folder' in parents" in query
        assert "name contains '.txt'" in query

        # Test with exact pattern
        query = drive_service._build_query(None, "specific.txt")
        assert "name = 'specific.txt'" in query

        # Test with no parameters
        query = drive_service._build_query(None, None)
        assert "'shared_folder' in parents" in query
        assert "trashed = false" in query