# tests/test_integrations/google/drive/test_drive_service_files.py
"""
Tests for Google Drive service file operations.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from quackcore.errors import QuackFileNotFoundError
from quackcore.fs.results import FileInfoResult
from quackcore.integrations.google.drive.service import GoogleDriveService


class TestGoogleDriveServiceFiles:
    """Tests for the GoogleDriveService file operations."""

    @pytest.fixture
    def drive_service(self):
        """Set up a Google Drive service with mocked dependencies."""
        # Mock the resolver instance directly since it's imported and used
        with patch(
            "quackcore.integrations.google.drive.service.resolver"
        ) as mock_resolver:
            # Setup the resolver mock
            mock_resolver.resolve_project_path.side_effect = lambda p, *args: Path(
                f"/fake/test/dir/{Path(p).name}"
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
            "quackcore.integrations.google.drive.service.resolver.resolve_project_path"
        ) as mock_resolve:
            mock_resolve.return_value = test_file

            with patch("quackcore.fs.service.get_file_info") as mock_info:
                mock_info.return_value = FileInfoResult(
                    success=True, path=str(test_file), exists=True, is_file=True
                )

                with patch("quackcore.fs.service.split_path") as mock_split:
                    mock_split.return_value = ["path", "to", "test_file.txt"]

                    with patch("quackcore.fs.service.get_mime_type") as mock_mime:
                        mock_mime.return_value = "text/plain"

                        with patch("quackcore.fs.service.split_path") as mock_split:
                            mock_split.return_value = ["test_file.txt"]

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
            "quackcore.integrations.google.drive.service.resolver"
        ) as mock_resolver:
            mock_resolver.resolve_project_path.return_value = test_file

            with patch("quackcore.fs.service.get_file_info") as mock_info:
                mock_info.return_value = FileInfoResult(
                    success=True, path=str(test_file), exists=True, is_file=True
                )

                with patch("quackcore.fs.service.get_mime_type") as mock_mime:
                    mock_mime.return_value = "text/plain"

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
            "quackcore.integrations.google.drive.service.resolver"
        ) as mock_resolver:
            mock_resolver.resolve_project_path.return_value = test_file

            with patch("quackcore.fs.service.get_file_info") as mock_info:
                with patch("quackcore.fs.service.get_file_info") as mock_info:
                    # Configure the mock to raise QuackFileNotFoundError
                    mock_info.return_value = FileInfoResult(
                        success=False, path=str(test_file), exists=False
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

        with patch("quackcore.fs.create_temp_directory") as mock_temp:
            # Setup the mock to return a specific path
            mock_temp.return_value = tmp_path / "temp_dir"

            with patch("quackcore.fs.join_path") as mock_join:
                # Setup mock_join to return expected path
                mock_join.return_value = tmp_path / "temp_dir" / "test_file.txt"

                # Call the function
                result = drive_service._resolve_download_path(file_metadata, None)

                assert mock_temp.called, "create_temp_directory should be called"
                assert mock_join.called, "join_path should be called"
                assert str(result) == str(tmp_path / "temp_dir" / "test_file.txt")

        # Test with local path to directory
        local_dir = tmp_path / "local_dir"
        local_dir.mkdir()

        with patch("quackcore.paths.resolver.resolve_project_path") as mock_resolve:
            mock_resolve.return_value = local_dir

            with patch("quackcore.fs.get_file_info") as mock_info:
                # Setup mock to return a directory
                mock_info.return_value = FileInfoResult(
                    success=True, path=str(local_dir), exists=True, is_dir=True
                )

                with patch("quackcore.fs.join_path") as mock_join:
                    # Setup mock_join to return expected path
                    mock_join.return_value = local_dir / "test_file.txt"

                    # Test function with directory path
                    result = drive_service._resolve_download_path(file_metadata,
                                                                  str(local_dir))

                    assert str(result) == str(local_dir / "test_file.txt")
                    assert mock_join.called, "join_path should be called for directories"

        # Test with local path as specific file
        local_file = tmp_path / "specific_file.txt"

        with patch("quackcore.paths.resolver.resolve_project_path") as mock_resolve:
            mock_resolve.return_value = local_file

            with patch("quackcore.fs.get_file_info") as mock_info:
                # Setup mock to return a file
                mock_info.return_value = FileInfoResult(
                    success=True, path=str(local_file), exists=True, is_file=True,
                    is_dir=False
                )

                # Test function with file path
                result = drive_service._resolve_download_path(file_metadata,
                                                              str(local_file))

                assert str(result) == str(local_file)

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
