# tests/quackcore/test_integrations/core/base/test_auth_provider.py
"""
Tests for the BaseAuthProvider class.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from quackcore.integrations.core.base import BaseAuthProvider
from tests.quackcore.test_integrations.core.base.auth_provider_impl import MockAuthProvider


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
            "quackcore.integrations.core.base.resolver.resolve_project_path"
        ) as mock_resolve:
            mock_resolve.return_value = "/resolved/path"
            resolved = provider._resolve_path("relative/path")
            assert resolved == "/resolved/path"
            mock_resolve.assert_called_once()

        # Test with resolver exception - patch the fs service instance
        with patch(
            "quackcore.integrations.core.base.resolver.resolve_project_path"
        ) as mock_resolve:
            mock_resolve.side_effect = Exception("Test error")
            # Create a mock service instance
            mock_service = MagicMock()
            mock_service.normalize_path.return_value = Path("/normalized/path")
            # Patch the import of the service
            with patch("quackcore.fs.service", mock_service):
                resolved = provider._resolve_path("relative/path")
                assert resolved == "/normalized/path"
                mock_service.normalize_path.assert_called_once_with("relative/path")

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

    # In tests/test_integrations/base/test_auth_provider.py
    def test_ensure_credentials_directory(self, temp_dir: Path) -> None:
        """Test ensuring the credentials directory exists."""
        # Test with existing directory
        credentials_file = temp_dir / "creds" / "credentials.json"
        provider = MockAuthProvider(credentials_file=str(credentials_file))

        # Now correctly patch the method
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
        # Instead of trying to instantiate BaseAuthProvider directly,
        # create a concrete mock instance and replace its save_credentials method
        provider = MockAuthProvider()
        provider.logger = MagicMock()

        # Replace the save_credentials method with the one from BaseAuthProvider
        original_save = provider.save_credentials
        provider.save_credentials = BaseAuthProvider.save_credentials.__get__(
            provider, MockAuthProvider
        )

        try:
            result = provider.save_credentials()
            assert result is False
            provider.logger.warning.assert_called_once()
        finally:
            # Restore the original method
            provider.save_credentials = original_save
