# quackster/src/quackster/github/teaching_adapter.py
"""GitHub quackster adapter for QuackCore."""

from quackcore.errors import QuackApiError
from quackcore.integrations.core import IntegrationResult
from quackcore.integrations.github.client import GitHubClient
from quackcore.integrations.github.models import PullRequest
from quackcore.logging import get_logger
from quackster.core.gamification_service import GamificationService

logger = get_logger(__name__)


class GitHubTeachingAdapter:
    """Adapter for GitHub quackster features."""

    def __init__(self, client: GitHubClient) -> None:
        """Initialize the GitHub quackster adapter.

        Args:
            client: GitHub client
        """
        self.client = client

        # Cache for user information
        self._current_user = None
        self._username = None

    def ensure_starred(self, repo: str) -> IntegrationResult[bool]:
        """Ensure that the user has starred a repository.

        Args:
            repo: Full repository name (owner/repo)

        Returns:
            Result with True if the repo is now starred
        """
        try:
            # Check if the repo is already starred
            already_starred = self.client.is_repo_starred(repo)

            if already_starred:
                # Even if already starred, we might want to award XP if this is the first time we're checking
                try:
                    gamifier = GamificationService()
                    result = gamifier.handle_github_star(repo)
                    if result.message:
                        logger.info(result.message)
                except Exception as e:
                    logger.debug(f"Error integrating star with gamification: {str(e)}")

                return IntegrationResult.success_result(
                    content=True, message=f"Repository {repo} is already starred"
                )

            # Star the repo
            self.client.star_repo(repo)

            # Integrate with gamification system
            try:
                gamifier = GamificationService()
                result = gamifier.handle_github_star(repo)
                if result.message:
                    logger.info(result.message)
            except Exception as e:
                logger.debug(f"Error integrating star with gamification: {str(e)}")

            return IntegrationResult.success_result(
                content=True, message=f"Successfully starred repository {repo}"
            )
        except QuackApiError as e:
            return IntegrationResult.error_result(
                error=f"Failed to star repository: {str(e)}",
                message=f"Could not star {repo}",
            )

    def ensure_forked(self, repo: str) -> IntegrationResult[str]:
        """Ensure that the user has forked a repository.

        Args:
            repo: Full repository name (owner/repo)

        Returns:
            Result with the forked repository full name
        """
        try:
            # Get the current user's username if we don't have it
            if not self._username:
                self._current_user = self.client.get_user()
                self._username = self._current_user.username

            # Check if the user already has a fork
            expected_fork_name = f"{self._username}/{repo.split('/')[-1]}"

            if self.client.check_repository_exists(expected_fork_name):
                logger.info(
                    f"User already has a fork of {repo} at {expected_fork_name}"
                )
                return IntegrationResult.success_result(
                    content=expected_fork_name,
                    message=f"Repository {repo} is already forked to {expected_fork_name}",
                )

            # Create a new fork
            forked_repo = self.client.fork_repo(repo)

            return IntegrationResult.success_result(
                content=forked_repo.full_name,
                message=f"Successfully forked repository {repo} to {forked_repo.full_name}",
            )
        except QuackApiError as e:
            return IntegrationResult.error_result(
                error=f"Failed to fork repository: {str(e)}",
                message=f"Could not fork {repo}",
            )

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
        try:
            # Get the current user's username if we don't have it
            if not self._username:
                self._current_user = self.client.get_user()
                self._username = self._current_user.username

            # Format the head reference for the PR
            head = f"{self._username}:{branch}"

            # Create the pull request
            pr = self.client.create_pull_request(
                base_repo=base_repo,
                head=head,
                title=f"[SUBMISSION] {title}",
                body=body,
                base_branch=base_branch,
            )

            # Convert HttpUrl to string to match the return type
            url_string = str(pr.url)

            # Integrate with gamification system
            try:
                gamifier = GamificationService()
                result = gamifier.handle_github_pr_submission(pr.number, base_repo)
                if result.message:
                    logger.info(result.message)
            except Exception as e:
                logger.debug(f"Error integrating PR with gamification: {str(e)}")

            return IntegrationResult.success_result(
                content=url_string,
                message=f"Successfully submitted assignment via PR #{pr.number}",
            )
        except QuackApiError as e:
            return IntegrationResult.error_result(
                error=f"Failed to submit assignment: {str(e)}",
                message=f"Could not create pull request from {forked_repo}:{branch} to {base_repo}:{base_branch}",
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
        try:
            # List pull requests by the student
            prs = self.client.list_pull_requests(repo=repo, author=student)

            if not prs:
                return IntegrationResult.error_result(
                    error=f"No pull requests found for {student} in {repo}",
                    message=f"No submissions found for {student}",
                )

            # Find the latest submission
            # Sort by creation date, newest first
            latest_pr = sorted(prs, key=lambda pr: pr.created_at, reverse=True)[0]

            return IntegrationResult.success_result(
                content=latest_pr,
                message=f"Found latest submission (PR #{latest_pr.number}) from {student}",
            )
        except QuackApiError as e:
            return IntegrationResult.error_result(
                error=f"Failed to get latest submission: {str(e)}",
                message=f"Could not retrieve submissions for {student} in {repo}",
            )
