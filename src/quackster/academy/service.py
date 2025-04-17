# src/quackster/academy/service.py
"""
Teaching service module.

This module provides the primary service for quackster _operations,
serving as the main entry point for quackster _operations.
"""

import os

from quackcore.errors import QuackError, QuackFileNotFoundError
from quackcore.fs import service as fs
from quackcore.logging import get_logger
from quackcore.paths import service as paths
from quackster.academy.context import TeachingContext
from quackster.academy.results import AssignmentResult, TeachingResult
from quackster.core.gamification_service import GamificationService

logger = get_logger(__name__)


class TeachingService:
    """
    Service for quackster _operations.

    Provides methods for initialization, context creation,
    repository and assignment management, and integration with
    the gamification system.
    """

    def __init__(self) -> None:
        """Initialize the quackster service."""
        self._context: TeachingContext | None = None
        self._github = None

    def initialize(
        self, config_path: str | None = None, base_dir: str | None = None
    ) -> TeachingResult:
        """
        Initialize the quackster service.

        Args:
            config_path: Path to the configuration file.
            base_dir: Base directory for quackster resources.

        Returns:
            TeachingResult indicating success or failure.
        """
        try:
            if config_path is not None:
                config_path = fs.expand_user_vars(config_path)
            if base_dir is not None:
                if not os.path.isabs(base_dir):
                    try:
                        project_root = paths.get_project_root()
                        base_dir = fs.join_path(project_root, base_dir)
                    except QuackFileNotFoundError as err:
                        logger.warning(
                            f"Project root not found: {err}. Falling back to os.path.abspath(base_dir)."
                        )
                        base_dir = os.path.abspath(base_dir)
            self._context = TeachingContext.from_config(config_path, base_dir)
            logger.info(
                f"Teaching service initialized for course: {self._context.config.course_name}"
            )
            return TeachingResult(
                success=True,
                message=f"Teaching service initialized for course: {self._context.config.course_name}",
            )
        except QuackError as e:
            logger.error(f"Failed to initialize quackster service: {str(e)}")
            return TeachingResult(
                success=False,
                error=str(e),
                message="Failed to initialize quackster service",
            )

    def create_context(
        self, course_name: str, github_org: str, base_dir: str | None = None
    ) -> TeachingResult:
        """
        Create a new quackster context with default settings.

        Args:
            course_name: Name of the course.
            github_org: GitHub organization for the course.
            base_dir: Base directory for quackster resources.

        Returns:
            TeachingResult indicating success or failure.
        """
        if base_dir is not None:
            if not os.path.isabs(base_dir):
                try:
                    base_dir = fs.join_path(paths.get_project_root(), base_dir)
                except QuackFileNotFoundError as err:
                    logger.warning(
                        f"Project root not found: {err}. Falling back to os.path.abspath(base_dir)."
                    )
                    base_dir = os.path.abspath(base_dir)
        try:
            self._context = TeachingContext.create_default(
                course_name, github_org, base_dir
            )
            logger.info(f"Created new quackster context for course: {course_name}")
            return TeachingResult(
                success=True,
                message=f"Created new quackster context for course: {course_name}",
            )
        except QuackError as e:
            logger.error(f"Failed to create quackster context: {str(e)}")
            return TeachingResult(
                success=False,
                error=str(e),
                message="Failed to create quackster context",
            )

    @property
    def context(self) -> TeachingContext | None:
        """
        Get the current quackster context.

        Returns:
            Current quackster context or None if not initialized.
        """
        return self._context

    @property
    def github(self):
        """
        Get the GitHub integration.

        Returns:
            GitHub integration or None if not available.
        """
        if self._context is None:
            return None
        try:
            return self._context.github
        except QuackError:
            return None

    def _integrate_with_gamification(self, action: str, **kwargs) -> None:
        """
        Integrate an academy action with the gamification system.

        Args:
            action: The type of action (e.g., module_completion, course_completion, etc.)
            **kwargs: Additional parameters for the action.
        """
        try:
            gamifier = GamificationService()
            result = None
            if action == "module_completion":
                result = gamifier.handle_module_completion(
                    course_id=kwargs.get("course_id", ""),
                    module_id=kwargs.get("module_id", ""),
                    module_name=kwargs.get("module_name", "Unknown Module"),
                )
            elif action == "course_completion":
                result = gamifier.handle_course_completion(
                    course_id=kwargs.get("course_id", ""),
                    course_name=kwargs.get("course_name", "Unknown Course"),
                )
            elif action == "assignment_completion":
                result = gamifier.handle_assignment_completion(
                    assignment_id=kwargs.get("assignment_id", ""),
                    assignment_name=kwargs.get("assignment_name", "Unknown Assignment"),
                    score=kwargs.get("score", 0.0),
                    max_score=kwargs.get("max_score", 100.0),
                )
            elif action == "feedback_submission":
                result = gamifier.handle_feedback_submission(
                    feedback_id=kwargs.get("feedback_id", ""),
                    context=kwargs.get("context", "Unknown Context"),
                )
            if result and result.message:
                logger.info(result.message)
        except QuackError as e:
            logger.debug(
                f"Error integrating academy action with gamification: {str(e)}"
            )

    def ensure_repo_exists(
        self, repo_name: str, private: bool = True, description: str | None = None
    ) -> TeachingResult:
        """
        Ensure a repository exists in the course organization.

        Args:
            repo_name: Name of the repository (without organization).
            private: Whether the repository should be private.
            description: Optional repository description.

        Returns:
            TeachingResult with the repository on success.
        """
        if self._context is None:
            return TeachingResult(
                success=False,
                error="Teaching service not initialized",
                message="Call initialize() before using the service",
            )
        github = self.github
        if github is None:
            return TeachingResult(
                success=False,
                error="GitHub integration not available",
                message="GitHub integration is required but not available",
            )
        org = self._context.config.github.organization
        full_repo_name = f"{org}/{repo_name}"
        try:
            repo_result = github.get_repo(full_repo_name)
            if repo_result.success:
                logger.info(f"Repository {full_repo_name} already exists")
                return TeachingResult(
                    success=True,
                    message=f"Repository {full_repo_name} already exists",
                    content=repo_result.content,
                )
            if not self._context.config.github.auto_create_repos:
                return TeachingResult(
                    success=False,
                    error=f"Repository {full_repo_name} does not exist and auto-creation is disabled",
                    message="Enable auto_create_repos in config to create repositories automatically",
                )
            repo_creation_result = github.create_repo(
                org=org,
                repo_name=repo_name,
                private=private,
                description=description,
            )
            if repo_creation_result.success:
                logger.info(f"Repository {full_repo_name} created successfully.")
                return TeachingResult(
                    success=True,
                    message=f"Repository {full_repo_name} created successfully.",
                    content=repo_creation_result.content,
                )
            else:
                logger.error(
                    f"Failed to create repository {full_repo_name}: {repo_creation_result.error}"
                )
                return TeachingResult(
                    success=False,
                    error=repo_creation_result.error,
                    message=f"Failed to create repository {full_repo_name}",
                )
        except QuackError as e:
            logger.error(f"Error ensuring repository exists: {str(e)}")
            return TeachingResult(
                success=False,
                error=str(e),
                message=f"Failed to ensure repository {full_repo_name} exists",
            )

    def create_assignment_from_template(
        self,
        assignment_name: str,
        template_repo: str,
        description: str | None = None,
        due_date: str | None = None,
        students: list[str] | None = None,
    ) -> AssignmentResult:
        """
        Create an assignment from a template repository.

        Args:
            assignment_name: Name of the assignment.
            template_repo: Name of the template repository.
            description: Optional assignment description.
            due_date: Optional due date (ISO format).
            students: List of student GitHub usernames.

        Returns:
            AssignmentResult with the created repositories on success.
        """
        if self._context is None:
            return AssignmentResult(
                success=False,
                error="Teaching service not initialized",
                message="Call initialize() before using the service",
            )
        github = self.github
        if github is None:
            return AssignmentResult(
                success=False,
                error="GitHub integration not available",
                message="GitHub integration is required but not available",
            )
        org = self._context.config.github.organization
        if not template_repo.startswith(f"{org}/"):
            template_repo = f"{org}/{template_repo}"
        template_result = github.get_repo(template_repo)
        if not template_result.success:
            return AssignmentResult(
                success=False,
                error=f"Template repository {template_repo} does not exist",
                message="Ensure the template repository exists before creating an assignment",
            )
        if not students:
            return AssignmentResult(
                success=False,
                error="Student list not provided",
                message="Provide a list of student GitHub usernames",
            )
        repo_name_base = assignment_name.lower().replace(" ", "-")
        created_repos = []
        failed_students = []
        for student in students:
            student_repo_name = f"{repo_name_base}-{student}"
            full_repo_name = f"{org}/{student_repo_name}"
            try:
                repo_result = github.get_repo(full_repo_name)
                if repo_result.success:
                    logger.info(f"Repository {full_repo_name} already exists")
                    created_repos.append(repo_result.content)
                else:
                    new_description = description if description else ""
                    if due_date:
                        new_description += f" | Due: {due_date}"
                    creation_result = self.ensure_repo_exists(
                        repo_name=student_repo_name,
                        private=True,
                        description=new_description,
                    )
                    if creation_result.success:
                        logger.info(
                            f"Successfully created repository {full_repo_name} for student {student}"
                        )
                        created_repos.append(creation_result.content)
                    else:
                        logger.error(
                            f"Failed to create repository for {student}: {creation_result.error}"
                        )
                        failed_students.append(student)
            except QuackError as e:
                logger.error(f"Error processing repository for {student}: {str(e)}")
                failed_students.append(student)
        if failed_students:
            return AssignmentResult(
                success=False,
                error=f"Failed to create repositories for {len(failed_students)} students",
                message=f"Successfully created {len(created_repos)} repositories; failed for {len(failed_students)} students",
                repositories=created_repos,
                failed_students=failed_students,
            )
        if not created_repos:
            return AssignmentResult(
                success=False,
                error="No repositories created",
                message="Failed to create any assignment repositories",
            )
        self._integrate_with_gamification(
            "assignment_completion",
            assignment_id=assignment_name,
            assignment_name=assignment_name,
        )
        return AssignmentResult(
            success=True,
            message=f"Successfully created {len(created_repos)} assignment repositories",
            repositories=created_repos,
        )

    def find_student_submissions(
        self, assignment_name: str, student: str | None = None
    ) -> TeachingResult:
        """
        Find submissions for an assignment.

        Args:
            assignment_name: Name of the assignment.
            student: Specific student GitHub username.

        Returns:
            TeachingResult with the found submission.
        """
        if self._context is None:
            return TeachingResult(
                success=False,
                error="Teaching service not initialized",
                message="Call initialize() before using the service",
            )
        github = self.github
        if github is None:
            return TeachingResult(
                success=False,
                error="GitHub integration not available",
                message="GitHub integration is required but not available",
            )
        org = self._context.config.github.organization
        repo_name_base = assignment_name.lower().replace(" ", "-")
        if student:
            student_repo_name = f"{repo_name_base}-{student}"
            full_repo_name = f"{org}/{student_repo_name}"
            repo_result = github.get_repo(full_repo_name)
            if not repo_result.success:
                return TeachingResult(
                    success=False,
                    error=f"Repository {full_repo_name} does not exist",
                    message=f"No repository found for student {student} and assignment {assignment_name}",
                )
            return TeachingResult(
                success=True,
                message=f"Found repository for student {student} and assignment {assignment_name}",
                content=repo_result.content,
            )
        return TeachingResult(
            success=False,
            error="Finding all submissions is not yet implemented",
            message="Provide a specific student name to find submissions",
        )

    def record_module_completion(
        self, course_id: str, module_id: str, module_name: str
    ) -> TeachingResult:
        """
        Record completion of a module.

        Args:
            course_id: ID of the course.
            module_id: ID of the module.
            module_name: Name of the module.

        Returns:
            TeachingResult indicating success or failure.
        """
        if self._context is None:
            return TeachingResult(
                success=False,
                error="Teaching service not initialized",
                message="Call initialize() before using the service",
            )
        self._integrate_with_gamification(
            "module_completion",
            course_id=course_id,
            module_id=module_id,
            module_name=module_name,
        )
        return TeachingResult(
            success=True,
            message=f"Successfully recorded completion of module '{module_name}'",
        )

    def record_course_completion(
        self, course_id: str, course_name: str
    ) -> TeachingResult:
        """
        Record completion of a course.

        Args:
            course_id: ID of the course.
            course_name: Name of the course.

        Returns:
            TeachingResult indicating success or failure.
        """
        if self._context is None:
            return TeachingResult(
                success=False,
                error="Teaching service not initialized",
                message="Call initialize() before using the service",
            )
        self._integrate_with_gamification(
            "course_completion", course_id=course_id, course_name=course_name
        )
        return TeachingResult(
            success=True,
            message=f"Successfully recorded completion of course '{course_name}'",
        )

    def grade_student_assignment(
        self,
        assignment_id: str,
        student_github: str,
        score: float,
        feedback: str | None = None,
    ) -> TeachingResult:
        """
        Grade a student's assignment.

        Args:
            assignment_id: ID of the assignment.
            student_github: GitHub username of the student.
            score: Score to assign (0-100).
            feedback: Optional feedback text.

        Returns:
            TeachingResult indicating success or failure.
        """
        if self._context is None:
            return TeachingResult(
                success=False,
                error="Teaching service not initialized",
                message="Call initialize() before using the service",
            )

        assignment_name = f"Assignment {assignment_id}"
        max_score = 100.0

        self._integrate_with_gamification(
            "assignment_completion",
            assignment_id=assignment_id,
            assignment_name=assignment_name,
            score=score,
            max_score=max_score,
            feedback=feedback,
        )

        message = f"Successfully graded assignment '{assignment_name}' for student {student_github}."
        if feedback is not None:
            message += f" Feedback provided: {feedback}"

        return TeachingResult(
            success=True,
            message=message,
        )

    @staticmethod
    def _resolve_file_path(file_path: str) -> str:
        """
        Resolve a file path to an absolute path.

        If the given file_path is relative, attempt to resolve it relative to the project root
        using the QuackCore Paths resolver; if that fails, resolve it relative to the current working directory.

        Args:
            file_path: The path to resolve as a string.

        Returns:
            An absolute path as a string.
        """
        if os.path.isabs(file_path):
            return file_path
        try:
            project_root = paths.get_project_root()
            return fs.join_path(project_root, file_path)
        except FileNotFoundError as err:
            logger.warning(
                f"Project root not found: {err}. Falling back to os.path.abspath(file_path)."
            )
            return os.path.abspath(file_path)

    def save_config(self, config_path: str | None = None) -> TeachingResult:
        """
        Save the current configuration to a file.

        Args:
            config_path: Path where to save the configuration.
                        If None, uses the default location within the current context base directory.

        Returns:
            TeachingResult indicating success or failure.
        """
        if self._context is None:
            return TeachingResult(
                success=False,
                error="Teaching service not initialized",
                message="Call initialize() before saving configuration",
            )
        if config_path is None:
            config_path = fs.join_path(self._context.base_dir, "teaching_config.yaml")
        else:
            config_path = self._resolve_file_path(config_path)
        config_dict = self._context.config.model_dump()
        try:
            result = fs.write_yaml(config_path, config_dict)
            if result.success:
                logger.info(f"Configuration saved to {config_path}")
                return TeachingResult(
                    success=True, message=f"Configuration saved to {config_path}"
                )
            else:
                return TeachingResult(
                    success=False,
                    error=f"Failed to save configuration: {result.error}",
                    message=f"Could not save configuration to {config_path}",
                )
        except QuackError as e:
            logger.error(f"Error saving configuration: {str(e)}")
            return TeachingResult(
                success=False,
                error=str(e),
                message=f"Failed to save configuration to {config_path}",
            )


# Create the global service instance
service = TeachingService()
