# tests/test_integrations/github/test_protocols.py
"""Tests for GitHub integration protocols."""

from unittest.mock import MagicMock

import pytest

from quackcore.integrations.core import IntegrationProtocol, IntegrationResult
from quackcore.integrations.github.models import GitHubRepo, GitHubUser, PullRequest
from quackcore.integrations.github.protocols import GitHubIntegrationProtocol
from quackcore.integrations.github.service import GitHubIntegration


class TestGitHubProtocols:
    """Tests for GitHub protocols."""

    def test_github_integration_protocol(self):
        """Test that GitHubIntegration implements the GitHubIntegrationProtocol."""
        # Create a GitHub integration instance
        integration = GitHubIntegration()

        # Check that it implements the protocol
        assert isinstance(integration, GitHubIntegrationProtocol)
        assert isinstance(integration, IntegrationProtocol)

        # Verify protocol methods exist
        assert hasattr(integration, "get_current_user")
        assert hasattr(integration, "get_repo")
        assert hasattr(integration, "star_repo")
        assert hasattr(integration, "fork_repo")
        assert hasattr(integration, "create_pull_request")
        assert hasattr(integration, "list_pull_requests")
        assert hasattr(integration, "get_pull_request")

    def test_github_integration_protocol_method_signatures(self):
        """Test that GitHubIntegration methods have correct return type hints."""
        # Create a GitHub integration instance
        integration = GitHubIntegration()

        # Check method annotations
        assert (
            integration.get_current_user.__annotations__["return"]
            == IntegrationResult[GitHubUser]
        )
        assert (
            integration.get_repo.__annotations__["return"]
            == IntegrationResult[GitHubRepo]
        )
        assert (
            integration.star_repo.__annotations__["return"] == IntegrationResult[bool]
        )
        assert (
            integration.fork_repo.__annotations__["return"]
            == IntegrationResult[GitHubRepo]
        )
        assert (
            integration.create_pull_request.__annotations__["return"]
            == IntegrationResult[PullRequest]
        )
        assert (
            integration.list_pull_requests.__annotations__["return"]
            == IntegrationResult[list[PullRequest]]
        )
        assert (
            integration.get_pull_request.__annotations__["return"]
            == IntegrationResult[PullRequest]
        )

    def test_protocol_runtime_checkable(self):
        """Test that GitHubIntegrationProtocol is runtime checkable."""
        # Create a mock object that implements the protocol methods
        mock_impl = MagicMock(spec=GitHubIntegrationProtocol)

        # It should be considered an instance of the protocol
        assert isinstance(mock_impl, GitHubIntegrationProtocol)

        # Create a mock that doesn't implement all methods
        incomplete_mock = MagicMock()
        incomplete_mock.name = "GitHub"
        incomplete_mock.get_current_user = lambda: None

        # It should not be considered an instance of the protocol
        assert not isinstance(incomplete_mock, GitHubIntegrationProtocol)
