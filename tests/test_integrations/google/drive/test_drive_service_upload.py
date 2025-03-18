# tests/test_integrations/google/test_drive_service_upload.py
"""
Tests for Google Drive service upload operations.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from quackcore.errors import QuackApiError
from quackcore.integrations.google.drive.service import GoogleDriveService
from quackcore.integrations.results import IntegrationResult


class TestGoogleDriveServiceUpload:
    """Tests for the GoogleDriveService upload operations."""

    @patch(
        "quackcore.integrations.google.drive.service.GoogleDriveService._execute_upload")
    def test_upload_file(self, mock_execute_upload: MagicMock, temp_dir: Path) -> None:
        """Test uploading a file."""
        service = GoogleDriveService(shared_folder_id="shared_folder")
        service._initialized = True

        # Create a test file
        test_file = temp_dir / "test_file.txt"
        test_file.write_text("test content")

        # Mock file info
        file_info_result = MagicMock()
        file_info_result.success = True
        file_info_result.exists = True

        # Mock file content
        file_content_result = MagicMock()
        file_content_result.success = True
        file_content_result.content = b"test content"

        # Mock API response
        mock_execute_upload.return_value = {
            "id": "file123",
            "webViewLink": "https://drive.google.com/file/d/file123/view",
        }

        # Test successful upload
        with patch("quackcore.paths.resolver.resolve_project_path") as mock_resolve:
            mock_resolve.return_value = str(test_file)

            with patch("quackcore.fs.service.get_file_info") as mock_info:
                mock_info.return_value = file_info_result

                with patch("quackcore.fs.service.get_mime_type") as mock_mime:
                    mock_mime.return_value = "text/plain"

                    with patch("quackcore.fs.service.read_binary") as mock_read:
                        mock_read.return_value = file_content_result

                        with patch.object(service,
                                          "set_file_permissions") as mock_permissions:
                            mock_permissions.return_value = IntegrationResult(
                                success=True)

                            result = service.upload_file(str(test_file))

                            assert result.success is True
                            assert result.content == "https://drive.google.com/file/d/file123/view"
                            mock_execute_upload.assert_called_once()
                            mock_permissions.assert_called_once_with("file123")

        # Test with file read error
        with patch("quackcore.paths.resolver.resolve_project_path") as mock_resolve:
            mock_resolve.return_value = str(test_file)

            with patch("quackcore.fs.service.get_file_info") as mock_info:
                mock_info.return_value = file_info_result

                with patch("quackcore.fs.service.get_mime_type") as mock_mime:
                    mock_mime.return_value = "text/plain"

                    with patch("quackcore.fs.service.read_binary") as mock_read:
                        mock_read.return_value.success = False
                        mock_read.return_value.error = "Read error"

                        result = service.upload_file(str(test_file))

                        assert result.success is False
                        assert "Read error" in result.error

        # Test with upload error
        with patch("quackcore.paths.resolver.resolve_project_path") as mock_resolve:
            mock_resolve.return_value = str(test_file)

            with patch("quackcore.fs.service.get_file_info") as mock_info:
                mock_info.return_value = file_info_result

                with patch("quackcore.fs.service.get_mime_type") as mock_mime:
                    mock_mime.return_value = "text/plain"

                    with patch("quackcore.fs.service.read_binary") as mock_read:
                        mock_read.return_value = file_content_result

                        mock_execute_upload.side_effect = QuackApiError("API error",
                                                                        service="drive")

                        result = service.upload_file(str(test_file))

                        assert result.success is False
                        assert "API error" in result.error

        # Test not initialized
        service._initialized = False
        with patch.object(service, "_ensure_initialized") as mock_ensure:
            mock_ensure.return_value = IntegrationResult(
                success=False,
                error="Not initialized",
            )

            result = service.upload_file(str(test_file))

            assert result.success is False
            assert "Not initialized" in result.error