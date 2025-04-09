# src/quackcore/integrations/github/__init__.py
"""GitHub integration for QuackCore."""

from quackcore.integrations.core import registry
from quackcore.teaching.github.grading import GitHubGrader
from quackcore.teaching.github.teaching_adapter import GitHubTeachingAdapter

from .auth import GitHubAuthProvider
from .client import GitHubClient
from .config import GitHubConfigProvider
from .models import GitHubRepo, GitHubUser, PullRequest, PullRequestStatus
from .protocols import GitHubIntegrationProtocol
from .service import GitHubIntegration

__all__ = [
    # Main classes
    "GitHubIntegration",
    "GitHubClient",
    "GitHubAuthProvider",
    "GitHubConfigProvider",
    "GitHubTeachingAdapter",
    "GitHubGrader",
    # Protocols
    "GitHubIntegrationProtocol",
    # Models
    "GitHubRepo",
    "GitHubUser",
    "PullRequest",
    "PullRequestStatus",
    # Factory function
    "create_integration",
]


def create_integration() -> GitHubIntegration:
    """Create and return a GitHub integration instance.

    Returns:
        GitHubIntegration instance
    """
    return GitHubIntegration()


# Automatically register the integration
try:
    integration = create_integration()
    registry.register(integration)
except Exception as e:
    # Log error but don't crash on import
    import logging

    logging.getLogger(__name__).error(f"Failed to register GitHub integration: {e}")
