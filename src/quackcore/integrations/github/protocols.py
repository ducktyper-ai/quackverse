# src/quackcore/integrations/github/protocols.py
"""Protocols for GitHub integration."""

from typing import Any, Protocol, runtime_checkable

from quackcore.integrations.core import IntegrationProtocol, IntegrationResult

from .models import GitHubRepo, GitHubUser, PullRequest


@runtime_checkable
class GitHubIntegrationProtocol(IntegrationProtocol, Protocol):
    """Protocol for GitHub integration."""

    def get_current_user(self) -> IntegrationResult[GitHubUser]:
        """Get the authenticated user."""
        ...

    def get_repo(self, full_name: str) -> IntegrationResult[GitHubRepo]:
        """Get a GitHub repository."""
        ...

    def star_repo(self, full_name: str) -> IntegrationResult[bool]:
        """Star a GitHub repository."""
        ...

    def fork_repo(self, full_name: str) -> IntegrationResult[GitHubRepo]:
        """Fork a GitHub repository."""
        ...


@runtime_checkable
class GitHubTeachingIntegrationProtocol(GitHubIntegrationProtocol, Protocol):
    """Protocol for GitHub teaching integration."""

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
        base_branch: str = "main"
    ) -> IntegrationResult[str]:
        """Submit an assignment by creating a pull request."""
        ...

    def get_latest_submission(self, repo: str, student: str) -> IntegrationResult[PullRequest]:
        """Get the latest assignment submission for a student."""
        ...

    def grade_submission(
        self,
        pull_request: PullRequest,
        grading_criteria: dict[str, Any] | None = None
    ) -> IntegrationResult[Any]:
        """Grade a pull request submission."""
        ...