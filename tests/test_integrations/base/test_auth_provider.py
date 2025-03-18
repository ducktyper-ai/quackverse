# tests/test_integrations/base/test_auth_provider.py
"""
Tests for the BaseAuthProvider class.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from quackcore.integrations.base import BaseAuthProvider
from tests.test_integrations.base.auth_provider_impl import MockAuthProvider


class TestBaseAuthProvider:
    """Tests for the BaseAuthProvider class."""

    def test_init(self, temp_dir: Path) -> None:
        """Test initializing the auth provider."""
        # Test with credentials file
        credentials_file = temp_dir / "credentials.json"
        provider = MockAuthProvider(credentials_file=str(credentials_file))

        assert provider.credentials_file == str(credentials_file)
        assert provider.authenticated is False
        assert provider.name == "test_auth"

        # Test without credentials file
        provider = MockAuthProvider()
        assert provider.credentials_file is None

    def test_resolve_path(self) -> None:
        """Test resolving a relative path."""
        provider = MockAuthProvider()

        # Test with absolute path
        abs_path = "/absolute/path"
        resolved = provider._resolve_path(abs_path)
        assert resolved == abs_path

        # Test with relative path (mocking resolver)
        with patch(
                "quackcore.integrations.base.resolver.resolve_project_path") as mock_resolve:
            mock_resolve.return_value = "/resolved/path"
            resolved = provider._resolve_path("relative/path")
            assert resolved == "/resolved/path"
            mock_resolve.assert_called_once()

        # Test with resolver exception
        with patch(
                "quackcore.integrations.base.resolver.resolve_project_path") as mock_resolve:
            mock_resolve.side_effect = Exception("Test error")
            with patch("quackcore.fs.service.normalize_path") as mock_normalize:
                mock_normalize.return_value = "/normalized/path"
                resolved = provider._resolve_path("relative/path")
                assert resolved == "/normalized/path"
                mock_normalize.assert_called_once()

    def test_abstract_methods(self) -> None:
        """Test that abstract methods must be implemented."""
        # Attempt to create a class without implementing the abstract methods
        with pytest.raises(TypeError):
            class InvalidProvider(BaseAuthProvider):
                pass

            InvalidProvider()  # This should raise TypeError

    def test_authenticate(self, temp_dir: Path) -> None:
        """Test authentication flow."""
        # Create a provider with credentials file
        credentials_file = temp_dir / "credentials.json"
        credentials_file.touch()
        provider = MockAuthProvider(credentials_file=str(credentials_file))

        # Test successful authentication
        result = provider.authenticate()
        assert result.success is True
        assert provider.authenticated is True

        # Test with missing credentials file
        provider = MockAuthProvider(credentials_file="/nonexistent/path")
        result = provider.authenticate()
        assert result.success is False
        assert "not found" in result.error

    def test_refresh_credentials(self) -> None:
        """Test refreshing credentials."""
        provider = MockAuthProvider()

        # Test refresh before authentication
        result = provider.refresh_credentials()
        assert result.success is False
        assert "Not authenticated" in result.error

        # Test refresh after authentication
        provider.authenticated = True
        result = provider.refresh_credentials()
        assert result.success is True
        assert "refreshed" in result.message

    def test_ensure_credentials_directory(self, temp_dir: Path) -> None:
        """Test ensuring the credentials directory exists."""
        # Test with existing directory
        credentials_file = temp_dir / "creds" / "credentials.json"
        provider = MockAuthProvider(credentials_file=str(credentials_file))

        with patch("quackcore.fs.service.create_directory") as mock_create:
            mock_create.return_value.success = True
            result = provider._ensure_credentials_directory()
            assert result is True
            mock_create.assert_called_once()

        # Test with creation error
        with patch("quackcore.fs.service.create_directory") as mock_create:
            mock_create.return_value.success = False
            result = provider._ensure_credentials_directory()
            assert result is False

        # Test without credentials file
        provider = MockAuthProvider()
        result = provider._ensure_credentials_directory()
        assert result is False

    def test_base_save_credentials(self) -> None:
        """Test the default save_credentials implementation."""
        provider = BaseAuthProvider.__new__(BaseAuthProvider)
        provider.logger = MagicMock()

        result = provider.save_credentials()
        assert result is False
        provider.logger.warning.assert_called_once()