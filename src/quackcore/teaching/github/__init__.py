# src/quackcore/teaching/github/__init__.py
"""Teaching-specific GitHub integration for QuackCore."""

from quackcore.integrations.core import registry

from .teaching_service import GitHubTeachingIntegration

__all__ = [
    "GitHubTeachingIntegration",
    "create_teaching_integration",
]


def create_teaching_integration() -> GitHubTeachingIntegration:
    """Create and return a GitHub teaching integration instance.

    Returns:
        GitHubTeachingIntegration instance
    """
    # Get the core GitHub integration
    github = registry.get_integration("GitHub")
    if not github:
        raise ValueError("GitHub integration not found in registry")

    # Create and return the teaching integration
    return GitHubTeachingIntegration(github)
