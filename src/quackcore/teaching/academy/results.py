# src/quackcore/teaching/academy/results.py
"""
Result classes for teaching operations.

This module provides standardized result classes for teaching operations,
similar to the result pattern used throughout QuackCore.
"""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from quackcore.integrations.github.models import GitHubRepo, PullRequest

T = TypeVar("T")


class TeachingResult(BaseModel, Generic[T]):
    """
    Result of a teaching operation.

    This is the base class for all teaching operation results, providing
    a consistent interface for success/error handling.
    """

    success: bool = Field(description="Whether the operation was successful")
    message: str = Field(default="", description="Message describing the result")
    error: str | None = Field(
        default=None, description="Error message (if operation failed)"
    )
    content: T | None = Field(
        default=None, description="Result content (when operation succeeds)"
    )

    def __bool__(self) -> bool:
        """
        Boolean representation of the result.

        Returns:
            True if operation was successful, False otherwise
        """
        return self.success


class AssignmentResult(TeachingResult):
    """
    Result of an assignment operation.

    Extends TeachingResult with assignment-specific fields.
    """

    repositories: list[GitHubRepo] = Field(
        default_factory=list,
        description="GitHub repositories created or affected by the operation",
    )
    failed_students: list[str] = Field(
        default_factory=list,
        description="List of student GitHub usernames for which the operation failed",
    )


class SubmissionResult(TeachingResult):
    """
    Result of a submission operation.

    Extends TeachingResult with submission-specific fields.
    """

    pull_request: PullRequest | None = Field(
        default=None, description="Pull request created or affected by the operation"
    )
    student_github: str | None = Field(
        default=None, description="GitHub username of the student"
    )
    assignment_id: str | None = Field(default=None, description="ID of the assignment")


class FeedbackResult(TeachingResult):
    """
    Result of a feedback operation.

    Extends TeachingResult with feedback-specific fields.
    """

    feedback_id: str | None = Field(default=None, description="ID of the feedback")
    submission_id: str | None = Field(default=None, description="ID of the submission")
    score: float | None = Field(default=None, description="Score assigned")


class StudentResult(TeachingResult):
    """
    Result of a student operation.

    Extends TeachingResult with student-specific fields.
    """

    student_id: str | None = Field(default=None, description="ID of the student")
    github_username: str | None = Field(
        default=None, description="GitHub username of the student"
    )


class CourseResult(TeachingResult):
    """
    Result of a course operation.

    Extends TeachingResult with course-specific fields.
    """

    course_id: str | None = Field(default=None, description="ID of the course")
    course_name: str | None = Field(default=None, description="Name of the course")
