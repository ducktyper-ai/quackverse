# src/quackcore/paths/__init__.py
"""
Path resolution and management utilities for QuackCore.

This package provides utilities for resolving paths, detecting project structure,
and inferring context from file locations in QuackCore projects.
"""

from quackcore.paths.context import ContentContext, ProjectContext, ProjectDirectory
from quackcore.paths.resolver import PathResolver, resolve_project_path
from quackcore.paths.utils import (
    find_nearest_directory,
    find_project_root,
    get_extension,
    infer_module_from_path,
    join_path,
    normalize_path,
    resolve_relative_to_project,
    split_path,
)

# Create a global instance for convenience
resolver = PathResolver()

__all__ = [
    # Classes
    "PathResolver",
    "ProjectContext",
    "ContentContext",
    "ProjectDirectory",
    # Global instance
    "resolver",
    "resolve_project_path",
    # Utility functions
    "find_project_root",
    "find_nearest_directory",
    "resolve_relative_to_project",
    "normalize_path",
    "join_path",
    "split_path",
    "get_extension",
    "infer_module_from_path",
]
