# quackcore/src/quackcore/paths/api/__init__.py
"""
API package for the paths module.

This package provides the API for the paths module,
including both public and internal interfaces.
"""

from quackcore.paths.api.public import ContextResult, PathResult

__all__ = [
    "PathResult",
    "ContextResult",
]
