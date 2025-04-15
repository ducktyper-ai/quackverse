# src/quackcore/paths/__init__.py
"""
Path resolution and management utilities for QuackCore.

This package provides utilities for resolving paths, detecting project structure,
and inferring context from file locations in QuackCore projects.
"""
from quackcore.fs._helpers import _get_extension
from quackcore.fs._helpers.path_ops import _join_path, _split_path
from quackcore.paths._internal.context import ContentContext, ProjectContext, ProjectDirectory
from quackcore.paths._internal.resolver import PathResolver, _resolve_project_path
from quackcore.paths._internal.utils import _find_project_root, _find_nearest_directory, \
    _resolve_relative_to_project, _normalize_path, _infer_module_from_path

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
    "_resolve_project_path",
    # Utility functions
    "_find_project_root",
    "_find_nearest_directory",
    "_resolve_relative_to_project",
    "_normalize_path",
    "_join_path",
    "_split_path",
    "_get_extension",
    "_infer_module_from_path",
]
