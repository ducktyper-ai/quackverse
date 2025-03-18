# tests/test_integrations/google/test_drive_service_folders.py
"""
Tests for Google Drive service folder operations.
"""

from unittest.mock import MagicMock, patch

from quackcore.errors import QuackApiError
from quackcore.integrations.google.drive.service import GoogleDriveService
from quackcore.integrations.results import IntegrationResult


class TestGoogleDriveServiceFolders:
    """Tests for the GoogleDriveService folder operations."""

    def test_create_folder(self) -> None:
        """Test creating a folder."""
        service = GoogleDriveService(shared_folder_id="shared_folder")
        service._initialized = True
        service.drive_service = MagicMock()

        # Mock API response
        mock_create = MagicMock()
        service.drive_service.files().create.return_value = mock_create
        mock_create.execute.return_value = {
            "id": "new_folder",
            "webViewLink": "https://drive.google.com/drive/folders/new_folder",
        }

        # Test successful folder creation
        with patch.object(service, "set_file_permissions") as mock_permissions:
            mock_permissions.return_value = IntegrationResult(success=True)

            result = service.create_folder("New Folder", "parent_folder")

            assert result.success is True
            assert result.content == "new_folder"
            service.drive_service.files().create.assert_called_once_with(
                body={
                    "name": "New Folder",
                    "mimeType": "application/vnd.google-apps.folder",
                    "parents": ["parent_folder"],
                },
                fields="id, webViewLink",
            )
            mock_permissions.assert_called_once_with("new_folder")

        # Test with default parent folder
        service.drive_service.files().create.reset_mock()
        result = service.create_folder("New Folder")
        assert result.success is True
        service.drive_service.files().create.assert_called_once_with(
            body={
                "name": "New Folder",
                "mimeType": "application/vnd.google-apps.folder",
                "parents": ["shared_folder"],
            },
            fields="id, webViewLink",
        )

        # Test API error
        service.drive_service.files().create.side_effect = QuackApiError(
            "API error", service="drive"
        )
        result = service.create_folder("Error Folder")
        assert result.success is False
        assert "API error" in result.error
