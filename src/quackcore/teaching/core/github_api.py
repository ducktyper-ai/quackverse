# src/quackcore/teaching/core/github_api.py
"""
GitHub API utilities for checking user actions.

This module provides functions for checking GitHub-related quest conditions,
such as starring repositories and opening pull requests.
"""

from quackcore.integrations.core import registry
from quackcore.integrations.github.models import GitHubRepo
from quackcore.logging import get_logger

logger = get_logger(__name__)


def _get_github_client():
    """
    Get the GitHub client from the integration registry.

    Returns:
        GitHub client or None if not available
    """
    github = registry.get_integration("GitHub")
    if not github:
        logger.warning("GitHub integration not found in registry")
        return None

    # Initialize if not already
    if not hasattr(github, "client") or github.client is None:
        result = github.initialize()
        if not result.success:
            logger.error(f"Failed to initialize GitHub integration: {result.error}")
            return None

    return github.client


def has_starred_repo(username: str, repo_name: str) -> bool:
    """
    Check if a user has starred a GitHub repository.

    Args:
        username: GitHub username
        repo_name: Repository name in format "owner/repo"

    Returns:
        True if the user has starred the repository, False otherwise
    """
    client = _get_github_client()
    if not client:
        return False

    try:
        # This would normally call the GitHub API
        return client.is_repo_starred(repo_name)
    except Exception as e:
        logger.error(f"Error checking if {username} starred {repo_name}: {str(e)}")
        return False


def has_forked_repo(username: str, repo_name: str) -> bool:
    """
    Check if a user has forked a GitHub repository.

    Args:
        username: GitHub username
        repo_name: Repository name in format "owner/repo"

    Returns:
        True if the user has forked the repository, False otherwise
    """
    client = _get_github_client()
    if not client:
        return False

    try:
        # This would check if a fork exists
        # For now, just return a placeholder result
        return False
    except Exception as e:
        logger.error(f"Error checking if {username} forked {repo_name}: {str(e)}")
        return False


def has_opened_pr(username: str, org_name: str) -> bool:
    """
    Check if a user has opened a pull request to any repository in an organization.

    Args:
        username: GitHub username
        org_name: GitHub organization name

    Returns:
        True if the user has opened a PR, False otherwise
    """
    client = _get_github_client()
    if not client:
        return False

    try:
        # In a real implementation, this would search for PRs by the user in the org
        # For now, just return a placeholder result
        return False
    except Exception as e:
        logger.error(f"Error checking if {username} opened PRs in {org_name}: {str(e)}")
        return False


def has_merged_pr(username: str, org_name: str) -> bool:
    """
    Check if a user has a merged pull request in any repository in an organization.

    Args:
        username: GitHub username
        org_name: GitHub organization name

    Returns:
        True if the user has a merged PR, False otherwise
    """
    client = _get_github_client()
    if not client:
        return False

    try:
        # In a real implementation, this would search for merged PRs by the user in the org
        # For now, just return a placeholder result
        return False
    except Exception as e:
        logger.error(
            f"Error checking if {username} has merged PRs in {org_name}: {str(e)}"
        )
        return False


def get_repo_info(repo_name: str) -> GitHubRepo | None:
    """
    Get information about a GitHub repository.

    Args:
        repo_name: Repository name in format "owner/repo"

    Returns:
        Repository information or None if not found
    """
    client = _get_github_client()
    if not client:
        return None

    try:
        # Would normally call the GitHub API to get repository information
        # For now, we'll just return None
        return None
    except Exception as e:
        logger.error(f"Error getting repository info for {repo_name}: {str(e)}")
        return None


def get_user_contributions(username: str, org_name: str) -> dict[str, int]:
    """
    Get a user's contributions to repositories in an organization.

    Args:
        username: GitHub username
        org_name: GitHub organization name

    Returns:
        Dictionary mapping contribution types to counts
    """
    client = _get_github_client()
    if not client:
        return {}

    try:
        # In a real implementation, this would analyze the user's contributions
        # For now, just return placeholder data
        return {"commits": 0, "pull_requests": 0, "issues": 0, "reviews": 0}
    except Exception as e:
        logger.error(
            f"Error getting user contributions for {username} in {org_name}: {str(e)}"
        )
        return {}
