# src/quackster/academy/student.py
"""
Student management module.

This module provides classes for managing students, their information,
and their submissions in educational contexts.
"""

import os
import uuid
from collections.abc import Sequence
from datetime import datetime
from enum import Enum, auto

from pydantic import BaseModel, EmailStr, Field, model_validator

# Dogfood our errors by using our own error types
from quackcore.errors import QuackFileNotFoundError, QuackValidationError
from quackcore.fs import service as fs
from quackcore.logging import get_logger
from quackcore.paths import service as paths

logger = get_logger(__name__)


class SubmissionStatus(Enum):
    """Status of a student submission."""

    NOT_SUBMITTED = auto()
    SUBMITTED = auto()
    LATE = auto()
    GRADED = auto()
    RETURNED = auto()


class StudentSubmission(BaseModel):
    """A student submission for an assignment."""

    id: str = Field(description="Unique identifier for the submission")
    student_id: str = Field(description="ID of the student")
    assignment_id: str = Field(description="ID of the assignment")
    status: SubmissionStatus = Field(
        default=SubmissionStatus.NOT_SUBMITTED, description="Status of the submission"
    )
    submitted_at: datetime | None = Field(
        default=None, description="When the submission was made"
    )
    graded_at: datetime | None = Field(
        default=None, description="When the submission was graded"
    )
    score: float | None = Field(default=None, description="Score for the submission")
    pr_url: str | None = Field(
        default=None, description="URL of the pull request (if submitted via GitHub)"
    )
    repo_url: str | None = Field(
        default=None, description="URL of the repository (if submitted via GitHub)"
    )
    feedback_id: str | None = Field(
        default=None, description="ID of the associated feedback"
    )
    comments: str | None = Field(default=None, description="Comments on the submission")

    @classmethod
    def create(cls, student_id: str, assignment_id: str) -> "StudentSubmission":
        """
        Create a new submission.

        Args:
            student_id: ID of the student.
            assignment_id: ID of the assignment.

        Returns:
            New submission with default values.
        """
        return cls(
            id=str(uuid.uuid4()),
            student_id=student_id,
            assignment_id=assignment_id,
            status=SubmissionStatus.NOT_SUBMITTED,
        )

    def mark_submitted(
        self, pr_url: str | None = None, repo_url: str | None = None
    ) -> "StudentSubmission":
        """
        Mark the submission as submitted.

        Args:
            pr_url: Optional URL of the pull request.
            repo_url: Optional URL of the repository.

        Returns:
            Self for method chaining.
        """
        self.status = SubmissionStatus.SUBMITTED
        self.submitted_at = datetime.now()

        if pr_url:
            self.pr_url = pr_url

        if repo_url:
            self.repo_url = repo_url

        return self

    def mark_graded(
        self, score: float, feedback_id: str | None = None
    ) -> "StudentSubmission":
        """
        Mark the submission as graded.

        Args:
            score: Score for the submission.
            feedback_id: Optional ID of the associated feedback.

        Returns:
            Self for method chaining.
        """
        self.status = SubmissionStatus.GRADED
        self.graded_at = datetime.now()
        self.score = score

        if feedback_id:
            self.feedback_id = feedback_id

        return self

    def update_gamification(self) -> None:
        """Update gamification based on this submission."""
        if (
            self.status != SubmissionStatus.SUBMITTED
            and self.status != SubmissionStatus.GRADED
        ):
            return

        try:
            # Import here to avoid circular imports
            from quackster.core.gamification_service import GamificationService

            gamifier = GamificationService()

            if self.pr_url:
                pr_parts = self.pr_url.split("/")
                if len(pr_parts) >= 2:
                    try:
                        pr_number = int(pr_parts[-1])
                        repo = "/".join(pr_parts[-4:-2])
                        result = gamifier.handle_github_pr_submission(pr_number, repo)
                        if result.message:
                            logger.info(result.message)
                    except (ValueError, IndexError):
                        logger.debug(f"Could not parse PR URL: {self.pr_url}")

            if self.status == SubmissionStatus.GRADED and self.score is not None:
                result = gamifier.handle_assignment_completion(
                    assignment_id=self.assignment_id,
                    assignment_name=f"Assignment {self.assignment_id}",
                    score=self.score,
                    max_score=100.0,
                )
                if result.message:
                    logger.info(result.message)

        except Exception as e:
            logger.debug(f"Error integrating submission with gamification: {str(e)}")


