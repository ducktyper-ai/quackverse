# tests/test_integrations/google/test_drive_service_files.py
"""
Tests for Google Drive service file operations.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from quackcore.errors import QuackFileNotFoundError
from quackcore.integrations.google.drive.service import GoogleDriveService


class TestGoogleDriveServiceFiles:
    """Tests for the GoogleDriveService file operations."""

    def test_resolve_file_details(self, temp_dir: Path) -> None:
        """Test resolving file details."""
        service = GoogleDriveService()

        # Create a test file
        test_file = temp_dir / "test_file.txt"
        test_file.write_text("test content")

        # Test with relative path and parent folder
        with patch("quackcore.paths.resolver.resolve_project_path") as mock_resolve:
            mock_resolve.return_value = str(test_file)

            with patch("quackcore.fs.service.get_file_info") as mock_info:
                mock_info.return_value.success = True
                mock_info.return_value.exists = True

                with patch("quackcore.fs.service.split_path") as mock_split:
                    mock_split.return_value = ["path", "to", "test_file.txt"]

                    with patch("quackcore.fs.service.get_mime_type") as mock_mime:
                        mock_mime.return_value = "text/plain"

                        path_obj, filename, folder_id, mime_type = service._resolve_file_details(
                            "test_file.txt", None, "folder123"
                        )

                        assert path_obj == str(test_file)
                        assert filename == "test_file.txt"
                        assert folder_id == "folder123"
                        assert mime_type == "text/plain"

        # Test with remote path specified
        with patch("quackcore.paths.resolver.resolve_project_path") as mock_resolve:
            mock_resolve.return_value = str(test_file)

            with patch("quackcore.fs.service.get_file_info") as mock_info:
                mock_info.return_value.success = True
                mock_info.return_value.exists = True

                with patch("quackcore.fs.service.get_mime_type") as mock_mime:
                    mock_mime.return_value = "text/plain"

                    path_obj, filename, folder_id, mime_type = service._resolve_file_details(
                        "test_file.txt", "remote_name.txt", None
                    )

                    assert path_obj == str(test_file)
                    assert filename == "remote_name.txt"
                    assert folder_id == service.shared_folder_id
                    assert mime_type == "text/plain"

        # Test with file not found
        with patch("quackcore.paths.resolver.resolve_project_path") as mock_resolve:
            mock_resolve.return_value = str(test_file)

            with patch("quackcore.fs.service.get_file_info") as mock_info:
                mock_info.return_value.success = False
                mock_info.return_value.exists = False

                with pytest.raises(QuackFileNotFoundError):
                    service._resolve_file_details("nonexistent.txt", None, None)

    def test_resolve_download_path(self, temp_dir: Path) -> None:
        """Test resolving download path."""
        service = GoogleDriveService()

        # Test with no local path specified (should create temp dir)
        file_metadata = {"name": "test_file.txt"}

        with patch("quackcore.fs.service.create_temp_directory") as mock_temp:
            mock_temp.return_value = str(temp_dir / "temp_dir")

            with patch("quackcore.fs.service.join_path") as mock_join:
                mock_join.return_value = str(temp_dir / "temp_dir" / "test_file.txt")

                result = service._resolve_download_path(file_metadata, None)
                assert result == str(temp_dir / "temp_dir" / "test_file.txt")

        # Test with local path to directory
        local_dir = temp_dir / "local_dir"

        with patch("quackcore.paths.resolver.resolve_project_path") as mock_resolve:
            mock_resolve.return_value = str(local_dir)

            with patch("quackcore.fs.service.get_file_info") as mock_info:
                mock_info.return_value.success = True
                mock_info.return_value.exists = True
                mock_info.return_value.is_dir = True

                with patch("quackcore.fs.service.join_path") as mock_join:
                    mock_join.return_value = str(local_dir / "test_file.txt")

                    result = service._resolve_download_path(file_metadata,
                                                            str(local_dir))
                    assert result == str(local_dir / "test_file.txt")

        # Test with local path as specific file
        local_file = temp_dir / "specific_file.txt"

        with patch("quackcore.paths.resolver.resolve_project_path") as mock_resolve:
            mock_resolve.return_value = str(local_file)

            with patch("quackcore.fs.service.get_file_info") as mock_info:
                mock_info.return_value.success = True
                mock_info.return_value.exists = True
                mock_info.return_value.is_dir = False

                result = service._resolve_download_path(file_metadata, str(local_file))
                assert result == str(local_file)

    def test_build_query(self) -> None:
        """Test building query string for listing files."""
        service = GoogleDriveService(shared_folder_id="shared_folder")

        # Test with folder ID
        query = service._build_query("folder123", None)
        assert "'folder123' in parents" in query
        assert "trashed = false" in query

        # Test with pattern
        query = service._build_query(None, "*.txt")
        assert "'shared_folder' in parents" in query
        assert "name contains '.txt'" in query

        # Test with exact pattern
        query = service._build_query(None, "specific.txt")
        assert "name = 'specific.txt'" in query

        # Test with no parameters
        query = service._build_query(None, None)
        assert "'shared_folder' in parents" in query
        assert "trashed = false" in query