# tests/test_integrations/google/test_drive_service_permissions.py
"""
Tests for Google Drive service permissions operations.
"""

from unittest.mock import MagicMock

from quackcore.errors import QuackApiError
from quackcore.integrations.google.drive.service import GoogleDriveService


class TestGoogleDriveServicePermissions:
    """Tests for the GoogleDriveService permissions operations."""

    def test_set_file_permissions(self) -> None:
        """Test setting file permissions."""
        service = GoogleDriveService()
        service._initialized = True
        service.drive_service = MagicMock()

        # Mock API response
        mock_create = MagicMock()
        service.drive_service.permissions().create.return_value = mock_create
        mock_create.execute.return_value = {"id": "perm1"}

        # Test successful permission setting
        result = service.set_file_permissions("file123", "writer", "user")

        assert result.success is True
        assert result.content is True
        service.drive_service.permissions().create.assert_called_once_with(
            fileId="file123",
            body={"type": "user", "role": "writer", "allowFileDiscovery": True},
            fields="id"
        )

        # Test with default parameters
        service.drive_service.permissions().create.reset_mock()
        service.config["default_share_access"] = "commenter"

        result = service.set_file_permissions("file123")

        assert result.success is True
        service.drive_service.permissions().create.assert_called_once_with(
            fileId="file123",
            body={"type": "anyone", "role": "commenter", "allowFileDiscovery": True},
            fields="id"
        )

        # Test API error
        service.drive_service.permissions().create.side_effect = QuackApiError(
            "API error", service="drive")
        result = service.set_file_permissions("file123")
        assert result.success is False
        assert "API error" in result.error

    def test_get_sharing_link(self) -> None:
        """Test getting a sharing link."""
        service = GoogleDriveService()
        service._initialized = True
        service.drive_service = MagicMock()

        # Mock API response
        mock_get = MagicMock()
        service.drive_service.files().get.return_value = mock_get
        mock_get.execute.return_value = {
            "webViewLink": "https://drive.google.com/file/d/file123/view",
        }

        # Test successful link retrieval
        result = service.get_sharing_link("file123")

        assert result.success is True
        assert result.content == "https://drive.google.com/file/d/file123/view"
        service.drive_service.files().get.assert_called_once_with(
            fileId="file123", fields="webViewLink, webContentLink"
        )

        # Test with only content link
        mock_get.execute.return_value = {
            "webContentLink": "https://drive.google.com/uc?id=file123",
        }

        result = service.get_sharing_link("file123")

        assert result.success is True
        assert result.content == "https://drive.google.com/uc?id=file123"

        # Test with no links (should generate default)
        mock_get.execute.return_value = {}

        result = service.get_sharing_link("file123")

        assert result.success is True
        assert result.content == "https://drive.google.com/file/d/file123/view"

        # Test API error
        service.drive_service.files().get.side_effect = QuackApiError("API error",
                                                                      service="drive")
        result = service.get_sharing_link("file123")
        assert result.success is False
        assert "API error" in result.error