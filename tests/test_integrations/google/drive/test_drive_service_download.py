# tests/test_integrations/google/test_drive_service_download.py
"""
Tests for Google Drive service download operations.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from quackcore.errors import QuackApiError
from quackcore.integrations.google.drive.service import GoogleDriveService


class TestGoogleDriveServiceDownload:
    """Tests for the GoogleDriveService download operations."""

    @patch("googleapiclient.http.MediaIoBaseDownload")
    def test_download_file(self, mock_download_class: MagicMock) -> None:
        """Test downloading a file."""
        service = GoogleDriveService()
        service._initialized = True
        service.drive_service = MagicMock()

        # Mock API response
        mock_get = MagicMock()
        service.drive_service.files().get.return_value = mock_get
        mock_get.execute.return_value = {
            "name": "test_file.txt",
            "mimeType": "text/plain",
        }

        # Mock get_media
        mock_get_media = MagicMock()
        service.drive_service.files().get_media.return_value = mock_get_media

        # Mock the downloader
        mock_downloader = MagicMock()
        mock_download_class.return_value = mock_downloader
        mock_downloader.next_chunk.side_effect = [
            (MagicMock(progress=lambda: 0.5), False),
            (MagicMock(progress=lambda: 1.0), True),
        ]

        # Test successful download
        with patch(
            "quackcore.integrations.google.drive.service.io.BytesIO"
        ) as mock_bytesio:
            mock_io = MagicMock()
            mock_bytesio.return_value = mock_io
            mock_io.read.return_value = b"file content"

            with patch.object(service, "_resolve_download_path") as mock_resolve:
                mock_resolve.return_value = "/tmp/test_file.txt"

                with patch("quackcore.fs.service.join_path") as mock_join:
                    mock_join.return_value = Path("/tmp/test_file.txt")

                    with patch("pathlib.Path.parent") as mock_parent:
                        mock_parent.return_value = Path("/tmp")

                        with patch(
                            "quackcore.fs.service.create_directory"
                        ) as mock_mkdir:
                            mock_mkdir.return_value.success = True

                            with patch(
                                "quackcore.fs.service.write_binary"
                            ) as mock_write:
                                mock_write.return_value.success = True

                                result = service.download_file(
                                    "file123", "/tmp/test_file.txt"
                                )

                                assert result.success is True
                                assert result.content == "/tmp/test_file.txt"
                                service.drive_service.files().get.assert_called_once_with(
                                    fileId="file123", fields="name, mimeType"
                                )
                                service.drive_service.files().get_media.assert_called_once_with(
                                    fileId="file123"
                                )
                                mock_write.assert_called_once()

        # Test API error
        service.drive_service.files().get.side_effect = QuackApiError(
            "API error", service="drive"
        )
        result = service.download_file("file123")
        assert result.success is False
        assert "API error" in result.error

        # Test download error
        service.drive_service.files().get.side_effect = None
        mock_download_class.side_effect = Exception("Download error")
        result = service.download_file("file123")
        assert result.success is False
        assert "Download error" in result.error

        # Test write error
        mock_download_class.side_effect = None
        with patch.object(service, "_resolve_download_path"):
            with patch("quackcore.fs.service.join_path"):
                with patch("pathlib.Path.parent"):
                    with patch("quackcore.fs.service.create_directory"):
                        with patch("quackcore.fs.service.write_binary") as mock_write:
                            mock_write.return_value.success = False
                            mock_write.return_value.error = "Write error"

                            result = service.download_file("file123")

                            assert result.success is False
                            assert "Write error" in result.error
