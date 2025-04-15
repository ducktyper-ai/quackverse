# src/quackcore/paths/api/public/results.py
"""
Path resolution result models.

This module defines result models for path resolution operations.
"""

from typing import Optional

from pydantic import BaseModel

from quackcore.paths._internal.context import ContentContext, ProjectContext


class PathResult(BaseModel):
    """
    Result of a path resolution operation.

    Attributes:
        success: Whether the operation was successful.
        path: The resolved path, if successful.
        error: Error message, if unsuccessful.
    """

    success: bool
    path: Optional[str] = None
    error: Optional[str] = None


class ContextResult(BaseModel):
    """
    Result of a context detection operation.

    Attributes:
        success: Whether the operation was successful.
        context: The detected context, if successful.
        error: Error message, if unsuccessful.
    """

    success: bool
    context: Optional[ProjectContext | ContentContext] = None
    error: Optional[str] = None