class Student(BaseModel):
    """
    Student model for quackster applications.

    Represents a student with their basic information and settings.
    """

    id: str = Field(description="Unique identifier for the student")
    github_username: str = Field(description="GitHub username of the student")
    name: str = Field(description="Full name of the student")
    email: EmailStr | None = Field(
        default=None, description="Email address of the student"
    )
    active: bool = Field(default=True, description="Whether the student is active")
    group: str | None = Field(
        default=None, description="Group or section the student belongs to"
    )
    metadata: dict = Field(
        default_factory=dict, description="Additional metadata about the student"
    )
    submissions: dict[str, StudentSubmission] = Field(
        default_factory=dict, description="Student submissions by assignment ID"
    )

    @model_validator(mode="after")
    def ensure_id(self) -> "Student":
        """Ensure the student ID is set, generating one if needed."""
        if not self.id:
            self.id = str(uuid.uuid4())
        return self

    @classmethod
    def create(
        cls,
        github_username: str,
        name: str,
        email: str | None = None,
        group: str | None = None,
    ) -> "Student":
        """
        Create a new student.

        Args:
            github_username: GitHub username of the student.
            name: Full name of the student.
            email: Optional email address.
            group: Optional group or section.

        Returns:
            New student instance.
        """
        return cls(
            id=str(uuid.uuid4()),
            github_username=github_username,
            name=name,
            email=email,
            group=group,
        )

    def add_submission(self, submission: StudentSubmission) -> None:
        """
        Add a submission for this student.

        Args:
            submission: Submission to add.

        Raises:
            ValueError: If the submission is for a different student.
        """
        if submission.student_id != self.id:
            raise ValueError(
                f"Submission student ID {submission.student_id} does not match student ID {self.id}"
            )
        self.submissions[submission.assignment_id] = submission

    def get_submission(self, assignment_id: str) -> StudentSubmission | None:
        """
        Get a student's submission for an assignment.

        Args:
            assignment_id: ID of the assignment.

        Returns:
            Submission if found, None otherwise.
        """
        return self.submissions.get(assignment_id)

    def sync_with_progress(self) -> None:
        """
        Synchronize the student with the core UserProgress system.

        This ensures that the student's GitHub username is properly
        recorded in the UserProgress system, allowing for proper
        attribution of gamification rewards.
        """
        try:
            from quackster.core import utils as core_utils

            progress = core_utils.load_progress()
            if progress.github_username != self.github_username:
                progress.github_username = self.github_username
                core_utils.save_progress(progress)
                logger.info(
                    f"Updated progress GitHub username to {self.github_username}"
                )
        except Exception as e:
            logger.debug(f"Error syncing student with progress: {str(e)}")


class StudentRoster:
    """
    Manage a roster of students.

    This class provides functionality for loading, saving, and managing
    a collection of students.
    """

    def __init__(self) -> None:
        """Initialize an empty student roster."""
        self.students: dict[str, Student] = {}
        self.by_github: dict[str, Student] = {}

    def add_student(self, student: Student) -> None:
        """
        Add a student to the roster.

        Args:
            student: Student to add.
        """
        self.students[student.id] = student
        self.by_github[student.github_username.lower()] = student
        student.sync_with_progress()

    def get_student(self, student_id: str) -> Student | None:
        """
        Get a student by ID.

        Args:
            student_id: ID of the student to get.

        Returns:
            Student if found, None otherwise.
        """
        return self.students.get(student_id)

    def get_student_by_github(self, github_username: str) -> Student | None:
        """
        Get a student by GitHub username.

        Args:
            github_username: GitHub username of the student.

        Returns:
            Student if found, None otherwise.
        """
        return self.by_github.get(github_username.lower())

    def add_students(self, students: Sequence[Student]) -> None:
        """
        Add multiple students to the roster.

        Args:
            students: Sequence of students to add.
        """
        for student in students:
            self.add_student(student)

    def remove_student(self, student_id: str) -> bool:
        """
        Remove a student from the roster.

        Args:
            student_id: ID of the student to remove.

        Returns:
            True if the student was removed, False if not found.
        """
        student = self.students.get(student_id)
        if student is None:
            return False
        del self.students[student_id]
        del self.by_github[student.github_username.lower()]
        return True

    def get_active_students(self) -> list[Student]:
        """
        Get all active students.

        Returns:
            List of active students.
        """
        return [student for student in self.students.values() if student.active]

    def get_students_by_group(self, group: str) -> list[Student]:
        """
        Get students by group.

        Args:
            group: Group to filter by.

        Returns:
            List of students in the group.
        """
        return [student for student in self.students.values() if student.group == group]

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

    @classmethod
    def load_from_file(cls, file_path: str) -> "StudentRoster":
        """
        Load a student roster from a file.

        Args:
            file_path: Path to the file to load from.

        Returns:
            Loaded student roster.

        Raises:
            QuackFileNotFoundError: If the file doesn't exist.
            QuackValidationError: If the file format is invalid.
        """
        resolved_path = cls._resolve_file_path(file_path)
        result = fs.read_yaml(resolved_path)
        if not result.success:
            raise QuackFileNotFoundError(
                resolved_path,
                f"Could not read student roster from {resolved_path}: {result.error}",
            )
        data = result.data
        if not isinstance(data, dict) or "students" not in data:
            raise QuackValidationError(
                resolved_path, f"Invalid student roster format in {resolved_path}"
            )
        roster = cls()
        for student_data in data["students"]:
            try:
                student = Student.model_validate(student_data)
                roster.add_student(student)
            except Exception as e:
                logger.warning(f"Error loading student: {e}")
        logger.info(f"Loaded {len(roster.students)} students from {resolved_path}")
        return roster

    def save_to_file(self, file_path: str) -> bool:
        """
        Save the student roster to a file.

        Args:
            file_path: Path to save to.

        Returns:
            True if saved successfully, False otherwise.
        """
        resolved_path = self._resolve_file_path(file_path)
        data = {
            "students": [student.model_dump() for student in self.students.values()]
        }
        result = fs.write_yaml(resolved_path, data)
        if not result.success:
            logger.error(
                f"Error saving student roster to {resolved_path}: {result.error}"
            )
            return False
        logger.info(f"Saved {len(self.students)} students to {resolved_path}")
        return True
