# tests/test_teaching/test_github/test_teaching_service.py
"""
Tests for the GitHub teaching integration service.

This module tests the GitHub teaching integration service in quackcore.teaching.github.teaching_service.
"""

from unittest.mock import MagicMock, patch

from quackcore.teaching.github.teaching_service import GitHubTeachingIntegration


class TestGitHubTeachingIntegration:
    """Tests for the GitHub teaching integration."""

    def test_init(self):
        """Test initialization of the GitHub teaching integration."""
        # Setup
        mock_github = MagicMock()
        mock_github.client = MagicMock()

        # Act
        integration = GitHubTeachingIntegration(mock_github)

        # Assert
        assert integration.github is mock_github
        assert hasattr(integration, "teaching_adapter")
        assert hasattr(integration, "grader")

    def test_name_and_version(self):
        """Test name and version properties."""
        # Setup
        mock_github = MagicMock()
        integration = GitHubTeachingIntegration(mock_github)

        # Act & Assert
        assert integration.name == "GitHubTeaching"
        assert integration.version == "1.0.0"

    def test_initialize_success(self):
        """Test successful initialization."""
        # Setup
        mock_github = MagicMock()
        mock_github.is_available.return_value = True
        integration = GitHubTeachingIntegration(mock_github)

        # Act
        result = integration.initialize()

        # Assert
        assert result.success is True
        assert "initialized successfully" in result.message
        mock_github.is_available.assert_called_once()

    def test_initialize_failure(self):
        """Test initialization failure when GitHub integration is not available."""
        # Setup
        mock_github = MagicMock()
        mock_github.is_available.return_value = False
        integration = GitHubTeachingIntegration(mock_github)

        # Act
        result = integration.initialize()

        # Assert
        assert result.success is False
        assert "GitHub integration is not initialized" in result.error
        mock_github.is_available.assert_called_once()

    def test_is_available(self):
        """Test is_available method."""
        # Setup
        mock_github = MagicMock()
        mock_github.is_available.return_value = True
        integration = GitHubTeachingIntegration(mock_github)

        # Act
        result = integration.is_available()

        # Assert
        assert result is True
        mock_github.is_available.assert_called_once()

    def test_ensure_starred_github_not_available(self):
        """Test ensure_starred when GitHub integration is not available."""
        # Setup
        mock_github = MagicMock()
        mock_github.is_available.return_value = False
        integration = GitHubTeachingIntegration(mock_github)

        # Act
        result = integration.ensure_starred("test/repo")

        # Assert
        assert result.success is False
        assert "GitHub integration is not initialized" in result.error

    def test_ensure_forked_github_not_available(self):
        """Test ensure_forked when GitHub integration is not available."""
        # Setup
        mock_github = MagicMock()
        mock_github.is_available.return_value = False
        integration = GitHubTeachingIntegration(mock_github)

        # Act
        result = integration.ensure_forked("test/repo")

        # Assert
        assert result.success is False
        assert "GitHub integration is not initialized" in result.error

    def test_submit_assignment_github_not_available(self):
        """Test submit_assignment when GitHub integration is not available."""
        # Setup
        mock_github = MagicMock()
        mock_github.is_available.return_value = False
        integration = GitHubTeachingIntegration(mock_github)

        # Act
        result = integration.submit_assignment(
            "user/fork", "owner/base", "branch", "title"
        )

        # Assert
        assert result.success is False
        assert "GitHub integration is not initialized" in result.error

    def test_get_latest_submission_github_not_available(self):
        """Test get_latest_submission when GitHub integration is not available."""
        # Setup
        mock_github = MagicMock()
        mock_github.is_available.return_value = False
        integration = GitHubTeachingIntegration(mock_github)

        # Act
        result = integration.get_latest_submission("repo", "student")

        # Assert
        assert result.success is False
        assert "GitHub integration is not initialized" in result.error

    def test_grade_submission_github_not_available(self):
        """Test grade_submission when GitHub integration is not available."""
        # Setup
        mock_github = MagicMock()
        mock_github.is_available.return_value = False
        integration = GitHubTeachingIntegration(mock_github)
        mock_pr = MagicMock()

        # Act
        result = integration.grade_submission(mock_pr)

        # Assert
        assert result.success is False
        assert "GitHub integration is not initialized" in result.error

    def test_grade_submission_by_number_github_not_available(self):
        """Test grade_submission_by_number when GitHub integration is not available."""
        # Setup
        mock_github = MagicMock()
        mock_github.is_available.return_value = False
        integration = GitHubTeachingIntegration(mock_github)

        # Act
        result = integration.grade_submission_by_number("repo", 42)

        # Assert
        assert result.success is False
        assert "GitHub integration is not initialized" in result.error

    @patch("quackcore.teaching.github.teaching_service.GitHubTeachingAdapter")
    def test_ensure_starred_success(self, mock_adapter_class):
        """Test successful ensure_starred method."""
        # Setup
        mock_github = MagicMock()
        mock_github.is_available.return_value = True

        mock_adapter = MagicMock()
        mock_adapter_class.return_value = mock_adapter

        expected_result = MagicMock()
        expected_result.success = True
        expected_result.content = True
        mock_adapter.ensure_starred.return_value = expected_result

        integration = GitHubTeachingIntegration(mock_github)

        # Act
        result = integration.ensure_starred("test/repo")

        # Assert
        assert result is expected_result
        mock_adapter.ensure_starred.assert_called_once_with("test/repo")

    @patch("quackcore.teaching.github.teaching_service.GitHubTeachingAdapter")
    def test_ensure_forked_success(self, mock_adapter_class):
        """Test successful ensure_forked method."""
        # Setup
        mock_github = MagicMock()
        mock_github.is_available.return_value = True

        mock_adapter = MagicMock()
        mock_adapter_class.return_value = mock_adapter

        expected_result = MagicMock()
        expected_result.success = True
        expected_result.content = "user/forked-repo"
        mock_adapter.ensure_forked.return_value = expected_result

        integration = GitHubTeachingIntegration(mock_github)

        # Act
        result = integration.ensure_forked("test/repo")

        # Assert
        assert result is expected_result
        mock_adapter.ensure_forked.assert_called_once_with("test/repo")

    @patch("quackcore.teaching.github.teaching_service.GitHubTeachingAdapter")
    def test_submit_assignment_success(self, mock_adapter_class):
        """Test successful submit_assignment method."""
        # Setup
        mock_github = MagicMock()
        mock_github.is_available.return_value = True

        mock_adapter = MagicMock()
        mock_adapter_class.return_value = mock_adapter

        expected_result = MagicMock()
        expected_result.success = True
        expected_result.content = "https://github.com/test/repo/pull/42"
        mock_adapter.submit_assignment.return_value = expected_result

        integration = GitHubTeachingIntegration(mock_github)

        # Act
        result = integration.submit_assignment(
            "user/fork", "owner/base", "branch", "title", "body", "main"
        )

        # Assert
        assert result is expected_result
        mock_adapter.submit_assignment.assert_called_once_with(
            forked_repo="user/fork",
            base_repo="owner/base",
            branch="branch",
            title="title",
            body="body",
            base_branch="main",
        )

    @patch("quackcore.teaching.github.teaching_service.GitHubTeachingAdapter")
    def test_get_latest_submission_success(self, mock_adapter_class):
        """Test successful get_latest_submission method."""
        # Setup
        mock_github = MagicMock()
        mock_github.is_available.return_value = True

        mock_adapter = MagicMock()
        mock_adapter_class.return_value = mock_adapter

        expected_result = MagicMock()
        expected_result.success = True
        expected_result.content = MagicMock()  # A PullRequest object
        mock_adapter.get_latest_submission.return_value = expected_result

        integration = GitHubTeachingIntegration(mock_github)

        # Act
        result = integration.get_latest_submission("test/repo", "student")

        # Assert
        assert result is expected_result
        mock_adapter.get_latest_submission.assert_called_once_with(
            "test/repo", "student"
        )

    @patch("quackcore.teaching.github.teaching_service.GitHubGrader")
    def test_grade_submission_success(self, mock_grader_class):
        """Test successful grade_submission method."""
        # Setup
        mock_github = MagicMock()
        mock_github.is_available.return_value = True

        mock_grader = MagicMock()
        mock_grader_class.return_value = mock_grader

        expected_result = MagicMock()
        expected_result.success = True
        expected_result.content = MagicMock()  # Grade result object
        mock_grader.grade_submission.return_value = expected_result

        integration = GitHubTeachingIntegration(mock_github)

        mock_pr = MagicMock()
        grading_criteria = {"criteria": "value"}

        # Act
        result = integration.grade_submission(mock_pr, grading_criteria)

        # Assert
        assert result is expected_result
        mock_grader.grade_submission.assert_called_once_with(mock_pr, grading_criteria)

    @patch("quackcore.teaching.github.teaching_service.GitHubGrader")
    def test_grade_submission_by_number_success(self, mock_grader_class):
        """Test successful grade_submission_by_number method."""
        # Setup
        mock_github = MagicMock()
        mock_github.is_available.return_value = True

        mock_pr_result = MagicMock()
        mock_pr_result.success = True
        mock_pr_result.content = MagicMock()  # PR object
        mock_github.get_pull_request.return_value = mock_pr_result

        mock_grader = MagicMock()
        mock_grader_class.return_value = mock_grader

        expected_result = MagicMock()
        expected_result.success = True
        expected_result.content = MagicMock()  # Grade result object
        mock_grader.grade_submission.return_value = expected_result

        integration = GitHubTeachingIntegration(mock_github)

        # Act
        result = integration.grade_submission_by_number("test/repo", 42)

        # Assert
        assert result is expected_result
        mock_github.get_pull_request.assert_called_once_with("test/repo", 42)
        mock_grader.grade_submission.assert_called_once_with(
            mock_pr_result.content, None
        )

    @patch("quackcore.teaching.github.teaching_service.GitHubGrader")
    def test_grade_submission_by_number_pr_not_found(self, mock_grader_class):
        """Test grade_submission_by_number when PR is not found."""
        # Setup
        mock_github = MagicMock()
        mock_github.is_available.return_value = True

        mock_pr_result = MagicMock()
        mock_pr_result.success = False
        mock_pr_result.error = "PR not found"
        mock_github.get_pull_request.return_value = mock_pr_result

        integration = GitHubTeachingIntegration(mock_github)

        # Act
        result = integration.grade_submission_by_number("test/repo", 42)

        # Assert
        assert result is mock_pr_result
        mock_github.get_pull_request.assert_called_once_with("test/repo", 42)

    @patch("quackcore.teaching.github.teaching_service.GitHubGrader")
    def test_grade_submission_by_number_exception(self, mock_grader_class):
        """Test grade_submission_by_number when an exception occurs."""
        # Setup
        mock_github = MagicMock()
        mock_github.is_available.return_value = True
        mock_github.get_pull_request.side_effect = Exception("Test error")

        integration = GitHubTeachingIntegration(mock_github)

        # Act
        result = integration.grade_submission_by_number("test/repo", 42)

        # Assert
        assert result.success is False
        assert "Failed to grade submission" in result.error
        assert "Test error" in result.error
        mock_github.get_pull_request.assert_called_once_with("test/repo", 42)
