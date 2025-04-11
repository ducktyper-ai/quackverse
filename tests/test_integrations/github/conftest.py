# tests/test_integrations/github/conftest.py
"""Shared fixtures for GitHub integration tests."""

import json
import os
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from quackcore.integrations.github.auth import GitHubAuthProvider
from quackcore.integrations.github.client import GitHubClient
from quackcore.integrations.github.config import GitHubConfigProvider
from quackcore.integrations.github.models import GitHubRepo, GitHubUser, PullRequest
from quackcore.integrations.github.service import GitHubIntegration


@pytest.fixture
def github_credentials_file(temp_dir) -> Path:
    """Create a temporary GitHub credentials file."""
    creds_file = temp_dir / "github_creds.json"
    creds_data = {
        "token": "test_token",
        "saved_at": 1611111111,
        "user_info": {
            "login": "test_user",
            "name": "Test User",
            "email": "test@example.com",
        },
    }

    creds_file.write_text(json.dumps(creds_data))
    return creds_file


@pytest.fixture
def mock_github_auth_provider() -> GitHubAuthProvider:
    """Create a mock GitHub authentication provider."""
    auth_provider = MagicMock(spec=GitHubAuthProvider)
    auth_provider.name = "GitHub"
    auth_provider.get_credentials.return_value = {"token": "test_token"}
    auth_provider.authenticate.return_value = MagicMock(
        success=True,
        token="test_token",
        message="Successfully authenticated with GitHub",
    )
    return auth_provider


@pytest.fixture
def mock_github_config_provider() -> GitHubConfigProvider:
    """Create a mock GitHub configuration provider."""
    config_provider = MagicMock(spec=GitHubConfigProvider)
    config_provider.name = "GitHub"
    config_provider.get_default_config.return_value = {
        "token": "test_token",
        "api_url": "https://api.github.com",
        "timeout_seconds": 30,
        "max_retries": 3,
        "retry_delay": 1.0,
    }
    config_provider.load_config.return_value = MagicMock(
        success=True,
        content={
            "token": "test_token",
            "api_url": "https://api.github.com",
            "timeout_seconds": 30,
            "max_retries": 3,
            "retry_delay": 1.0,
        },
    )
    return config_provider


@pytest.fixture
def github_auth_provider(github_credentials_file) -> GitHubAuthProvider:
    """Create a real GitHub authentication provider with a mock file."""
    return GitHubAuthProvider(credentials_file=str(github_credentials_file))


@pytest.fixture
def github_config_provider() -> GitHubConfigProvider:
    """Create a real GitHub configuration provider."""
    return GitHubConfigProvider()


@pytest.fixture
def mock_github_client() -> GitHubClient:
    """Create a mock GitHub client."""
    client = MagicMock(spec=GitHubClient)

    # Set up common return values
    user = GitHubUser(
        username="test_user",
        url="https://github.com/test_user",
        name="Test User",
        email="test@example.com",
        avatar_url="https://github.com/test_user.png",
    )

    owner = GitHubUser(
        username="test_owner",
        url="https://github.com/test_owner",
        name="Test Owner",
        avatar_url="https://github.com/test_owner.png",
    )

    repo = GitHubRepo(
        name="test-repo",
        full_name="test_owner/test-repo",
        url="https://github.com/test_owner/test-repo",
        clone_url="https://github.com/test_owner/test-repo.git",
        default_branch="main",
        description="Test repository",
        fork=False,
        forks_count=10,
        stargazers_count=100,
        owner=owner,
    )

    pr = PullRequest(
        number=123,
        title="Test PR",
        url="https://github.com/test_owner/test-repo/pull/123",
        author=user,
        status="open",
        body="Test PR body",
        created_at="2023-01-01T00:00:00Z",
        updated_at="2023-01-01T00:00:00Z",
        base_repo="test_owner/test-repo",
        head_repo="test_user/test-repo",
        base_branch="main",
        head_branch="feature",
    )

    # Set up mock return values
    client.get_user.return_value = user
    client.get_repo.return_value = repo
    client.star_repo.return_value = True
    client.unstar_repo.return_value = True
    client.is_repo_starred.return_value = True
    client.fork_repo.return_value = repo
    client.create_pull_request.return_value = pr
    client.list_pull_requests.return_value = [pr]
    client.get_pull_request.return_value = pr
    client.check_repository_exists.return_value = True
    client.get_repository_file_content.return_value = ("file content", "abc123")
    client.update_repository_file.return_value = True

    return client


@pytest.fixture
def github_service(
    mock_github_auth_provider, mock_github_config_provider
) -> GitHubIntegration:
    """Create a GitHub integration service with mocked dependencies."""
    service = GitHubIntegration(
        auth_provider=mock_github_auth_provider,
        config_provider=mock_github_config_provider,
    )
    service.client = mock_github_client()
    service._initialized = True
    service.config = {
        "token": "test_token",
        "api_url": "https://api.github.com",
        "timeout_seconds": 30,
        "max_retries": 3,
        "retry_delay": 1.0,
    }
    return service


@pytest.fixture
def mock_requests_session() -> requests.Session:
    """Create a mock requests session."""
    session = MagicMock(spec=requests.Session)
    session.headers = {}
    return session


@pytest.fixture
def mock_response() -> requests.Response:
    """Create a mock API response."""
    response = MagicMock(spec=requests.Response)
    response.raise_for_status.return_value = None
    response.status_code = 200
    response.headers = {"X-RateLimit-Remaining": "100"}
    return response


@pytest.fixture
def mock_env_github_token() -> Generator[None, None, None]:
    """Add GitHub token to environment variables temporarily."""
    original_env = os.environ.copy()
    os.environ["GITHUB_TOKEN"] = "env_test_token"
    yield
    os.environ.clear()
    os.environ.update(original_env)
