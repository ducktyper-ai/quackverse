# src/quackcore/integrations/github/service.py
"""GitHub integration service for QuackCore."""

from typing import Any

from quackcore.integrations.core import (
    AuthProviderProtocol,
    BaseIntegrationService,
    ConfigProviderProtocol,
    IntegrationResult
)
from quackcore.logging import get_logger

from .auth import GitHubAuthProvider
from .client import GitHubClient
from .config import GitHubConfigProvider
from .grading import GitHubGrader
from .models import GitHubRepo, GitHubUser, PullRequest
from .protocols import GitHubTeachingIntegrationProtocol
from .teaching_adapter import GitHubTeachingAdapter

logger = get_logger(__name__)


class GitHubIntegration(BaseIntegrationService, GitHubTeachingIntegrationProtocol):
    """GitHub integration for QuackCore."""

    def __init__(
        self,
        config_provider: ConfigProviderProtocol | None = None,
        auth_provider: AuthProviderProtocol | None = None,
        config_path: str | None = None,
        log_level: int | None = None,
    ) -> None:
        """Initialize the GitHub integration.

        Args:
            config_provider: Configuration provider
            auth_provider: Authentication provider
            config_path: Path to configuration file
            log_level: Logging level
        """
        # Create default providers if not provided
        if config_provider is None:
            config_provider = GitHubConfigProvider(log_level=log_level)

        if auth_provider is None:
            auth_provider = GitHubAuthProvider(log_level=log_level)

        super().__init__(
            config_provider=config_provider,
            auth_provider=auth_provider,
            config_path=config_path,
            log_level=log_level,
        )

        self.client = None
        self.teaching_adapter = None
        self.grader = None

    @property
    def name(self) -> str:
        """Name of the integration."""
        return "GitHub"

    @property
    def version(self) -> str:
        """Version of the integration."""
        return "1.0.0"

    def initialize(self) -> IntegrationResult:
        """Initialize the GitHub integration.

        Returns:
            Result of the initialization
        """
        # First, call the base initialization
        init_result = super().initialize()
        if not init_result.success:
            return init_result

        try:
            # Get configuration
            if not self.config:
                return IntegrationResult.error_result(
                    "GitHub configuration is not available"
                )

            # Get authentication token
            token = self.config.get("token")

            # If token is not in config, try to get it from auth provider
            if not token and self.auth_provider:
                auth_result = self.auth_provider.get_credentials()

                if isinstance(auth_result, dict):
                    token = auth_result.get("token")
                else:
                    token = getattr(auth_result, "token", None)

            if not token:
                # Try to authenticate with auth provider
                if self.auth_provider:
                    auth_result = self.auth_provider.authenticate()
                    if auth_result.success and auth_result.token:
                        token = auth_result.token
                    else:
                        return IntegrationResult.error_result(
                            "Failed to authenticate with GitHub",
                            message=auth_result.error if hasattr(auth_result, "error") else "Authentication failed"
                        )
                else:
                    return IntegrationResult.error_result(
                        "GitHub token is not configured and no auth provider is available"
                    )

            # Initialize GitHub client
            self.client = GitHubClient(
                token=token,
                api_url=self.config.get("api_url", "https://api.github.com"),
                timeout=self.config.get("timeout_seconds", 30),
                max_retries=self.config.get("max_retries", 3),
                retry_delay=self.config.get("retry_delay", 1.0),
            )

            # Initialize teaching adapter
            self.teaching_adapter = GitHubTeachingAdapter(self.client)

            # Initialize grader
            self.grader = GitHubGrader(self.client)

            self._initialized = True
            return IntegrationResult.success_result(
                message="GitHub integration initialized successfully"
            )
        except Exception as e:
            logger.exception("Failed to initialize GitHub integration")
            return IntegrationResult.error_result(
                f"Failed to initialize GitHub integration: {str(e)}"
            )

    def is_available(self) -> bool:
        """Check if the GitHub integration is available.

        Returns:
            True if available, False otherwise
        """
        return self._initialized and self.client is not None

    # User and Repository Methods

    def get_current_user(self) -> IntegrationResult[GitHubUser]:
        """Get the authenticated user.

        Returns:
            Result with GitHubUser
        """
        init_error = self._ensure_initialized()
        if init_error:
            return init_error

        try:
            user = self.client.get_user()
            return IntegrationResult.success_result(
                content=user,
                message=f"Successfully retrieved user {user.username}"
            )
        except Exception as e:
            return IntegrationResult.error_result(
                f"Failed to get user: {str(e)}"
            )

    def get_repo(self, full_name: str) -> IntegrationResult[GitHubRepo]:
        """Get a GitHub repository.

        Args:
            full_name: Full repository name (owner/repo)

        Returns:
            Result with GitHubRepo
        """
        init_error = self._ensure_initialized()
        if init_error:
            return init_error

        try:
            repo = self.client.get_repo(full_name)
            return IntegrationResult.success_result(
                content=repo,
                message=f"Successfully retrieved repository {repo.full_name}"
            )
        except Exception as e:
            return IntegrationResult.error_result(
                f"Failed to get repository: {str(e)}"
            )

    def star_repo(self, full_name: str) -> IntegrationResult[bool]:
        """Star a GitHub repository.

        Args:
            full_name: Full repository name (owner/repo)

        Returns:
            Result with True if successful
        """
        init_error = self._ensure_initialized()
        if init_error:
            return init_error

        try:
            self.client.star_repo(full_name)
            return IntegrationResult.success_result(
                content=True,
                message=f"Successfully starred repository {full_name}"
            )
        except Exception as e:
            return IntegrationResult.error_result(
                f"Failed to star repository: {str(e)}"
            )

    def fork_repo(self, full_name: str) -> IntegrationResult[GitHubRepo]:
        """Fork a GitHub repository.

        Args:
            full_name: Full repository name (owner/repo)

        Returns:
            Result with GitHubRepo for the fork
        """
        init_error = self._ensure_initialized()
        if init_error:
            return init_error

        try:
            fork = self.client.fork_repo(full_name)
            return IntegrationResult.success_result(
                content=fork,
                message=f"Successfully forked repository {full_name} to {fork.full_name}"
            )
        except Exception as e:
            return IntegrationResult.error_result(
                f"Failed to fork repository: {str(e)}"
            )

    # Pull Request Methods

    def create_pull_request(
        self,
        base_repo: str,
        head: str,
        title: str,
        body: str | None = None,
        base_branch: str = "main"
    ) -> IntegrationResult[PullRequest]:
        """Create a pull request.

        Args:
            base_repo: Full name of the base repository (owner/repo)
            head: Head reference in the format "username:branch"
            title: Pull request title
            body: Pull request body
            base_branch: Base branch to merge into

        Returns:
            Result with PullRequest
        """
        init_error = self._ensure_initialized()
        if init_error:
            return init_error

        try:
            pr = self.client.create_pull_request(
                base_repo=base_repo,
                head=head,
                title=title,
                body=body,
                base_branch=base_branch
            )
            return IntegrationResult.success_result(
                content=pr,
                message=f"Successfully created pull request #{pr.number}"
            )
        except Exception as e:
            return IntegrationResult.error_result(
                f"Failed to create pull request: {str(e)}"
            )

    def list_pull_requests(
        self,
        repo: str,
        state: str = "open",
        author: str | None = None
    ) -> IntegrationResult[list[PullRequest]]:
        """List pull requests for a repository.

        Args:
            repo: Full repository name (owner/repo)
            state: Pull request state (open, closed, all)
            author: Filter by author username

        Returns:
            Result with list of PullRequest objects
        """
        init_error = self._ensure_initialized()
        if init_error:
            return init_error

        try:
            prs = self.client.list_pull_requests(
                repo=repo,
                state=state,
                author=author
            )
            return IntegrationResult.success_result(
                content=prs,
                message=f"Successfully retrieved {len(prs)} pull requests for {repo}"
            )
        except Exception as e:
            return IntegrationResult.error_result(
                f"Failed to list pull requests: {str(e)}"
            )

    # Teaching Methods

    def ensure_starred(self, repo: str) -> IntegrationResult[bool]:
        """Ensure that the user has starred a repository.

        Args:
            repo: Full repository name (owner/repo)

        Returns:
            Result with True if the repo is now starred
        """
        init_error = self._ensure_initialized()
        if init_error:
            return init_error

        return self.teaching_adapter.ensure_starred(repo)

    def ensure_forked(self, repo: str) -> IntegrationResult[str]:
        """Ensure that the user has forked a repository.

        Args:
            repo: Full repository name (owner/repo)

        Returns:
            Result with the forked repository full name
        """
        init_error = self._ensure_initialized()
        if init_error:
            return init_error

        return self.teaching_adapter.ensure_forked(repo)

    def submit_assignment(
        self,
        forked_repo: str,
        base_repo: str,
        branch: str,
        title: str,
        body: str | None = None,
        base_branch: str = "main"
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
        init_error = self._ensure_initialized()
        if init_error:
            return init_error

        return self.teaching_adapter.submit_assignment(
            forked_repo=forked_repo,
            base_repo=base_repo,
            branch=branch,
            title=title,
            body=body,
            base_branch=base_branch
        )

    def get_latest_submission(self, repo: str, student: str) -> IntegrationResult[PullRequest]:
        """Get the latest assignment submission for a student.

        Args:
            repo: Full repository name (owner/repo)
            student: Student's GitHub username

        Returns:
            Result with the latest pull request
        """
        init_error = self._ensure_initialized()
        if init_error:
            return init_error

        return self.teaching_adapter.get_latest_submission(repo, student)

    # Grading Methods

    def grade_submission(
        self,
        pull_request: PullRequest,
        grading_criteria: dict[str, Any] | None = None
    ) -> IntegrationResult[Any]:
        """Grade a pull request submission.

        Args:
            pull_request: Pull request to grade
            grading_criteria: Dictionary of grading criteria

        Returns:
            Result with the grading result
        """
        init_error = self._ensure_initialized()
        if init_error:
            return init_error

        return self.grader.grade_submission(pull_request, grading_criteria)

    def grade_submission_by_number(
        self,
        repo: str,
        pr_number: int,
        grading_criteria: dict[str, Any] | None = None
    ) -> IntegrationResult[Any]:
        """Grade a pull request submission by PR number.

        Args:
            repo: Full repository name (owner/repo)
            pr_number: Pull request number
            grading_criteria: Dictionary of grading criteria

        Returns:
            Result with the grading result
        """
        init_error = self._ensure_initialized()
        if init_error:
            return init_error

        try:
            # First get the pull request
            pr = self.client.get_pull_request(repo, pr_number)

            # Then grade it
            return self.grader.grade_submission(pr, grading_criteria)
        except Exception as e:
            return IntegrationResult.error_result(
                f"Failed to grade submission: {str(e)}"
            )