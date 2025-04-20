# quackster/src/quackster/academy/context.py
"""
Teaching context management module.

This module provides the TeachingContext class, which is responsible for
managing the quackster environment, configuration, and dependencies.
"""

import os

from pydantic import BaseModel, Field, model_validator

# For configuration loading using YAML.
from quackcore.config.loader import load_yaml_config
from quackcore.errors import QuackConfigurationError

# Dogfood QuackCore FS for file and directory _operations.
from quackcore.fs import service as fs
from quackcore.integrations.core import registry
from quackcore.logging import get_logger

# Dogfood QuackCore Paths for project root detection and path resolution.
from quackcore.paths import service as paths

logger = get_logger(__name__)


class GitHubConfig(BaseModel):
    """GitHub configuration for quackster contexts."""

    organization: str = Field(
        description="GitHub organization where course repositories are hosted"
    )
    template_repo_prefix: str = Field(
        default="template-", description="Prefix for template repositories"
    )
    assignment_branch_prefix: str = Field(
        default="assignment-", description="Prefix for assignment branches"
    )
    default_base_branch: str = Field(
        default="main", description="Default base branch name"
    )
    pr_title_template: str = Field(
        default="[SUBMISSION] {title}", description="Template for pull request titles"
    )
    feedback_branch_prefix: str = Field(
        default="feedback-", description="Prefix for feedback branches"
    )
    auto_create_repos: bool = Field(
        default=False, description="Automatically create repositories when needed"
    )
    auto_star_repos: bool = Field(
        default=True, description="Automatically star repositories for tracking"
    )


class TeachingConfig(BaseModel):
    """Configuration model for quackster contexts."""

    course_name: str = Field(description="Name of the course")
    course_id: str = Field(default="", description="Unique identifier for the course")
    github: GitHubConfig = Field(
        default_factory=GitHubConfig, description="GitHub configuration"
    )
    assignments_dir: str = Field(
        default="assignments", description="Directory for storing assignment data"
    )
    feedback_dir: str = Field(
        default="feedback", description="Directory for storing feedback data"
    )
    grading_dir: str = Field(
        default="grading", description="Directory for storing grading data"
    )
    submissions_dir: str = Field(
        default="submissions", description="Directory for storing submission data"
    )
    students_file: str = Field(
        default="students.yaml", description="Path to students roster file"
    )
    course_config_file: str = Field(
        default="course.yaml", description="Path to course configuration file"
    )

    @model_validator(mode="after")
    def ensure_course_id(self) -> "TeachingConfig":
        """Ensure the course_id is set, generating one from course_name if needed."""
        if not self.course_id:
            self.course_id = self.course_name.lower().replace(" ", "-")
        return self


