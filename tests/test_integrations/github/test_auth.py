# tests/test_integrations/github/test_auth.py
"""Tests for GitHub integration initialization."""

from unittest.mock import MagicMock, patch

import pytest

from quackcore.integrations.core import registry
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


def test_integration_registered():
    """Test that the GitHub integration is registered."""
    # First remove any existing GitHub integration from the registry
    for i, integration in enumerate(registry.integrations):
        if isinstance(integration, GitHubIntegration):
            registry.integrations.pop(i)
            break

    # Now register a new one and check it's there
    integration = create_integration()
    registry.register(integration)

    # Verify it's registered
    github_integrations = [
        integration
        for integration in registry.integrations
        if isinstance(integration, GitHubIntegration)
    ]
    assert len(github_integrations) > 0


@patch("quackcore.integrations.github.create_integration")
@patch("quackcore.integrations.core.registry.register")
def test_module_init_registers_integration(mock_register, mock_create):
    """Test that the module's __init__ registers the integration."""
    # Create a mock integration
    mock_integration = MagicMock(spec=GitHubIntegration)
    mock_create.return_value = mock_integration

    # Re-import the module to trigger the registration
    import importlib

    import quackcore.integrations.github

    importlib.reload(quackcore.integrations.github)

    # Check if register was called with the integration
    mock_register.assert_called_once_with(mock_integration)


def test_lazy_loading():
    """Test lazy loading of teaching-related classes."""
    import quackcore.integrations.github

    # Test access to lazy-loaded attributes
    with patch("quackcore.integrations.github.__getattr__") as mock_getattr:
        # Try accessing GitHubGrader
        _ = quackcore.integrations.github.GitHubGrader
        mock_getattr.assert_called_with("GitHubGrader")

        # Try accessing GitHubTeachingAdapter
        mock_getattr.reset_mock()
        _ = quackcore.integrations.github.GitHubTeachingAdapter
        mock_getattr.assert_called_with("GitHubTeachingAdapter")


def test_getattr_unknown_attribute():
    """Test that __getattr__ raises AttributeError for unknown attributes."""
    import quackcore.integrations.github

    with pytest.raises(AttributeError):
        _ = quackcore.integrations.github.NonExistentAttribute
