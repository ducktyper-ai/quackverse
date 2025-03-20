# tests/test_integrations/google/drive/test_drive_service_init.py
"""
Tests for Google Drive service initialization.
"""

from unittest.mock import MagicMock, patch

from quackcore.integrations.google.drive.service import GoogleDriveService
from quackcore.integrations.protocols import StorageIntegrationProtocol


class TestGoogleDriveServiceInit:
    """Tests for the GoogleDriveService initialization."""

    def test_init(self) -> None:
        """Test initializing the drive service."""
        # Test with explicit parameters
        service = GoogleDriveService(
            client_secrets_file="/path/to/secrets.json",
            credentials_file="/path/to/credentials.json",
            shared_folder_id="folder123",
        )

        assert service.name == "GoogleDrive"
        assert service.config["client_secrets_file"] == "/path/to/secrets.json"
        assert service.config["credentials_file"] == "/path/to/credentials.json"
        assert service.config["shared_folder_id"] == "folder123"
        assert service.scopes == GoogleDriveService.SCOPES
        assert service._initialized is False

        # Test with custom scopes
        custom_scopes = ["https://www.googleapis.com/auth/drive.readonly"]
        service = GoogleDriveService(scopes=custom_scopes)

        assert service.scopes == custom_scopes

    def test_is_storage_integration(self) -> None:
        """Test that service implements StorageIntegrationProtocol."""
        service = GoogleDriveService()

        assert isinstance(service, StorageIntegrationProtocol)

    @patch("quackcore.integrations.google.config.GoogleConfigProvider.load_config")
    def test_initialize_config(self, mock_load_config: MagicMock) -> None:
        """Test initializing the service configuration."""
        # Test with explicit parameters
        service = GoogleDriveService(
            client_secrets_file="/path/to/secrets.json",
            credentials_file="/path/to/credentials.json",
            shared_folder_id="folder123",
        )

        assert service.config["client_secrets_file"] == "/path/to/secrets.json"
        assert service.config["credentials_file"] == "/path/to/credentials.json"
        assert service.config["shared_folder_id"] == "folder123"

        # Test with config from file
        mock_load_config.return_value.success = True
        mock_load_config.return_value.content = {
            "client_secrets_file": "/config/secrets.json",
            "credentials_file": "/config/credentials.json",
            "shared_folder_id": "config_folder",
        }

        service = GoogleDriveService(config_path="/path/to/config.yaml")
        assert service.config["client_secrets_file"] == "/config/secrets.json"
        assert service.config["credentials_file"] == "/config/credentials.json"
        assert service.config["shared_folder_id"] == "config_folder"

        # Test with invalid config (should use default)
        mock_load_config.return_value.success = False

        with patch(
            "quackcore.integrations.google.config.GoogleConfigProvider.get_default_config"
        ) as mock_default:
            mock_default.return_value = {
                "client_secrets_file": "/default/secrets.json",
                "credentials_file": "/default/credentials.json",
            }

            service = GoogleDriveService(config_path="/invalid/config.yaml")
            assert service.config["client_secrets_file"] == "/default/secrets.json"
            assert service.config["credentials_file"] == "/default/credentials.json"

    @patch("quackcore.integrations.google.auth.GoogleAuthProvider.get_credentials")
    @patch("googleapiclient.discovery.build")
    def test_initialize(
        self, mock_build: MagicMock, mock_get_credentials: MagicMock
    ) -> None:
        """Test initializing the drive service."""
        service = GoogleDriveService(
            client_secrets_file="/path/to/secrets.json",
            credentials_file="/path/to/credentials.json",
        )

        # Mock the drive service
        mock_drive_service = MagicMock()
        mock_build.return_value = mock_drive_service

        # Mock credentials
        mock_credentials = MagicMock()
        mock_get_credentials.return_value = mock_credentials

        # Test successful initialization
        result = service.initialize()
        assert result.success is True
        assert service._initialized is True
        assert service.drive_service is mock_drive_service

        mock_get_credentials.assert_called_once()
        mock_build.assert_called_once_with("drive", "v3", credentials=mock_credentials)

        # Test authentication error
        mock_get_credentials.side_effect = Exception("Auth error")

        service = GoogleDriveService(
            client_secrets_file="/path/to/secrets.json",
            credentials_file="/path/to/credentials.json",
        )
        result = service.initialize()

        assert result.success is False
        assert "Auth error" in result.error
        assert service._initialized is False

        # Test API error
        mock_get_credentials.side_effect = None
        mock_build.side_effect = Exception("API error")

        service = GoogleDriveService(
            client_secrets_file="/path/to/secrets.json",
            credentials_file="/path/to/credentials.json",
        )
        result = service.initialize()

        assert result.success is False
        assert "API error" in result.error
        assert service._initialized is False
