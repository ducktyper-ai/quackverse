# quackster/src/quackster/github/teaching_service.py
"""GitHub quackster integration service for QuackCore."""

from typing import Any

from quackcore.integrations.core import IntegrationResult
from quackcore.integrations.github import GitHubIntegration
from quackcore.integrations.github.models import PullRequest
from quackcore.logging import get_logger
from quackster.github.grading import GitHubGrader
from quackster.github.protocols import GitHubTeachingIntegrationProtocol
from quackster.github.teaching_adapter import GitHubTeachingAdapter

logger = get_logger(__name__)


class GitHubTeachingIntegration(GitHubTeachingIntegrationProtocol):
    """GitHub quackster integration for educational workflows."""

    def __init__(self, github_integration: GitHubIntegration) -> None:
        """Initialize the GitHub quackster integration.

        Args:
            github_integration: Core GitHub integration
        """
        self.github = github_integration
        self.teaching_adapter = GitHubTeachingAdapter(github_integration.client)
        self.grader = GitHubGrader(github_integration.client)

    @property
    def name(self) -> str:
        """Name of the integration."""
        return "GitHubTeaching"

    @property
    def version(self) -> str:
        """Version of the integration."""
        return "1.0.0"

    def initialize(self) -> IntegrationResult:
        """Initialize the GitHub quackster integration.

        Returns:
            Result of the initialization
        """
        # Make sure the core GitHub integration is initialized
        if not self.github.is_available():
            return IntegrationResult.error_result(
                "GitHub integration is not initialized"
            )

        return IntegrationResult.success_result(
            message="GitHub quackster integration initialized successfully"
        )

    def is_available(self) -> bool:
        """Check if the GitHub quackster integration is available.

        Returns:
            True if available, False otherwise
        """
        return self.github.is_available()

    # Teaching Methods

    def ensure_starred(self, repo: str) -> IntegrationResult[bool]:
        """Ensure that the user has starred a repository.

        Args:
            repo: Full repository name (owner/repo)

        Returns:
            Result with True if the repo is now starred
        """
        if not self.github.is_available():
            return IntegrationResult.error_result(
                "GitHub integration is not initialized"
            )

        return self.teaching_adapter.ensure_starred(repo)

    def ensure_forked(self, repo: str) -> IntegrationResult[str]:
        """Ensure that the user has forked a repository.

        Args:
            repo: Full repository name (owner/repo)

        Returns:
            Result with the forked repository full name
        """
        if not self.github.is_available():
            return IntegrationResult.error_result(
                "GitHub integration is not initialized"
            )

        return self.teaching_adapter.ensure_forked(repo)

    def submit_assignment(
        self,
        forked_repo: str,
        base_repo: str,
        branch: str,
        title: str,
        body: str | None = None,
        base_branch: str = "main",
    ) -> IntegrationResult[str]:
        """Submit an assignment by creating a pull request.

        Args:
            forked_repo: Full name of the forked repository (username/repo)
            base_repo: Full name of the base repository (owner/repo)
            branch: Branch in the forked repo containing the changes
            title: Pull request title
            body: Pull request body
            base_branch: Base branch to merge into

        Returns:
            Result with the pull request URL
        """
        if not self.github.is_available():
            return IntegrationResult.error_result(
                "GitHub integration is not initialized"
            )

        return self.teaching_adapter.submit_assignment(
            forked_repo=forked_repo,
            base_repo=base_repo,
            branch=branch,
            title=title,
            body=body,
            base_branch=base_branch,
        )

    def get_latest_submission(
        self, repo: str, student: str
    ) -> IntegrationResult[PullRequest]:
        """Get the latest assignment submission for a student.

        Args:
            repo: Full repository name (owner/repo)
            student: Student's GitHub username

        Returns:
            Result with the latest pull request
        """
        if not self.github.is_available():
            return IntegrationResult.error_result(
                "GitHub integration is not initialized"
            )

        return self.teaching_adapter.get_latest_submission(repo, student)

    # Grading Methods

    def grade_submission(
        self, pull_request: PullRequest, grading_criteria: dict[str, Any] | None = None
    ) -> IntegrationResult[Any]:
        """Grade a pull request submission.

        Args:
            pull_request: Pull request to grade
            grading_criteria: Dictionary of grading criteria

        Returns:
            Result with the grading result
        """
        if not self.github.is_available():
            return IntegrationResult.error_result(
                "GitHub integration is not initialized"
            )

        return self.grader.grade_submission(pull_request, grading_criteria)

    def grade_submission_by_number(
        self, repo: str, pr_number: int, grading_criteria: dict[str, Any] | None = None
    ) -> IntegrationResult[Any]:
        """Grade a pull request submission by PR number.

        Args:
            repo: Full repository name (owner/repo)
            pr_number: Pull request number
            grading_criteria: Dictionary of grading criteria

        Returns:
            Result with the grading result
        """
        if not self.github.is_available():
            return IntegrationResult.error_result(
                "GitHub integration is not initialized"
            )

        try:
            # First get the pull request
            pr_result = self.github.get_pull_request(repo, pr_number)
            if not pr_result.success:
                return pr_result

            # Then grade it
            return self.grader.grade_submission(pr_result.content, grading_criteria)
        except Exception as e:
            return IntegrationResult.error_result(
                f"Failed to grade submission: {str(e)}"
            )