class TeachingContext:
    """
    Context for quackster _operations.

    This class manages the quackster environment, configuration, and dependencies.
    It serves as the central hub for accessing quackster resources and services.
    """

    def __init__(self, config: TeachingConfig, base_dir: str | None = None) -> None:
        """
        Initialize a quackster context.

        Args:
            config: Teaching configuration.
            base_dir: Base directory for quackster resources.
                If None, the project root will be determined via the resolver,
                falling back to the current working directory.
        """
        self.config = config

        # Determine the base directory either from the provided value or by detecting the project root.
        if base_dir is None:
            try:
                self.base_dir = paths.get_project_root()
            except FileNotFoundError as err:
                logger.warning(
                    f"Could not determine project root: {err}. Falling back to current working directory."
                )
                self.base_dir = os.getcwd()
        else:
            self.base_dir = str(base_dir)

        # Resolve all relative paths using _resolve_path which utilizes fs.join_path.
        self.assignments_dir = self._resolve_path(config.assignments_dir)
        self.feedback_dir = self._resolve_path(config.feedback_dir)
        self.grading_dir = self._resolve_path(config.grading_dir)
        self.submissions_dir = self._resolve_path(config.submissions_dir)
        self.students_file = self._resolve_path(config.students_file)
        self.course_config_file = self._resolve_path(config.course_config_file)

        # GitHub integration (lazy-loaded).
        self._github = None

        logger.info(f"Initialized quackster context for course: {config.course_name}")

    def _resolve_path(self, path_value: str) -> str:
        """
        Resolve a path relative to the base directory.

        Uses QuackCore FS's join_path to merge paths in a cross-platform way.

        Args:
            path_value: Path to resolve, either absolute or relative.

        Returns:
            A resolved absolute path as a string.
        """
        from quackcore.fs import service as fs

        return fs.resolve_path(path_value, self.base_dir)

    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        for directory in [
            self.assignments_dir,
            self.feedback_dir,
            self.grading_dir,
            self.submissions_dir,
        ]:
            fs.create_directory(directory, exist_ok=True)
        logger.debug(f"Ensured quackster directories exist in {self.base_dir}")

    @property
    def github(self):
        """
        Get the GitHub integration.

        Returns:
            Initialized GitHub integration.

        Raises:
            QuackConfigurationError: If GitHub integration cannot be initialized.
        """
        if self._github is None:
            github = registry.get_integration("GitHub")
            if github is None:
                raise QuackConfigurationError(
                    "GitHub integration not available. Make sure it's installed and registered."
                )
            if not hasattr(github, "client") or github.client is None:
                result = github.initialize()
                if not result.success:
                    raise QuackConfigurationError(
                        f"Failed to initialize GitHub integration: {result.error}"
                    )
            self._github = github
        return self._github

    @classmethod
    def from_config(
        cls, config_path: str | None = None, base_dir: str | None = None
    ) -> "TeachingContext":
        """
        Create a quackster context from a configuration file.

        Args:
            config_path: Path to the quackster configuration file.
                If None, standard locations or the QUACK_TEACHING_CONFIG environment variable are used.
            base_dir: Base directory for quackster resources.
                If None, it is inferred from the configuration file location.

        Returns:
            An initialized TeachingContext.

        Raises:
            QuackConfigurationError: If the configuration file cannot be loaded.
        """
        # Resolve configuration file path.
        if config_path is None:
            config_path = os.environ.get("QUACK_TEACHING_CONFIG")
            if not config_path:
                potential_paths = [
                    os.path.join(os.getcwd(), "teaching_config.yaml"),
                    os.path.join(os.getcwd(), "config", "quackster.yaml"),
                    os.path.join(
                        os.path.expanduser("~"), ".config", "quack", "quackster.yaml"
                    ),
                ]
                for p in potential_paths:
                    if os.path.exists(p):
                        config_path = p
                        break
        if config_path is None:
            raise QuackConfigurationError(
                "No quackster configuration file found. "
                "Specify the path or set the QUACK_TEACHING_CONFIG environment variable."
            )

        # Infer base_dir if not provided.
        if base_dir is None:
            base_dir = os.path.dirname(config_path)
        else:
            base_dir = str(base_dir)

        # Load configuration via YAML loader.
        try:
            config_dict = load_yaml_config(config_path)
            config = TeachingConfig.model_validate(config_dict)
        except Exception as e:
            raise QuackConfigurationError(
                f"Failed to load quackster configuration from {config_path}: {str(e)}",
                config_path=config_path,
                original_error=e,
            )

        context = cls(config, base_dir)
        context.ensure_directories()
        return context

    @classmethod
    def create_default(
        cls, course_name: str, github_org: str, base_dir: str | None = None
    ) -> "TeachingContext":
        """
        Create a quackster context with default configuration.

        Args:
            course_name: Name of the course.
            github_org: GitHub organization for the course.
            base_dir: Base directory for quackster resources.

        Returns:
            An initialized TeachingContext with default settings.
        """
        config = TeachingConfig(
            course_name=course_name, github=GitHubConfig(organization=github_org)
        )
        context = cls(config, base_dir)
        context.ensure_directories()
        return context
