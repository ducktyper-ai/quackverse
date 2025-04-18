# src/quackster/academy/plugin.py
"""
Plugin implementation for the QuackCore quackster module.

This module provides a plugin interface for the quackster module, allowing
integration with the QuackCore plugin system.
"""

import os
from typing import Any

from quackcore.errors import QuackFileNotFoundError  # Dogfood our errors
from quackcore.fs import service as fs
from quackcore.logging import get_logger
from quackcore.paths import service as paths
from quackcore.plugins.discovery import PluginInfo
from quackster.academy.context import TeachingContext
from quackster.academy.results import TeachingResult
from quackster.academy.service import TeachingService

logger = get_logger(__name__)


class QuackPlugin:
    pass


class TeachingPlugin(QuackPlugin):
    """
    Plugin implementation for the QuackCore quackster module.

    This plugin provides quackster functionality for QuackCore applications.
    """

    def __init__(self) -> None:
        """Initialize the quackster plugin."""
        self._service = TeachingService()
        self._initialized = False

    @property
    def info(self) -> PluginInfo:
        """
        Get plugin information.

        Returns:
            Plugin information.
        """
        return PluginInfo(
            name="quackster",
            version="0.1.0",
            description="Teaching module for QuackCore",
            author="QuackCore Team",
            dependencies=["github"],
        )

    def initialize(self, options: dict | None = None) -> TeachingResult:
        """
        Initialize the plugin.

        Args:
            options: Optional initialization options:
                - config_path: Path to the quackster configuration file.
                - base_dir: Base directory for quackster resources.

        Returns:
            TeachingResult indicating success or failure.
        """
        if self._initialized:
            return TeachingResult(
                success=True, message="Teaching plugin already initialized"
            )

        options = options or {}

        config_path = options.get("config_path")
        if config_path:
            # Expand user variables (e.g., '~') in the provided config path.
            config_path = fs.expand_user_vars(config_path)

        base_dir = options.get("base_dir")
        if base_dir:
            if not os.path.isabs(base_dir):
                try:
                    # Use the project root if available.
                    base_dir = fs.join_path(paths.get_project_root(), base_dir)
                except QuackFileNotFoundError as err:
                    logger.warning(
                        f"Project root not found: {err}. Falling back to os.path.abspath(base_dir)."
                    )
                    base_dir = os.path.abspath(base_dir)
        # Pass resolved options to the quackster service.
        result = self._service.initialize(config_path, base_dir)
        if result.success:
            self._initialized = True

        return result

    def create_context(
        self, course_name: str, github_org: str, base_dir: str | None = None
    ) -> TeachingResult:
        """
        Create a new quackster context.

        Args:
            course_name: Name of the course.
            github_org: GitHub organization for the course.
            base_dir: Optional base directory for quackster resources.

        Returns:
            TeachingResult indicating success or failure.
        """
        # Optionally, resolve the base_dir if provided.
        if base_dir and not os.path.isabs(base_dir):
            try:
                base_dir = fs.join_path(paths.get_project_root(), base_dir)
            except QuackFileNotFoundError as err:
                logger.warning(
                    f"Project root not found: {err}. Falling back to os.path.abspath(base_dir)."
                )
                base_dir = os.path.abspath(base_dir)
        return self._service.create_context(course_name, github_org, base_dir)

    def create_assignment(
        self,
        assignment_name: str,
        template_repo: str,
        description: str | None = None,
        due_date: str | None = None,
        students: list[str] | None = None,
    ) -> TeachingResult:
        """
        Create an assignment from a template repository.

        Args:
            assignment_name: Name of the assignment.
            template_repo: Name of the template repository.
            description: Optional assignment description.
            due_date: Optional due date (ISO format).
            students: Optional list of student GitHub usernames.

        Returns:
            TeachingResult with the created repositories on success.
        """
        if not self._initialized:
            return TeachingResult(
                success=False,
                error="Teaching plugin not initialized",
                message="Call initialize() before using plugin methods",
            )

        return self._service.create_assignment_from_template(
            assignment_name=assignment_name,
            template_repo=template_repo,
            description=description,
            due_date=due_date,
            students=students,
        )

    def find_student_submissions(
        self, assignment_name: str, student: str | None = None
    ) -> TeachingResult:
        """
        Find submissions for an assignment.

        Args:
            assignment_name: Name of the assignment.
            student: Optional student GitHub username.

        Returns:
            TeachingResult with the found submissions on success.
        """
        if not self._initialized:
            return TeachingResult(
                success=False,
                error="Teaching plugin not initialized",
                message="Call initialize() before using plugin methods",
            )
        return self._service.find_student_submissions(assignment_name, student)

    def get_context(self) -> TeachingContext | None:
        """
        Get the current quackster context.

        Returns:
            Current quackster context or None if not initialized.
        """
        if not self._initialized:
            return None
        return self._service.context

    def call(self, method: str, **kwargs: Any) -> Any:
        """
        Call a plugin method dynamically.

        Args:
            method: Name of the method to call.
            **kwargs: Method arguments.

        Returns:
            Method result.

        Raises:
            AttributeError: If the method doesn't exist.
        """
        if not hasattr(self, method):
            raise AttributeError(f"TeachingPlugin has no method '{method}'")
        return getattr(self, method)(**kwargs)


def create_plugin() -> TeachingPlugin:
    """
    Create a quackster plugin instance.

    Returns:
        Teaching plugin instance.
    """
    return TeachingPlugin()
