# tests/test_integrations/google/test_auth_provider.py
"""
Tests for Google authentication provider.

This module tests the GoogleAuthProvider class, including authentication flow,
token management, and credential handling.
"""

from unittest.mock import MagicMock, patch

import pytest

from quackcore.errors import QuackIntegrationError
from quackcore.integrations.google.auth import GoogleAuthProvider
from quackcore.integrations.results import AuthResult


class TestGoogleAuthProvider:
    """Tests for the GoogleAuthProvider class."""

    def test_init(self) -> None:
        """Test initializing the auth provider."""
        # Test with minimum parameters
        with patch("quackcore.integrations.google.auth.fs.get_file_info") as mock_info:
            mock_info.return_value.success = True
            mock_info.return_value.exists = True

            provider = GoogleAuthProvider(
                client_secrets_file="/path/to/secrets.json",
            )

            assert provider.name == "GoogleAuth"
            assert provider.client_secrets_file == "/path/to/secrets.json"
            assert provider.credentials_file is None
            assert provider.authenticated is False
            assert provider.scopes == []

        # Test with all parameters
        with patch("quackcore.integrations.google.auth.fs.get_file_info") as mock_info:
            mock_info.return_value.success = True
            mock_info.return_value.exists = True

            scopes = ["https://www.googleapis.com/auth/drive.file"]
            provider = GoogleAuthProvider(
                client_secrets_file="/path/to/secrets.json",
                credentials_file="/path/to/credentials.json",
                scopes=scopes,
            )

            assert provider.client_secrets_file == "/path/to/secrets.json"
            assert provider.credentials_file == "/path/to/credentials.json"
            assert provider.scopes == scopes

    def test_verify_client_secrets_file(self) -> None:
        """Test verifying the client secrets file."""
        # Test with existing file
        with patch("quackcore.integrations.google.auth.fs.get_file_info") as mock_info:
            mock_info.return_value.success = True
            mock_info.return_value.exists = True

            provider = GoogleAuthProvider(
                client_secrets_file="/path/to/secrets.json",
            )

            # Method is called during initialization, so no exception is raised
            assert provider.client_secrets_file == "/path/to/secrets.json"

        # Test with non-existing file
        with patch("quackcore.integrations.google.auth.fs.get_file_info") as mock_info:
            mock_info.return_value.success = True
            mock_info.return_value.exists = False

            with pytest.raises(QuackIntegrationError) as excinfo:
                GoogleAuthProvider(
                    client_secrets_file="/nonexistent/secrets.json",
                )

            assert "Client secrets file not found" in str(excinfo.value)

    def test_authenticate(self) -> None:
        """Test authentication flow."""
        # Mock file existence check
        with patch("quackcore.integrations.google.auth.fs.get_file_info") as mock_info:
            mock_info.return_value.success = True
            mock_info.return_value.exists = True

            provider = GoogleAuthProvider(
                client_secrets_file="/path/to/secrets.json",
                credentials_file="/path/to/credentials.json",
            )

        # Test with new OAuth flow
        with patch("google.oauth2.credentials.Credentials") as mock_creds_class:
            with patch(
                    "quackcore.integrations.google.auth.fs.get_file_info") as mock_info:
                mock_info.return_value.exists = True

                with patch(
                        "quackcore.integrations.google.auth.fs.read_json") as mock_read:
                    mock_read.return_value.success = True
                    mock_read.return_value.data = {}

                    mock_creds = MagicMock()
                    mock_creds.valid = False

                    mock_creds_class.from_authorized_user_info.return_value = mock_creds

                    with patch(
                            "google_auth_oauthlib.flow.InstalledAppFlow"
                    ) as mock_flow_class:
                        mock_flow = MagicMock()
                        mock_flow_class.from_client_secrets_file.return_value = (
                            mock_flow
                        )

                        new_creds = MagicMock()
                        new_creds.token = "new_token"
                        new_creds.expiry = MagicMock()
                        new_creds.expiry.timestamp.return_value = 1234567890

                        mock_flow.run_local_server.return_value = new_creds

                        with patch.object(
                                provider, "_save_credentials_to_file"
                        ) as mock_save:
                            mock_save.return_value = True

                            result = provider.authenticate()

                            assert result.success is True
                            assert provider.authenticated is True
                            assert provider.auth is new_creds
                            assert result.token == "new_token"
                            mock_flow_class.from_client_secrets_file.assert_called_once_with(
                                "/path/to/secrets.json",
                                [],
                            )
                            mock_flow.run_local_server.assert_called_once_with(port=0)
                            mock_save.assert_called_once_with(new_creds)

        # Test with expired credentials needing refresh
        with patch("google.oauth2.credentials.Credentials") as mock_creds_class:
            with patch("quackcore.integrations.google.auth.fs.get_file_info") as mock_info:
                mock_info.return_value.exists = True

                with patch("quackcore.integrations.google.auth.fs.read_json") as mock_read:
                    mock_read.return_value.success = True
                    mock_read.return_value.data = {
                        "token": "old_token",
                        "refresh_token": "refresh_token",
                    }

                    mock_creds = MagicMock()
                    mock_creds.expired = True
                    mock_creds.refresh_token = True
                    mock_creds.token = "refreshed_token"
                    mock_creds.expiry = MagicMock()
                    mock_creds.expiry.timestamp.return_value = 1234567890

                    mock_creds_class.from_authorized_user_info.return_value = mock_creds

                    with patch.object(
                        provider, "_save_credentials_to_file"
                    ) as mock_save:
                        mock_save.return_value = True

                        result = provider.authenticate()

                        assert result.success is True
                        assert provider.authenticated is True
                        assert provider.auth is mock_creds
                        assert result.token == "refreshed_token"
                        assert mock_save.called

        # Test with new OAuth flow
        with patch("google.oauth2.credentials.Credentials") as mock_creds_class:
            with patch("quackcore.integrations.google.auth.fs.get_file_info") as mock_info:
                mock_info.return_value.exists = True

                with patch("quackcore.integrations.google.auth.fs.read_json") as mock_read:
                    mock_read.return_value.success = True
                    mock_read.return_value.data = {}

                    mock_creds = MagicMock()
                    mock_creds.valid = False

                    mock_creds_class.from_authorized_user_info.return_value = mock_creds

                    with patch(
                        "google_auth_oauthlib.flow.InstalledAppFlow"
                    ) as mock_flow_class:
                        mock_flow = MagicMock()
                        mock_flow_class.from_client_secrets_file.return_value = (
                            mock_flow
                        )

                        new_creds = MagicMock()
                        new_creds.token = "new_token"
                        new_creds.expiry = MagicMock()
                        new_creds.expiry.timestamp.return_value = 1234567890

                        mock_flow.run_local_server.return_value = new_creds

                        with patch.object(
                            provider, "_save_credentials_to_file"
                        ) as mock_save:
                            mock_save.return_value = True

                            result = provider.authenticate()

                            assert result.success is True
                            assert provider.authenticated is True
                            assert provider.auth is new_creds
                            assert result.token == "new_token"
                            mock_flow_class.from_client_secrets_file.assert_called_once_with(
                                "/path/to/secrets.json",
                                [],
                            )
                            mock_flow.run_local_server.assert_called_once_with(port=0)
                            mock_save.assert_called_once_with(new_creds)

        # Test with authentication error
        with patch("google.oauth2.credentials.Credentials") as mock_creds_class:
            mock_creds_class.side_effect = Exception("Auth error")

            result = provider.authenticate()

            assert result.success is False
            assert "Failed to authenticate with Google" in result.error
            assert provider.authenticated is False

    def test_refresh_credentials(self) -> None:
        """Test refreshing credentials."""
        # Mock file existence check
        with patch("quackcore.integrations.google.auth.fs.get_file_info") as mock_info:
            mock_info.return_value.success = True
            mock_info.return_value.exists = True

            provider = GoogleAuthProvider(
                client_secrets_file="/path/to/secrets.json",
                credentials_file="/path/to/credentials.json",
            )

        # Test with no existing credentials
        result = provider.refresh_credentials()
        assert result.success is False
        assert "Failed to authenticate with Google" in result.error

        # Test with valid credentials
        provider.auth = MagicMock()
        provider.auth.expired = False
        provider.auth.token = "valid_token"
        provider.auth.expiry = MagicMock()
        provider.auth.expiry.timestamp.return_value = 1234567890
        provider.authenticated = True

        result = provider.refresh_credentials()
        assert result.success is True
        assert result.message == "Credentials are valid, no refresh needed"
        assert result.token == "valid_token"
        assert result.expiry == 1234567890

        # Test with expired credentials
        provider.auth = MagicMock()
        provider.auth.expired = True
        provider.auth.token = "refreshed_token"
        provider.auth.expiry = MagicMock()
        provider.auth.expiry.timestamp.return_value = 1234567890

        with patch.object(provider, "_save_credentials_to_file") as mock_save:
            mock_save.return_value = True

            result = provider.refresh_credentials()

            assert result.success is True
            assert result.message == "Successfully refreshed credentials"
            assert result.token == "refreshed_token"
            assert mock_save.called

        # Test with refresh error
        provider.auth = MagicMock()
        provider.auth.expired = True
        provider.auth.refresh.side_effect = Exception("Refresh error")

        result = provider.refresh_credentials()
        assert result.success is False
        assert "Failed to refresh Google credentials" in result.error
        assert provider.authenticated is False

    def test_get_credentials(self) -> None:
        """Test getting credentials."""
        # Mock file existence check
        with patch("quackcore.integrations.google.auth.fs.get_file_info") as mock_info:
            mock_info.return_value.success = True
            mock_info.return_value.exists = True

            provider = GoogleAuthProvider(
                client_secrets_file="/path/to/secrets.json",
                credentials_file="/path/to/credentials.json",
            )

        # Test with no existing credentials
        with patch.object(provider, "authenticate") as mock_auth:
            mock_auth.return_value = AuthResult(
                success=False,
                error="Auth failed",
            )

            with pytest.raises(QuackIntegrationError) as excinfo:
                provider.get_credentials()

            assert "No valid Google credentials available" in str(excinfo.value)

        # Test with valid credentials
        provider.auth = MagicMock()
        provider.authenticated = True

        creds = provider.get_credentials()
        assert creds is provider.auth

        # Test with successful authentication
        provider.auth = None
        provider.authenticated = False

        with patch.object(provider, "authenticate") as mock_auth:
            mock_creds = MagicMock()
            provider.auth = mock_creds
            provider.authenticated = True

            mock_auth.return_value = AuthResult(
                success=True,
                token="new_token",
            )

            creds = provider.get_credentials()
            assert creds is mock_creds

    def test_save_credentials(self) -> None:
        """Test saving credentials."""
        # Mock file existence check
        with patch("quackcore.integrations.google.auth.fs.get_file_info") as mock_info:
            mock_info.return_value.success = True
            mock_info.return_value.exists = True

            provider = GoogleAuthProvider(
                client_secrets_file="/path/to/secrets.json",
                credentials_file="/path/to/credentials.json",
            )

        # Test with no credentials
        provider.auth = None
        result = provider.save_credentials()
        assert result is False

        # Test with valid credentials
        provider.auth = MagicMock()

        with patch.object(provider, "_save_credentials_to_file") as mock_save:
            mock_save.return_value = True

            result = provider.save_credentials()
            assert result is True
            mock_save.assert_called_once_with(provider.auth)

    def test_save_credentials_to_file(self) -> None:
        """Test saving credentials to file."""
        # Mock file existence check
        with patch("quackcore.integrations.google.auth.fs.get_file_info") as mock_info:
            mock_info.return_value.success = True
            mock_info.return_value.exists = True

            provider = GoogleAuthProvider(
                client_secrets_file="/path/to/secrets.json",
                credentials_file="/path/to/credentials.json",
            )

        # Test with no credentials file
        provider.credentials_file = None
        result = provider._save_credentials_to_file(MagicMock())
        assert result is False

        # Reset credentials_file for subsequent tests
        provider.credentials_file = "/path/to/credentials.json"

        # Test with directory creation error
        with patch("quackcore.integrations.google.auth.fs.split_path") as mock_split:
            mock_split.return_value = ["path", "to", "credentials.json"]

            with patch("quackcore.integrations.google.auth.fs.join_path") as mock_join:
                mock_join.return_value = "/path/to"

                with patch(
                        "quackcore.integrations.google.auth.fs.create_directory") as mock_mkdir:
                    mock_mkdir.return_value = MagicMock(success=False,
                                                        error="Directory creation failed")

                    result = provider._save_credentials_to_file(MagicMock())
                    assert result is False

        # Test with to_json method
        creds = MagicMock()
        creds.to_json.return_value = '{"token": "test_token"}'

        with patch("quackcore.integrations.google.auth.fs.split_path") as mock_split:
            mock_split.return_value = ["path", "to", "credentials.json"]

            with patch("quackcore.integrations.google.auth.fs.join_path") as mock_join:
                mock_join.return_value = "/path/to"

                with patch(
                        "quackcore.integrations.google.auth.fs.create_directory") as mock_mkdir:
                    mock_mkdir.return_value = MagicMock(success=True)

                    with patch(
                            "quackcore.integrations.google.auth.fs.create_temp_file") as mock_temp:
                        mock_temp.return_value = "/tmp/temp.json"

                        with patch(
                                "quackcore.integrations.google.auth.fs.write_text") as mock_write:
                            mock_write.return_value = MagicMock(success=True)

                            with patch(
                                    "quackcore.integrations.google.auth.fs.read_json") as mock_read:
                                mock_read.return_value = MagicMock(
                                    success=True,
                                    data={"token": "test_token"}
                                )

                                with patch(
                                        "quackcore.integrations.google.auth.fs.delete") as mock_delete:
                                    with patch(
                                            "quackcore.integrations.google.auth.fs.write_json") as mock_write_json:
                                        mock_write_json.return_value = MagicMock(
                                            success=True)

                                        result = provider._save_credentials_to_file(
                                            creds)
                                        assert result is True
                                        mock_write_json.assert_called_once_with(
                                            "/path/to/credentials.json",
                                            {"token": "test_token"},
                                        )

        # Test with dictionary method - create a new provider instance
        with patch("quackcore.integrations.google.auth.fs.get_file_info") as mock_info:
            mock_info.return_value.success = True
            mock_info.return_value.exists = True

            # Create a fresh provider instance
            provider = GoogleAuthProvider(
                client_secrets_file="/path/to/secrets.json",
                credentials_file="/path/to/credentials.json",
            )

            creds = MagicMock()
            creds.token = "test_token"
            creds.refresh_token = "refresh_token"
            creds.token_uri = "https://oauth2.googleapis.com/token"
            creds.client_id = "client_id"
            creds.client_secret = "client_secret"
            creds.scopes = ["https://www.googleapis.com/auth/drive.file"]

            with patch(
                    "quackcore.integrations.google.auth.fs.split_path") as mock_split:
                mock_split.return_value = ["path", "to", "credentials.json"]

                with patch(
                        "quackcore.integrations.google.auth.fs.join_path") as mock_join:
                    mock_join.return_value = "/path/to"

                    with patch(
                            "quackcore.integrations.google.auth.fs.create_directory") as mock_mkdir:
                        # Create a proper mock object with success=True
                        mock_mkdir.return_value = MagicMock(success=True)

                        with patch(
                                "quackcore.integrations.google.auth.fs.write_json") as mock_write_json:
                            # Create a proper mock object with success=True
                            mock_write_json.return_value = MagicMock(success=True)

                            result = provider._save_credentials_to_file(creds)
                            assert result is True

                            # Check that the dictionary was properly constructed
                            creds_dict = mock_write_json.call_args[0][1]
                            assert creds_dict["token"] == "test_token"
                            assert creds_dict["refresh_token"] == "refresh_token"
                            assert creds_dict[
                                       "token_uri"] == "https://oauth2.googleapis.com/token"
                            assert creds_dict["client_id"] == "client_id"
                            assert creds_dict["client_secret"] == "client_secret"
                            assert creds_dict["scopes"] == [
                                "https://www.googleapis.com/auth/drive.file"]

        # Test with attribute error
        creds = MagicMock()
        # Missing required attributes
        delattr(creds, "token")

        with patch("quackcore.integrations.google.auth.fs.split_path") as mock_split:
            mock_split.return_value = ["path", "to", "credentials.json"]

            with patch("quackcore.integrations.google.auth.fs.join_path") as mock_join:
                mock_join.return_value = "/path/to"

                with patch(
                        "quackcore.integrations.google.auth.fs.create_directory") as mock_mkdir:
                    mock_mkdir.return_value.success = True

                    result = provider._save_credentials_to_file(creds)
                    assert result is False

        # Test with file write error
        creds = MagicMock()
        creds.to_json.return_value = '{"token": "test_token"}'

        with patch("quackcore.integrations.google.auth.fs.split_path") as mock_split:
            mock_split.return_value = ["path", "to", "credentials.json"]

            with patch("quackcore.integrations.google.auth.fs.join_path") as mock_join:
                mock_join.return_value = "/path/to"

                with patch(
                        "quackcore.integrations.google.auth.fs.create_directory") as mock_mkdir:
                    mock_mkdir.return_value.success = True

                    with patch(
                            "quackcore.integrations.google.auth.fs.create_temp_file") as mock_temp:
                        mock_temp.return_value = "/tmp/temp.json"

                        with patch(
                                "quackcore.integrations.google.auth.fs.write_text") as mock_write:
                            mock_write.return_value.success = True

                            with patch(
                                    "quackcore.integrations.google.auth.fs.read_json") as mock_read:
                                mock_read.return_value.success = True
                                mock_read.return_value.data = {"token": "test_token"}

                                with patch(
                                        "quackcore.integrations.google.auth.fs.delete"
                                ) as mock_delete:
                                    with patch(
                                            "quackcore.integrations.google.auth.fs.write_json"
                                    ) as mock_write_json:
                                        mock_write_json.return_value.success = False

                                        result = provider._save_credentials_to_file(
                                            creds
                                        )
                                        assert result is False