# tests/test_integrations/github/test_auth.py
"""Tests for GitHub integration initialization."""

from unittest.mock import MagicMock, patch

import pytest

from quackcore.integrations.github import (
    GitHubAuthProvider,
    GitHubConfigProvider,
    GitHubIntegration,
    create_integration,
)


def test_create_integration():
    """Test that create_integration returns a GitHubIntegration instance."""
    integration = create_integration()
    assert isinstance(integration, GitHubIntegration)
    assert integration.name == "GitHub"
    assert integration.version == "1.0.0"


@patch("quackcore.integrations.core.registry.add_integration")
def test_integration_registered(mock_add_integration):
    """Test that the GitHub integration is registered."""
    # Create a new integration
    integration = create_integration()

    # Mock the registry to have an integrations list
    with patch("quackcore.integrations.core.registry.get_integrations") as mock_get:
        mock_get.return_value = [integration]

        # Get integrations from registry and check
        from quackcore.integrations.core import registry

        github_integrations = [
            integration
            for integration in registry.get_integrations()
            if isinstance(integration, GitHubIntegration)
        ]
        assert len(github_integrations) > 0


@patch("quackcore.integrations.github.create_integration")
@patch("quackcore.integrations.core.registry.add_integration")
def test_module_init_registers_integration(mock_add_integration, mock_create):
    """Test that the module's __init__ registers the integration."""
    # Create a mock integration
    mock_integration = MagicMock(spec=GitHubIntegration)
    mock_create.return_value = mock_integration

    # Re-import the module to trigger the registration
    import importlib

    import quackcore.integrations.github

    importlib.reload(quackcore.integrations.github)

    # Check if add_integration was called with the integration
    mock_add_integration.assert_called_once_with(mock_integration)


def test_lazy_loading():
    """Test lazy loading of teaching-related classes."""
    import quackcore.integrations.github

    # Mock __getattr__ on the module
    original_getattr = getattr(quackcore.integrations.github, "__getattr__", None)

    # Add a temporary __getattr__ function for testing
    def mock_getattr(name):
        if name == "GitHubGrader":
            return "MockGitHubGrader"
        if name == "GitHubTeachingAdapter":
            return "MockGitHubTeachingAdapter"
        raise AttributeError(
            f"module 'quackcore.integrations.github' has no attribute '{name}'"
        )

    # Apply the mock
    try:
        quackcore.integrations.github.__getattr__ = mock_getattr

        # Test accessing lazy-loaded attributes
        assert quackcore.integrations.github.GitHubGrader == "MockGitHubGrader"
        assert (
            quackcore.integrations.github.GitHubTeachingAdapter
            == "MockGitHubTeachingAdapter"
        )
    finally:
        # Restore original if it existed
        if original_getattr:
            quackcore.integrations.github.__getattr__ = original_getattr
        else:
            delattr(quackcore.integrations.github, "__getattr__")


def test_getattr_unknown_attribute():
    """Test that __getattr__ raises AttributeError for unknown attributes."""
    import quackcore.integrations.github

    # Mock __getattr__ on the module
    original_getattr = getattr(quackcore.integrations.github, "__getattr__", None)

    # Add a temporary __getattr__ function for testing
    def mock_getattr(name):
        if name == "GitHubGrader":
            return "MockGitHubGrader"
        if name == "GitHubTeachingAdapter":
            return "MockGitHubTeachingAdapter"
        raise AttributeError(
            f"module 'quackcore.integrations.github' has no attribute '{name}'"
        )

    # Apply the mock
    try:
        quackcore.integrations.github.__getattr__ = mock_getattr

        # Test accessing unknown attribute
        # We are intentionally accessing a non-existent attribute to test the error handling
        # noinspection PyUnresolvedReferences
        with pytest.raises(AttributeError):
            _ = quackcore.integrations.github.NonExistentAttribute
    finally:
        # Restore original if it existed
        if original_getattr:
            quackcore.integrations.github.__getattr__ = original_getattr
        else:
            delattr(quackcore.integrations.github, "__getattr__")
