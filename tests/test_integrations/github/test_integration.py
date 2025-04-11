# tests/test_integrations/github/test_integration.py
"""Integration tests for GitHub integration."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest
import requests

from quackcore.integrations.github import (
    GitHubAuthProvider,
    GitHubConfigProvider,
    GitHubIntegration,
    create_integration,
)


@pytest.mark.integration
class TestGitHubFullIntegration:
    """Full integration tests for GitHub integration.

    These tests require GITHUB_TOKEN environment variable to be set.
    """

    @pytest.fixture
    def github_token(self) -> str:
        """Get GitHub token from environment variable."""
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            pytest.skip("GITHUB_TOKEN environment variable not set")
        return token

    @pytest.fixture
    def integration(self, github_token, temp_dir) -> GitHubIntegration:
        """Create a real GitHub integration instance with token."""
        credentials_file = temp_dir / "github_creds.json"
        auth_provider = GitHubAuthProvider(credentials_file=str(credentials_file))
        config_provider = GitHubConfigProvider()

        # Create config file
        config_file = temp_dir / "github_config.json"
        config_data = {
            "github": {
                "token": github_token,
                "api_url": "https://api.github.com",
                "timeout_seconds": 30,
                "max_retries": 3,
                "retry_delay": 1.0,
            }
        }
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        integration = GitHubIntegration(
            auth_provider=auth_provider,
            config_provider=config_provider,
            config_path=str(config_file),
        )

        # Initialize the integration
        result = integration.initialize()
        if not result.success:
            pytest.skip(f"Failed to initialize GitHub integration: {result.error}")

        return integration

    def test_integration_full_workflow(self, integration, github_token):
        """Test a full GitHub workflow."""
        # Test getting authenticated user
        user_result = integration.get_current_user()
        assert user_result.success is True
        assert user_result.content.username is not None

        # Test getting a public repository
        repo_result = integration.get_repo("Microsoft/vscode")
        assert repo_result.success is True
        assert repo_result.content.name == "vscode"
        assert repo_result.content.full_name == "microsoft/vscode"


@pytest.mark.integration
class TestGitHubMockedIntegration:
    """Integration tests with mocked API responses."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock requests session."""
        session = MagicMock(spec=requests.Session)
        session.headers = {}
        return session

    @pytest.fixture
    def mock_integration(self, temp_dir, mock_session):
        """Create a mock GitHub integration."""
        # Create credentials file
        credentials_file = temp_dir / "github_creds.json"

        # Create config file
        config_file = temp_dir / "github_config.json"
        config_data = {
            "github": {
                "token": "mock_token",
                "api_url": "https://api.github.com",
                "timeout_seconds": 30,
                "max_retries": 3,
                "retry_delay": 1.0,
            }
        }
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Create integration
        integration = GitHubIntegration(
            auth_provider=GitHubAuthProvider(credentials_file=str(credentials_file)),
            config_provider=GitHubConfigProvider(),
            config_path=str(config_file),
        )

        # Mock API session
        with patch("requests.Session", return_value=mock_session):
            # Mock successful user response
            user_response = MagicMock()
            user_response.json.return_value = {
                "login": "mock_user",
                "html_url": "https://github.com/mock_user",
                "name": "Mock User",
                "email": "mock@example.com",
                "avatar_url": "https://github.com/mock_user.png",
            }

            mock_session.get.return_value = user_response

            # Initialize the integration
            result = integration.initialize()
            assert result.success is True

        return integration, mock_session

    def test_integration_mocked_workflow(self, mock_integration):
        """Test a GitHub workflow with mocked responses."""
        integration, mock_session = mock_integration

        # Mock user response
        user_response = MagicMock()
        user_response.json.return_value = {
            "login": "mock_user",
            "html_url": "https://github.com/mock_user",
            "name": "Mock User",
            "email": "mock@example.com",
            "avatar_url": "https://github.com/mock_user.png",
        }

        # Mock repo response
        repo_response = MagicMock()
        repo_response.json.return_value = {
            "name": "mock-repo",
            "full_name": "mock_owner/mock-repo",
            "html_url": "https://github.com/mock_owner/mock-repo",
            "clone_url": "https://github.com/mock_owner/mock-repo.git",
            "default_branch": "main",
            "description": "Mock repository",
            "fork": False,
            "forks_count": 10,
            "stargazers_count": 100,
            "owner": {
                "login": "mock_owner",
                "html_url": "https://github.com/mock_owner",
                "avatar_url": "https://github.com/mock_owner.png",
            },
        }

        # Set up responses
        with patch.object(integration.client.session, "request") as mock_request:
            # First call for user info
            mock_request.return_value = user_response

            # Test getting authenticated user
            user_result = integration.get_current_user()
            assert user_result.success is True
            assert user_result.content.username == "mock_user"

            # Second call for repo info
            mock_request.return_value = repo_response

            # Test getting a repository
            repo_result = integration.get_repo("mock_owner/mock-repo")
            assert repo_result.success is True
            assert repo_result.content.name == "mock-repo"
            assert repo_result.content.full_name == "mock_owner/mock-repo"
