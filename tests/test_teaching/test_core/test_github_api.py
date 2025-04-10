"""
Tests for the teaching GitHub API integration.

This module tests the GitHub API utility functions in quackcore.teaching.core.github_api.
"""
from unittest.mock import MagicMock, patch

import pytest

from quackcore.teaching.core import github_api


class TestGitHubAPI:
    """Tests for GitHub API integration functions."""

    @patch("quackcore.teaching.core.github_api.registry")
    @patch("quackcore.teaching.core.github_api.logger")
    def test_get_github_client_success(self, mock_logger, mock_registry):
        """Test successfully getting a GitHub client."""
        # Setup
        mock_github = MagicMock()
        mock_github.client = MagicMock()
        mock_registry.get_integration.return_value = mock_github

        # Act
        client = github_api._get_github_client()

        # Assert
        mock_registry.get_integration.assert_called_with("GitHub")
        assert client == mock_github.client

    @patch("quackcore.teaching.core.github_api.registry")
    @patch("quackcore.teaching.core.github_api.logger")
    def test_get_github_client_not_found(self, mock_logger, mock_registry):
        """Test handling when GitHub integration is not found."""
        # Setup
        mock_registry.get_integration.return_value = None

        # Act
        client = github_api._get_github_client()

        # Assert
        mock_registry.get_integration.assert_called_with("GitHub")
        mock_logger.warning.assert_called_with(
            "GitHub integration not found in registry")
        assert client is None

    @patch("quackcore.teaching.core.github_api.registry")
    @patch("quackcore.teaching.core.github_api.logger")
    def test_get_github_client_initialize(self, mock_logger, mock_registry):
        """Test initializing a GitHub client."""
        # Setup
        mock_github = MagicMock()
        mock_github.client = None
        mock_github.initialize.return_value = MagicMock(success=True)
        mock_registry.get_integration.return_value = mock_github

        # Act
        client = github_api._get_github_client()

        # Assert
        mock_registry.get_integration.assert_called_with("GitHub")
        mock_github.initialize.assert_called_once()
        assert client == mock_github.client

    @patch("quackcore.teaching.core.github_api.registry")
    @patch("quackcore.teaching.core.github_api.logger")
    def test_get_github_client_initialize_error(self, mock_logger, mock_registry):
        """Test handling initialization errors."""
        # Setup
        mock_github = MagicMock()
        mock_github.client = None
        mock_github.initialize.return_value = MagicMock(success=False,
                                                        error="Init error")
        mock_registry.get_integration.return_value = mock_github

        # Act
        client = github_api._get_github_client()

        # Assert
        mock_github.initialize.assert_called_once()
        mock_logger.error.assert_called()
        assert client is None

    @patch("quackcore.teaching.core.github_api._get_github_client")
    @patch("quackcore.teaching.core.github_api.logger")
    def test_has_starred_repo_success(self, mock_logger, mock_get_client):
        """Test checking if a user has starred a repository."""
        # Setup
        mock_client = MagicMock()
        mock_client.is_repo_starred.return_value = True
        mock_get_client.return_value = mock_client

        username = "testuser"
        repo_name = "org/repo"

        # Act
        result = github_api.has_starred_repo(username, repo_name)

        # Assert
        mock_get_client.assert_called_once()
        mock_client.is_repo_starred.assert_called_with(repo_name)
        assert result is True

    @patch("quackcore.teaching.core.github_api._get_github_client")
    @patch("quackcore.teaching.core.github_api.logger")
    def test_has_starred_repo_no_client(self, mock_logger, mock_get_client):
        """Test handling when GitHub client is not available."""
        # Setup
        mock_get_client.return_value = None

        username = "testuser"
        repo_name = "org/repo"

        # Act
        result = github_api.has_starred_repo(username, repo_name)

        # Assert
        mock_get_client.assert_called_once()
        assert result is False

    @patch("quackcore.teaching.core.github_api._get_github_client")
    @patch("quackcore.teaching.core.github_api.logger")
    def test_has_starred_repo_error(self, mock_logger, mock_get_client):
        """Test handling errors when checking starred status."""
        # Setup
        mock_client = MagicMock()
        mock_client.is_repo_starred.side_effect = Exception("API error")
        mock_get_client.return_value = mock_client

        username = "testuser"
        repo_name = "org/repo"

        # Act
        result = github_api.has_starred_repo(username, repo_name)

        # Assert
        mock_client.is_repo_starred.assert_called_with(repo_name)
        mock_logger.error.assert_called()
        assert result is False

    @patch("quackcore.teaching.core.github_api._get_github_client")
    @patch("quackcore.teaching.core.github_api.logger")
    def test_has_forked_repo(self, mock_logger, mock_get_client):
        """Test checking if a user has forked a repository."""
        # Setup
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        username = "testuser"
        repo_name = "org/repo"

        # Act
        result = github_api.has_forked_repo(username, repo_name)

        # Assert
        mock_get_client.assert_called_once()
        # This implementation is a placeholder that returns False
        assert result is False

    @patch("quackcore.teaching.core.github_api._get_github_client")
    @patch("quackcore.teaching.core.github_api.logger")
    def test_has_opened_pr(self, mock_logger, mock_get_client):
        """Test checking if a user has opened a pull request."""
        # Setup
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        username = "testuser"
        org_name = "testorg"

        # Act
        result = github_api.has_opened_pr(username, org_name)

        # Assert
        mock_get_client.assert_called_once()
        # This implementation is a placeholder that returns False
        assert result is False

    @patch("quackcore.teaching.core.github_api._get_github_client")
    @patch("quackcore.teaching.core.github_api.logger")
    def test_has_merged_pr(self, mock_logger, mock_get_client):
        """Test checking if a user has a merged pull request."""
        # Setup
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        username = "testuser"
        org_name = "testorg"

        # Act
        result = github_api.has_merged_pr(username, org_name)

        # Assert
        mock_get_client.assert_called_once()
        # This implementation is a placeholder that returns False
        assert result is False

    @patch("quackcore.teaching.core.github_api._get_github_client")
    @patch("quackcore.teaching.core.github_api.logger")
    def test_get_repo_info(self, mock_logger, mock_get_client):
        """Test getting information about a repository."""
        # Setup
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        repo_name = "org/repo"

        # Act
        result = github_api.get_repo_info(repo_name)

        # Assert
        mock_get_client.assert_called_once()
        # This implementation is a placeholder that returns None
        assert result is None

    @patch("quackcore.teaching.core.github_api._get_github_client")
    @patch("quackcore.teaching.core.github_api.logger")
    def test_get_user_contributions(self, mock_logger, mock_get_client):
        """Test getting a user's contributions to repositories."""
        # Setup
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        username = "testuser"
        org_name = "testorg"

        # Act
        result = github_api.get_user_contributions(username, org_name)

        # Assert
        mock_get_client.assert_called_once()
        # This implementation is a placeholder that returns a dictionary
        assert isinstance(result, dict)
        assert "commits" in result
        assert "pull_requests" in result
        assert "issues" in result
        assert "reviews" in result