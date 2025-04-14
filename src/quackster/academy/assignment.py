# src/quackster/academy/assignment.py
"""
Assignment management module.

This module provides classes for creating, managing, and tracking
educational assignments and their associated workflows.
"""

import uuid
from collections.abc import Sequence
from datetime import datetime
from enum import Enum, auto
from pathlib import Path

from pydantic import BaseModel, Field, model_validator

from quackcore.fs import service as fs
from quackcore.logging import get_logger

logger = get_logger(__name__)


class AssignmentStatus(Enum):
    """Status of an assignment."""

    DRAFT = auto()
    PUBLISHED = auto()
    ACTIVE = auto()
    PAST_DUE = auto()
    CLOSED = auto()


class AssignmentType(Enum):
    """Type of assignment."""

    INDIVIDUAL = auto()
    GROUP = auto()
    QUIZ = auto()
    EXAM = auto()
    PROJECT = auto()
    DISCUSSION = auto()


class Assignment(BaseModel):
    """
    Assignment model for quackster applications.

    Represents an educational assignment with its settings and metadata.
    """

    id: str = Field(description="Unique identifier for the assignment")
    name: str = Field(description="Name of the assignment")
    description: str | None = Field(
        default=None, description="Description of the assignment"
    )
    status: AssignmentStatus = Field(
        default=AssignmentStatus.DRAFT, description="Status of the assignment"
    )
    assignment_type: AssignmentType = Field(
        default=AssignmentType.INDIVIDUAL, description="Type of assignment"
    )
    due_date: datetime | None = Field(
        default=None, description="Due date for the assignment"
    )
    points: float = Field(
        default=100.0, description="Total points possible for the assignment"
    )
    published_at: datetime | None = Field(
        default=None, description="When the assignment was published"
    )
    template_repo: str | None = Field(
        default=None, description="GitHub template repository for the assignment"
    )
    starter_code_url: str | None = Field(
        default=None, description="URL to starter code (if not using a template repo)"
    )
    instructions_url: str | None = Field(
        default=None, description="URL to assignment instructions"
    )
    allow_late_submissions: bool = Field(
        default=True, description="Whether late submissions are allowed"
    )
    late_penalty_percentage: float = Field(
        default=10.0, description="Percentage penalty for late submissions"
    )
    repositories: list[str] = Field(
        default_factory=list,
        description="List of GitHub repositories for this assignment",
    )
    metadata: dict = Field(
        default_factory=dict, description="Additional metadata for the assignment"
    )

    @model_validator(mode="after")
    def ensure_id(self) -> "Assignment":
        """Ensure the assignment ID is set, generating one if needed."""
        if not self.id:
            self.id = str(uuid.uuid4())
        return self

    @classmethod
    def create(
        cls,
        name: str,
        description: str | None = None,
        assignment_type: AssignmentType = AssignmentType.INDIVIDUAL,
        due_date: datetime | str | None = None,
        points: float = 100.0,
    ) -> "Assignment":
        """
        Create a new assignment.

        Args:
            name: Name of the assignment
            description: Optional description
            assignment_type: Type of assignment
            due_date: Optional due date (datetime or ISO format string)
            points: Total points possible

        Returns:
            New assignment instance
        """
        # Convert string due date to datetime if provided
        parsed_due_date = None
        if due_date is not None:
            if isinstance(due_date, str):
                parsed_due_date = datetime.fromisoformat(due_date)
            else:
                parsed_due_date = due_date

        return cls(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            assignment_type=assignment_type,
            due_date=parsed_due_date,
            points=points,
        )

    def publish(self) -> "Assignment":
        """
        Mark the assignment as published.

        Returns:
            Self for method chaining
        """
        self.status = AssignmentStatus.PUBLISHED
        self.published_at = datetime.now()
        return self

    def close(self) -> "Assignment":
        """
        Mark the assignment as closed.

        Returns:
            Self for method chaining
        """
        self.status = AssignmentStatus.CLOSED
        return self

    def is_past_due(self) -> bool:
        """
        Check if the assignment is past due.

        Returns:
            True if the assignment is past due, False otherwise
        """
        if self.due_date is None:
            return False
        return datetime.now() > self.due_date

    def update_status(self) -> "Assignment":
        """
        Update the assignment status based on current date.

        Returns:
            Self for method chaining
        """
        # Don't change draft or closed status
        if self.status in (AssignmentStatus.DRAFT, AssignmentStatus.CLOSED):
            return self

        # Check if past due
        if self.is_past_due():
            self.status = AssignmentStatus.PAST_DUE
        elif self.published_at is not None:
            self.status = AssignmentStatus.ACTIVE

        return self

    def add_repository(self, repo_name: str) -> None:
        """
        Add a GitHub repository to the assignment.

        Args:
            repo_name: Full name of the repository (org/name)
        """
        if repo_name not in self.repositories:
            self.repositories.append(repo_name)

    def get_student_repo_name(self, student_github: str) -> str:
        """
        Get the expected repository name for a student.

        Args:
            student_github: GitHub username of the student

        Returns:
            Expected repository name (without organization)
        """
        normalized_name = self.name.lower().replace(" ", "-")
        return f"{normalized_name}-{student_github}"


