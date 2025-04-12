# src/quackcore/integrations/github/__init__.py
"""GitHub integration for QuackCore."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

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


def __getattr__(name: str) -> Any:
    """Lazily load teaching-related classes to avoid circular imports.

    Args:
        name: Attribute name to load

    Returns:
        The requested module or class

    Raises:
        AttributeError: If the requested attribute doesn't exist
    """
    if name == "GitHubGrader":
        from quackcore.teaching.github.grading import GitHubGrader

        return GitHubGrader
    elif name == "GitHubTeachingAdapter":
        from quackcore.teaching.github.teaching_adapter import GitHubTeachingAdapter

        return GitHubTeachingAdapter
    else:
        raise AttributeError(
            f"module 'quackcore.integrations.github' has no attribute '{name}'"
        )


# Automatically register the integration only if it exists in the registry module
try:
    integration = create_integration()
    if hasattr(registry, "add_integration"):
        registry.add_integration(integration)
    else:
        logging.getLogger(__name__).warning(
            "Integration registry doesn't have add_integration method"
        )
except Exception as e:
    logging.getLogger(__name__).error(f"Failed to register GitHub integration: {e}")
