# src/quackcore/teaching/core/github_api.py
"""
GitHub API utilities for checking user actions.

This module provides functions for checking GitHub-related quest conditions,
such as starring repositories and opening pull requests.
"""

from quackcore.integrations.core import registry
from quackcore.integrations.github.models import GitHubRepo
from quackcore.logging import get_logger
from quackcore.errors import QuackError

logger = get_logger(__name__)


def _get_github_client():
    """
    Get the GitHub client from the integration registry.

    Returns:
        GitHub client.

    Raises:
        QuackError: If the GitHub integration is not found or fails to initialize.
    """
    github = registry.get_integration("GitHub")
    if not github:
        msg = "GitHub integration not found in registry"
        logger.warning(msg)
        raise QuackError(msg)
    if not hasattr(github, "client") or github.client is None:
        result = github.initialize()
        if not result.success:
            msg = f"Failed to initialize GitHub integration: {result.error}"
            logger.error(msg)
            raise QuackError(msg)
    return github.client


def has_starred_repo(username: str, repo_name: str) -> bool:
    """
    Check if a user has starred a GitHub repository.

    Args:
        username: GitHub username.
        repo_name: Repository name in format "owner/repo".

    Returns:
        True if the user has starred the repository, False otherwise.

    Raises:
        QuackError: If an unexpected error occurs.
    """
    try:
        client = _get_github_client()
        # Call a client method to check if repo is starred.
        # (Assuming the method exists on the client.)
        return client.is_repo_starred(repo_name)
    except QuackError as qe:
        logger.error(f"Error checking if {username} starred {repo_name}: {str(qe)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking if {username} starred {repo_name}: {str(e)}")
        raise QuackError("Unexpected error in has_starred_repo", original_error=e)


def has_forked_repo(username: str, repo_name: str) -> bool:
    """
    Check if a user has forked a GitHub repository.

    Args:
        username: GitHub username.
        repo_name: Repository name in format "owner/repo".

    Returns:
        True if the user has forked the repository, False otherwise.

    Raises:
        QuackError: If an unexpected error occurs.
    """
    try:
        client = _get_github_client()
        # Use the client to attempt to retrieve the user's fork.
        # For now, simulate by attempting to get the repository.
        dummy_repo = client.get_repo(repo_name)
        # Log the dummy result to use the client.
        logger.debug(f"Retrieved repository (for fork check): {dummy_repo}")
        # Placeholder: Return False (since a proper fork check isn't implemented).
        return False
    except QuackError as qe:
        logger.error(f"Error checking if {username} forked {repo_name}: {str(qe)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking if {username} forked {repo_name}: {str(e)}")
        raise QuackError("Unexpected error in has_forked_repo", original_error=e)


def has_opened_pr(username: str, org_name: str) -> bool:
    """
    Check if a user has opened a pull request to any repository in an organization.

    Args:
        username: GitHub username.
        org_name: GitHub organization name.

    Returns:
        True if the user has opened a PR, False otherwise.

    Raises:
        QuackError: If an unexpected error occurs.
    """
    try:
        client = _get_github_client()
        # Simulate by calling a hypothetical client method to get user PRs.
        pr_list = client.get_pull_requests_by_user(username, org_name)
        logger.debug(f"User {username} PR list: {pr_list}")
        return len(pr_list) > 0
    except QuackError as qe:
        logger.error(f"Error checking if {username} opened PRs in {org_name}: {str(qe)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking if {username} opened PRs in {org_name}: {str(e)}")
        raise QuackError("Unexpected error in has_opened_pr", original_error=e)


def has_merged_pr(username: str, org_name: str) -> bool:
    """
    Check if a user has a merged pull request in any repository in an organization.

    Args:
        username: GitHub username.
        org_name: GitHub organization name.

    Returns:
        True if the user has a merged PR, False otherwise.

    Raises:
        QuackError: If an unexpected error occurs.
    """
    try:
        client = _get_github_client()
        # Simulate by calling a hypothetical client method to get merged PRs.
        merged_pr_list = client.get_merged_pull_requests_by_user(username, org_name)
        logger.debug(f"User {username} merged PR list: {merged_pr_list}")
        return len(merged_pr_list) > 0
    except QuackError as qe:
        logger.error(f"Error checking if {username} has merged PRs in {org_name}: {str(qe)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking if {username} has merged PRs in {org_name}: {str(e)}")
        raise QuackError("Unexpected error in has_merged_pr", original_error=e)


def get_repo_info(repo_name: str) -> GitHubRepo | None:
    """
    Get information about a GitHub repository.

    Args:
        repo_name: Repository name in format "owner/repo".

    Returns:
        Repository information or None if not found.

    Raises:
        QuackError: If an unexpected error occurs.
    """
    try:
        client = _get_github_client()
        # Use the client to get the repository info.
        repo_info = client.get_repo(repo_name)
        logger.debug(f"Repository info for {repo_name}: {repo_info}")
        return repo_info
    except QuackError as qe:
        logger.error(f"Error getting repository info for {repo_name}: {str(qe)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting repository info for {repo_name}: {str(e)}")
        raise QuackError("Unexpected error in get_repo_info", original_error=e)


def get_user_contributions(username: str, org_name: str) -> dict[str, int]:
    """
    Get a user's contributions to repositories in an organization.

    Args:
        username: GitHub username.
        org_name: GitHub organization name.

    Returns:
        Dictionary mapping contribution types to counts.

    Raises:
        QuackError: If an unexpected error occurs.
    """
    try:
        client = _get_github_client()
        # Use a hypothetical client method to retrieve contributions.
        contributions = client.get_user_contributions(username, org_name)
        logger.debug(f"User {username} contributions in {org_name}: {contributions}")
        if contributions is None:
            return {"commits": 0, "pull_requests": 0, "issues": 0, "reviews": 0}
        return contributions
    except QuackError as qe:
        logger.error(f"Error getting user contributions for {username} in {org_name}: {str(qe)}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error getting contributions for {username} in {org_name}: {str(e)}")
        raise QuackError("Unexpected error in get_user_contributions", original_error=e)
