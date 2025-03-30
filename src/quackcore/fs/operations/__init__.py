# src/quackcore/fs/operations/__init__.py
"""
Core filesystem operations implementation.

This module provides the implementation of filesystem operations
with proper error handling and consistent return values.
"""

from typing import TypeVar

from quackcore.logging import get_logger

# Import the main class to maintain backward compatibility
from .base import FileSystemOperations

# Re-export the FileSystemOperations class
__all__ = ["FileSystemOperations"]

# Export TypeVar T for backward compatibility
T = TypeVar("T")  # Generic type for flexible typing

# Set up module-level logger
logger = get_logger(__name__)