class AssignmentManager:
    """
    Manage a collection of assignments.

    This class provides functionality for loading, saving, and managing
    assignments.
    """

    def __init__(self) -> None:
        """Initialize an empty assignment manager."""
        self.assignments: dict[str, Assignment] = {}
        self.by_name: dict[str, Assignment] = {}

    def add_assignment(self, assignment: Assignment) -> None:
        """
        Add an assignment to the manager.

        Args:
            assignment: Assignment to add
        """
        self.assignments[assignment.id] = assignment
        self.by_name[assignment.name.lower()] = assignment

    def get_assignment(self, assignment_id: str) -> Assignment | None:
        """
        Get an assignment by ID.

        Args:
            assignment_id: ID of the assignment to get

        Returns:
            Assignment if found, None otherwise
        """
        return self.assignments.get(assignment_id)

    def get_assignment_by_name(self, name: str) -> Assignment | None:
        """
        Get an assignment by name.

        Args:
            name: Name of the assignment

        Returns:
            Assignment if found, None otherwise
        """
        return self.by_name.get(name.lower())

    def add_assignments(self, assignments: Sequence[Assignment]) -> None:
        """
        Add multiple assignments to the manager.

        Args:
            assignments: Sequence of assignments to add
        """
        for assignment in assignments:
            self.add_assignment(assignment)

    def remove_assignment(self, assignment_id: str) -> bool:
        """
        Remove an assignment from the manager.

        Args:
            assignment_id: ID of the assignment to remove

        Returns:
            True if the assignment was removed, False if not found
        """
        assignment = self.assignments.get(assignment_id)
        if assignment is None:
            return False

        del self.assignments[assignment_id]
        del self.by_name[assignment.name.lower()]
        return True

    def update_statuses(self) -> None:
        """Update the status of all assignments based on current date."""
        for assignment in self.assignments.values():
            assignment.update_status()

    def get_active_assignments(self) -> list[Assignment]:
        """
        Get all active assignments.

        Returns:
            List of active assignments
        """
        self.update_statuses()
        return [
            assignment
            for assignment in self.assignments.values()
            if assignment.status == AssignmentStatus.ACTIVE
        ]

    def get_past_due_assignments(self) -> list[Assignment]:
        """
        Get all past due assignments.

        Returns:
            List of past due assignments
        """
        self.update_statuses()
        return [
            assignment
            for assignment in self.assignments.values()
            if assignment.status == AssignmentStatus.PAST_DUE
        ]

    @classmethod
    def load_from_file(cls, file_path: str | Path) -> "AssignmentManager":
        """
        Load assignments from a file.

        Args:
            file_path: Path to the file to load from

        Returns:
            Loaded assignment manager

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is invalid
        """
        result = fs.read_yaml(file_path)
        if not result.success:
            raise FileNotFoundError(
                f"Could not read assignments from {file_path}: {result.error}"
            )

        data = result.data
        if not isinstance(data, dict) or "assignments" not in data:
            raise ValueError(f"Invalid assignments format in {file_path}")

        manager = cls()
        for assignment_data in data["assignments"]:
            try:
                assignment = Assignment.model_validate(assignment_data)
                manager.add_assignment(assignment)
            except Exception as e:
                logger.warning(f"Error loading assignment: {e}")

        logger.info(f"Loaded {len(manager.assignments)} assignments from {file_path}")
        return manager

    def save_to_file(self, file_path: str | Path) -> bool:
        """
        Save assignments to a file.

        Args:
            file_path: Path to save to

        Returns:
            True if saved successfully, False otherwise
        """
        data = {
            "assignments": [
                assignment.model_dump() for assignment in self.assignments.values()
            ]
        }

        result = fs.write_yaml(file_path, data)
        if not result.success:
            logger.error(f"Error saving assignments to {file_path}: {result.error}")
            return False

        logger.info(f"Saved {len(self.assignments)} assignments to {file_path}")
        return True
