# quackster/src/quackster/github/protocols.py
"""Protocols for GitHub integration."""

from typing import Any, Protocol, runtime_checkable

from quackcore.integrations.core import IntegrationProtocol, IntegrationResult
from quackcore.integrations.github.models import PullRequest


@runtime_checkable
class GitHubTeachingIntegrationProtocol(IntegrationProtocol, Protocol):
    """Protocol for GitHub quackster integration."""

    def ensure_starred(self, repo: str) -> IntegrationResult[bool]:
        """Ensure that the user has starred a repository."""
        ...

    def ensure_forked(self, repo: str) -> IntegrationResult[str]:
        """Ensure that the user has forked a repository."""
        ...

    def submit_assignment(
        self,
        forked_repo: str,
        base_repo: str,
        branch: str,
        title: str,
        body: str | None = None,
        base_branch: str = "main",
    ) -> IntegrationResult[str]:
        """Submit an assignment by creating a pull request."""
        ...

    def get_latest_submission(
        self, repo: str, student: str
    ) -> IntegrationResult[PullRequest]:
        """Get the latest assignment submission for a student."""
        ...

    def grade_submission(
        self, pull_request: PullRequest, grading_criteria: dict[str, Any] | None = None
    ) -> IntegrationResult[Any]:
        """Grade a pull request submission."""
        ...

    def grade_submission_by_number(
        self, repo: str, pr_number: int, grading_criteria: dict[str, Any] | None = None
    ) -> IntegrationResult[Any]:
        """Grade a pull request submission by PR number."""
        ...
