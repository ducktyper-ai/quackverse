# tests/test_integrations/github/test_integration.py
"""Integration tests for GitHub integration."""

import json
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from quackcore.integrations.github import (
    GitHubAuthProvider,
    GitHubConfigProvider,
    GitHubIntegration,
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
    def integration(self, github_token: str, temp_dir: Path) -> GitHubIntegration:
        """Create a real GitHub integration instance with token."""
        credentials_file = temp_dir / "github_creds.json"
        auth_provider = GitHubAuthProvider(credentials_file=str(credentials_file))
        config_provider = GitHubConfigProvider()

        # Create the configuration file using write_text (satisfies SupportsWrite[str])
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
        config_file.write_text(json.dumps(config_data))

        integration = GitHubIntegration(
            auth_provider=auth_provider,
            config_provider=config_provider,
            config_path=str(config_file),
        )

        # Initialize the integration.
        result = integration.initialize()
        if not result.success:
            pytest.skip(f"Failed to initialize GitHub integration: {result.error}")

        return integration

    def test_integration_full_workflow(
        self, integration: GitHubIntegration, github_token: str
    ) -> None:
        """Test a full GitHub workflow."""
        # Test getting authenticated user.
        user_result = integration.get_current_user()
        assert user_result.success is True
        assert user_result.content.username is not None

        # Test getting a public repository.
        repo_result = integration.get_repo("Microsoft/vscode")
        assert repo_result.success is True
        # Compare names in a case-insensitive way
        assert repo_result.content.name.lower() == "vscode"
        assert repo_result.content.full_name.lower() == "microsoft/vscode"


@pytest.mark.integration
class TestGitHubMockedIntegration:
    """Integration tests with mocked API responses."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """Create a mock requests session."""
        session = MagicMock(spec=requests.Session)
        session.headers = {}
        # Configure the session to include a 'request' attribute that is a MagicMock.
        session.configure_mock(request=MagicMock())
        return session

    @pytest.fixture
    def mock_integration(
        self, temp_dir: Path, mock_session: MagicMock
    ) -> tuple[GitHubIntegration, MagicMock]:
        """Create a mock GitHub integration."""
        # Create credentials file.
        credentials_file = temp_dir / "github_creds.json"
        credentials_data = {
            "token": "mock_token",
            "saved_at": int(datetime.now().timestamp()),
            "user_info": {
                "login": "mock_user",
                "name": "Mock User",
                "email": "mock@example.com",
            },
        }
        credentials_file.write_text(json.dumps(credentials_data))

        # Create config file using write_text.
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
        config_file.write_text(json.dumps(config_data))

        # Create auth provider with credentials file and the mock session.
        auth_provider = GitHubAuthProvider(
            credentials_file=str(credentials_file),
            http_client=mock_session,
        )

        # Set up auth provider to mimic a successful authentication.
        auth_provider._user_info = {
            "login": "mock_user",
            "html_url": "https://github.com/mock_user",
            "name": "Mock User",
            "email": "mock@example.com",
            "avatar_url": "https://github.com/mock_user.png",
        }
        auth_provider.token = "mock_token"
        auth_provider.authenticated = True

        # Create integration.
        integration = GitHubIntegration(
            auth_provider=auth_provider,
            config_provider=GitHubConfigProvider(),
            config_path=str(config_file),
        )

        # Patch requests.Session so that the integration uses our mock_session.
        with patch("requests.Session", return_value=mock_session):
            # Prepare a mock response for user info.
            user_response = MagicMock(spec=requests.Response)
            user_response.status_code = 200
            user_response.raise_for_status.return_value = None
            user_response.json.return_value = {
                "login": "mock_user",
                "html_url": "https://github.com/mock_user",
                "name": "Mock User",
                "email": "mock@example.com",
                "avatar_url": "https://github.com/mock_user.png",
            }
            mock_session.get.return_value = user_response
            # Instead of assigning to mock_session.request.return_value directly,
            # we configure the 'request' attribute.
            mock_session.request = MagicMock(return_value=user_response)

            # Initialize the integration.
            result = integration.initialize()
            assert result.success is True

        return integration, mock_session

    def test_integration_mocked_workflow(
        self, mock_integration: tuple[GitHubIntegration, MagicMock]
    ) -> None:
        """Test a GitHub workflow with mocked responses."""
        integration, _ = mock_integration

        # Prepare mocked responses.
        user_response = MagicMock(spec=requests.Response)
        user_response.json.return_value = {
            "login": "mock_user",
            "html_url": "https://github.com/mock_user",
            "name": "Mock User",
            "email": "mock@example.com",
            "avatar_url": "https://github.com/mock_user.png",
        }

        repo_response = MagicMock(spec=requests.Response)
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

        # Patch the integration's client's session.request method.
        with patch.object(integration.client.session, "request") as mock_request:
            # For the first call, return the user response.
            mock_request.return_value = user_response

            # Test getting authenticated user.
            user_result = integration.get_current_user()
            assert user_result.success is True
            assert user_result.content.username == "mock_user"

            # For the second call, return the repo response.
            mock_request.return_value = repo_response

            # Test getting a repository.
            repo_result = integration.get_repo("mock_owner/mock-repo")
            assert repo_result.success is True
            assert repo_result.content.name == "mock-repo"
            assert repo_result.content.full_name == "mock_owner/mock-repo"
