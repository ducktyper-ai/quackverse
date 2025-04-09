# src/quackcore/integrations/github/__init__.py
"""GitHub integration for QuackCore."""

from quackcore.integrations.core import registry

from .auth import GitHubAuthProvider
from .client import GitHubClient
from .config import GitHubConfigProvider
from .grading import GitHubGrader
from .models import (
    GitHubRepo,
    GitHubUser,
    GradeResult,
    PullRequest,
    PullRequestStatus
)
from .protocols import GitHubIntegrationProtocol, GitHubTeachingIntegrationProtocol
from .service import GitHubIntegration
from .teaching_adapter import GitHubTeachingAdapter


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
    "GitHubTeachingIntegrationProtocol",

    # Models
    "GitHubRepo",
    "GitHubUser",
    "PullRequest",
    "PullRequestStatus",
    "GradeResult",

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