# tests/quackster/test_github/test_teaching_adapter.py
"""
Tests for the GitHub quackster adapter.

This module tests the GitHub quackster adapter in quackster.github.teaching_adapter.
"""

from unittest.mock import MagicMock, patch

from quackcore.errors import QuackApiError
from quackster.github.teaching_adapter import GitHubTeachingAdapter


class TestGitHubTeachingAdapter:
    """Tests for the GitHub quackster adapter."""

    def test_init(self):
        """Test initialization of the GitHub quackster adapter."""
        # Setup
        mock_client = MagicMock()

        # Act
        adapter = GitHubTeachingAdapter(mock_client)

        # Assert
        assert adapter.client is mock_client
        assert adapter._current_user is None
        assert adapter._username is None

    @patch("quackster.github.teaching_adapter.GamificationService")
    def test_ensure_starred_already_starred(self, mock_gamification_service_class):
        """Test ensure_starred when repo is already starred."""
        # Setup
        mock_client = MagicMock()
        mock_client.is_repo_starred.return_value = True

        mock_gamification_service = MagicMock()
        mock_gamification_service_class.return_value = mock_gamification_service

        mock_result = MagicMock()
        mock_result.message = "Star recorded"
        mock_gamification_service.handle_github_star.return_value = mock_result

        adapter = GitHubTeachingAdapter(mock_client)

        # Act
        result = adapter.ensure_starred("test/repo")

        # Assert
        assert result.success is True
        assert "already starred" in result.message
        assert result.content is True

        mock_client.is_repo_starred.assert_called_once_with("test/repo")
        mock_client.star_repo.assert_not_called()

        # Verify gamification integration
        mock_gamification_service.handle_github_star.assert_called_once_with(
            "test/repo"
        )

    @patch("quackster.github.teaching_adapter.GamificationService")
    def test_ensure_starred_new_star(self, mock_gamification_service_class):
        """Test ensure_starred when repo is not already starred."""
        # Setup
        mock_client = MagicMock()
        mock_client.is_repo_starred.return_value = False

        mock_gamification_service = MagicMock()
        mock_gamification_service_class.return_value = mock_gamification_service

        mock_result = MagicMock()
        mock_result.message = "Star recorded"
        mock_gamification_service.handle_github_star.return_value = mock_result

        adapter = GitHubTeachingAdapter(mock_client)

        # Act
        result = adapter.ensure_starred("test/repo")

        # Assert
        assert result.success is True
        assert "Successfully starred" in result.message
        assert result.content is True

        mock_client.is_repo_starred.assert_called_once_with("test/repo")
        mock_client.star_repo.assert_called_once_with("test/repo")

        # Verify gamification integration
        mock_gamification_service.handle_github_star.assert_called_once_with(
            "test/repo"
        )

    @patch("quackster.github.teaching_adapter.GamificationService")
    def test_ensure_starred_error(self, mock_gamification_service_class):
        """Test ensure_starred when an error occurs."""
        # Setup
        mock_client = MagicMock()
        mock_client.is_repo_starred.side_effect = QuackApiError("API error")

        adapter = GitHubTeachingAdapter(mock_client)

        # Act
        result = adapter.ensure_starred("test/repo")

        # Assert
        assert result.success is False
        assert "Failed to star repository" in result.error
        assert "API error" in result.error

        mock_client.is_repo_starred.assert_called_once_with("test/repo")
        mock_client.star_repo.assert_not_called()

        # Verify gamification service was not called
        mock_gamification_service_class.assert_not_called()

    def test_ensure_forked_already_exists(self):
        """Test ensure_forked when fork already exists."""
        # Setup
        mock_client = MagicMock()
        mock_client.get_user.return_value = MagicMock(username="testuser")
        mock_client.check_repository_exists.return_value = True

        adapter = GitHubTeachingAdapter(mock_client)

        # Act
        result = adapter.ensure_forked("owner/repo")

        # Assert
        assert result.success is True
        assert "already forked" in result.message
        assert result.content == "testuser/repo"

        mock_client.get_user.assert_called_once()
        mock_client.check_repository_exists.assert_called_once_with("testuser/repo")
        mock_client.fork_repo.assert_not_called()

    def test_ensure_forked_new_fork(self):
        """Test ensure_forked when creating a new fork."""
        # Setup
        mock_client = MagicMock()
        mock_client.get_user.return_value = MagicMock(username="testuser")
        mock_client.check_repository_exists.return_value = False

        forked_repo = MagicMock()
        forked_repo.full_name = "testuser/repo"
        mock_client.fork_repo.return_value = forked_repo

        adapter = GitHubTeachingAdapter(mock_client)

        # Act
        result = adapter.ensure_forked("owner/repo")

        # Assert
        assert result.success is True
        assert "Successfully forked" in result.message
        assert result.content == "testuser/repo"

        mock_client.get_user.assert_called_once()
        mock_client.check_repository_exists.assert_called_once_with("testuser/repo")
        mock_client.fork_repo.assert_called_once_with("owner/repo")

    def test_ensure_forked_error(self):
        """Test ensure_forked when an error occurs."""
        # Setup
        mock_client = MagicMock()
        mock_client.get_user.side_effect = QuackApiError("API error")

        adapter = GitHubTeachingAdapter(mock_client)

        # Act
        result = adapter.ensure_forked("owner/repo")

        # Assert
        assert result.success is False
        assert "Failed to fork repository" in result.error
        assert "API error" in result.error

        mock_client.get_user.assert_called_once()
        mock_client.check_repository_exists.assert_not_called()
        mock_client.fork_repo.assert_not_called()

    @patch("quackster.github.teaching_adapter.GamificationService")
    def test_submit_assignment(self, mock_gamification_service_class):
        """Test submit_assignment."""
        # Setup
        mock_client = MagicMock()
        mock_client.get_user.return_value = MagicMock(username="testuser")

        pr = MagicMock()
        pr.number = 42
        pr.url = "https://github.com/base/repo/pull/42"
        mock_client.create_pull_request.return_value = pr

        mock_gamification_service = MagicMock()
        mock_gamification_service_class.return_value = mock_gamification_service

        mock_result = MagicMock()
        mock_result.message = "PR recorded"
        mock_gamification_service.handle_github_pr_submission.return_value = mock_result

        adapter = GitHubTeachingAdapter(mock_client)

        # Act
        result = adapter.submit_assignment(
            "testuser/fork", "base/repo", "feature", "My PR", "Description", "main"
        )

        # Assert
        assert result.success is True
        assert "Successfully submitted" in result.message
        assert result.content == "https://github.com/base/repo/pull/42"

        mock_client.get_user.assert_called_once()
        mock_client.create_pull_request.assert_called_once_with(
            base_repo="base/repo",
            head="testuser:feature",
            title="[SUBMISSION] My PR",
            body="Description",
            base_branch="main",
        )

        # Verify gamification integration
        mock_gamification_service.handle_github_pr_submission.assert_called_once_with(
            42, "base/repo"
        )

    def test_submit_assignment_error(self):
        """Test submit_assignment when an error occurs."""
        # Setup
        mock_client = MagicMock()
        mock_client.get_user.return_value = MagicMock(username="testuser")
        mock_client.create_pull_request.side_effect = QuackApiError("API error")

        adapter = GitHubTeachingAdapter(mock_client)

        # Act
        result = adapter.submit_assignment(
            "testuser/fork", "base/repo", "feature", "My PR", "Description", "main"
        )

        # Assert
        assert result.success is False
        assert "Failed to submit assignment" in result.error
        assert "API error" in result.error

        mock_client.get_user.assert_called_once()
        mock_client.create_pull_request.assert_called_once()

    def test_get_latest_submission_found(self):
        """Test get_latest_submission when submissions are found."""
        # Setup
        mock_client = MagicMock()

        pr1 = MagicMock()
        pr1.created_at = "2025-01-01T12:00:00Z"

        pr2 = MagicMock()
        pr2.created_at = "2025-04-01T12:00:00Z"  # More recent

        mock_client.list_pull_requests.return_value = [pr1, pr2]

        adapter = GitHubTeachingAdapter(mock_client)

        # Act
        result = adapter.get_latest_submission("test/repo", "student")

        # Assert
        assert result.success is True
        assert "Found latest submission" in result.message
        assert result.content is pr2  # Should return the more recent PR

        mock_client.list_pull_requests.assert_called_once_with(
            repo="test/repo", author="student"
        )

    def test_get_latest_submission_not_found(self):
        """Test get_latest_submission when no submissions are found."""
        # Setup
        mock_client = MagicMock()
        mock_client.list_pull_requests.return_value = []

        adapter = GitHubTeachingAdapter(mock_client)

        # Act
        result = adapter.get_latest_submission("test/repo", "student")

        # Assert
        assert result.success is False
        assert "No submissions found" in result.message

        mock_client.list_pull_requests.assert_called_once_with(
            repo="test/repo", author="student"
        )

    def test_get_latest_submission_error(self):
        """Test get_latest_submission when an error occurs."""
        # Setup
        mock_client = MagicMock()
        mock_client.list_pull_requests.side_effect = QuackApiError("API error")

        adapter = GitHubTeachingAdapter(mock_client)

        # Act
        result = adapter.get_latest_submission("test/repo", "student")

        # Assert
        assert result.success is False
        assert "Failed to get latest submission" in result.error
        assert "API error" in result.error

        mock_client.list_pull_requests.assert_called_once_with(
            repo="test/repo", author="student"
        )
