# src/quackster/github/__init__.py
"""Teaching-specific GitHub integration for QuackCore."""

from quackcore.integrations.core import registry
from quackster.github.teaching_service import GitHubTeachingIntegration

__all__ = [
    "GitHubTeachingIntegration",
    "create_teaching_integration",
]


def create_teaching_integration() -> GitHubTeachingIntegration:
    """Create and return a GitHub quackster integration instance.

    Returns:
        GitHubTeachingIntegration instance
    """
    # Get the core GitHub integration
    github = registry.get_integration("GitHub")
    if not github:
        raise ValueError("GitHub integration not found in registry")

    # Create and return the quackster integration
    return GitHubTeachingIntegration(github)
