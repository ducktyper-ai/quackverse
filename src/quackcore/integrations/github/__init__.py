# src/quackcore/integrations/github/__init__.py
"""GitHub integration for QuackCore."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from quackcore.integrations.core import registry

from .auth import GitHubAuthProvider
from .client import GitHubClient
from .config import GitHubConfigProvider
from .models import GitHubRepo, GitHubUser, PullRequest, PullRequestStatus
from .protocols import GitHubIntegrationProtocol
from .service import GitHubIntegration

# For type checkers only, import the teaching-related classes so they appear defined.
if TYPE_CHECKING:
    from quackcore.teaching.github.grading import GitHubGrader
    from quackcore.teaching.github.teaching_adapter import GitHubTeachingAdapter

__all__ = [
    # Main classes
    "GitHubIntegration",
    "GitHubClient",
    "GitHubAuthProvider",
    "GitHubConfigProvider",
    "GitHubTeachingAdapter",  # Provided lazily below
    "GitHubGrader",  # Provided lazily below
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
    logging.getLogger(__name__).error(f"Failed to register GitHub integration: {e}")


# Lazy-load teaching-related attributes to avoid circular imports.
def __getattr__(name: str):
    if name == "GitHubGrader":
        from quackcore.teaching.github.grading import GitHubGrader

        return GitHubGrader
    elif name == "GitHubTeachingAdapter":
        from quackcore.teaching.github.teaching_adapter import GitHubTeachingAdapter

        return GitHubTeachingAdapter
    raise AttributeError(f"module {__name__} has no attribute {name}")
