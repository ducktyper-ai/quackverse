# src/quackster/academy/feedback.py
"""
Feedback module for quackster applications.

This module provides classes for creating, managing, and tracking
feedback for student submissions.
"""

import os
import uuid
from collections.abc import Sequence
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, model_validator

# Use QuackCore FS for file I/O.
from quackcore.fs import service as fs
from quackcore.logging import get_logger

# Use QuackCore Paths for resolving file paths against project structure.
from quackcore.paths import resolver

logger = get_logger(__name__)


class AnnotationType(Enum):
    """Type of annotation on student code."""

    COMMENT = "comment"
    SUGGESTION = "suggestion"
    QUESTION = "question"
    ERROR = "error"
    WARNING = "warning"
    PRAISE = "praise"


class Annotation(BaseModel):
    """
    Code annotation for feedback.

    Represents a comment or suggestion on a specific part of student code.
    """

    id: str = Field(description="Unique identifier for the annotation")
    type: AnnotationType = Field(
        default=AnnotationType.COMMENT, description="Type of annotation"
    )
    file_path: str = Field(description="Path to the file being annotated")
    line_start: int = Field(description="Starting line number (1-indexed)")
    line_end: int | None = Field(
        default=None, description="Ending line number (if range)"
    )
    column_start: int | None = Field(
        default=None, description="Starting column number (0-indexed)"
    )
    column_end: int | None = Field(default=None, description="Ending column number")
    text: str = Field(description="Annotation text")
    code_snippet: str | None = Field(
        default=None, description="Code snippet being annotated"
    )
    suggestion: str | None = Field(
        default=None, description="Suggested replacement (for suggestion type)"
    )

    @model_validator(mode="after")
    def ensure_id(self) -> "Annotation":
        """Ensure the annotation ID is set, generating one if needed."""
        if not self.id:
            self.id = str(uuid.uuid4())
        return self

    @classmethod
    def create(
        cls,
        file_path: str,
        line_start: int,
        text: str,
        type: AnnotationType = AnnotationType.COMMENT,
        line_end: int | None = None,
        suggestion: str | None = None,
    ) -> "Annotation":
        """
        Create a new annotation.

        Args:
            file_path: Path to the file being annotated.
            line_start: Starting line number (1-indexed).
            text: Annotation text.
            type: Type of annotation.
            line_end: Optional ending line number (for range).
            suggestion: Optional suggested replacement (for suggestion type).

        Returns:
            New annotation instance.
        """
        return cls(
            id=str(uuid.uuid4()),
            type=type,
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            text=text,
            suggestion=suggestion,
        )

    def format_for_github_pr(self) -> str:
        """
        Format the annotation for a GitHub PR review comment.

        Returns:
            Formatted text for GitHub PR review.
        """
        header = f"**{self.type.value.upper()}**"
        if self.type == AnnotationType.SUGGESTION and self.suggestion:
            return f"{header}: {self.text}\n\n```suggestion\n{self.suggestion}\n```"
        return f"{header}: {self.text}"


class FeedbackItemType(Enum):
    """Type of feedback item."""

    GENERAL = "general"
    SPECIFIC = "specific"
    QUESTION = "question"
    CODE_QUALITY = "code_quality"
    DESIGN = "design"
    LOGIC = "logic"
    STYLE = "style"
    TESTING = "testing"
    DOCUMENTATION = "documentation"


class FeedbackItem(BaseModel):
    """
    A single item of feedback.

    Represents one piece of feedback for a student submission.
    """

    id: str = Field(description="Unique identifier for the feedback item")
    type: FeedbackItemType = Field(
        default=FeedbackItemType.GENERAL, description="Type of feedback item"
    )
    text: str = Field(description="Feedback text")
    score: float | None = Field(
        default=None, description="Optional score associated with this item"
    )
    annotations: list[Annotation] = Field(
        default_factory=list,
        description="Code annotations associated with this feedback item",
    )

    @model_validator(mode="after")
    def ensure_id(self) -> "FeedbackItem":
        """Ensure the feedback item ID is set, generating one if needed."""
        if not self.id:
            self.id = str(uuid.uuid4())
        return self

    @classmethod
    def create(
        cls,
        text: str,
        type: FeedbackItemType = FeedbackItemType.GENERAL,
        score: float | None = None,
        annotations: list[Annotation] | None = None,
    ) -> "FeedbackItem":
        """
        Create a new feedback item.

        Args:
            text: Feedback text.
            type: Type of feedback item.
            score: Optional score associated with this item.
            annotations: Optional list of code annotations.

        Returns:
            New feedback item instance.
        """
        return cls(
            id=str(uuid.uuid4()),
            type=type,
            text=text,
            score=score,
            annotations=annotations or [],
        )

    def add_annotation(self, annotation: Annotation) -> None:
        """
        Add an annotation to the feedback item.

        Args:
            annotation: Annotation to add.
        """
        self.annotations.append(annotation)


class Feedback(BaseModel):
    """
    Comprehensive feedback for a student submission.

    Represents a collection of feedback items for a student submission.
    """

    id: str = Field(description="Unique identifier for the feedback")
    submission_id: str = Field(description="ID of the submission")
    student_id: str = Field(description="ID of the student")
    assignment_id: str = Field(description="ID of the assignment")
    created_at: datetime = Field(
        default_factory=datetime.now, description="When the feedback was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now, description="When the feedback was last updated"
    )
    score: float | None = Field(default=None, description="Overall score")
    summary: str | None = Field(default=None, description="Summary of the feedback")
    items: list[FeedbackItem] = Field(
        default_factory=list, description="Feedback items"
    )
    status: str = Field(
        default="draft",
        description="Status of the feedback (draft, reviewed, delivered)",
    )
    reviewer: str | None = Field(default=None, description="Name or ID of the reviewer")

    @model_validator(mode="after")
    def ensure_id(self) -> "Feedback":
        """Ensure the feedback ID is set, generating one if needed."""
        if not self.id:
            self.id = str(uuid.uuid4())
        return self

    @classmethod
    def create(
        cls,
        submission_id: str,
        student_id: str,
        assignment_id: str,
        score: float | None = None,
        summary: str | None = None,
        reviewer: str | None = None,
    ) -> "Feedback":
        """
        Create new feedback.

        Args:
            submission_id: ID of the submission.
            student_id: ID of the student.
            assignment_id: ID of the assignment.
            score: Optional overall score.
            summary: Optional summary.
            reviewer: Optional reviewer name or ID.

        Returns:
            New feedback instance.
        """
        return cls(
            id=str(uuid.uuid4()),
            submission_id=submission_id,
            student_id=student_id,
            assignment_id=assignment_id,
            score=score,
            summary=summary,
            reviewer=reviewer,
        )

    def add_item(self, item: FeedbackItem) -> None:
        """
        Add a feedback item.

        Args:
            item: Feedback item to add.
        """
        self.items.append(item)
        self.updated_at = datetime.now()

    def set_status(self, status: str) -> None:
        """
        Set the feedback status.

        Args:
            status: New status (draft, reviewed, delivered).
        """
        self.status = status
        self.updated_at = datetime.now()

    def format_for_github_pr(self) -> str:
        """
        Format the feedback for a GitHub PR review.

        Returns:
            Formatted text for GitHub PR review.
        """
        lines = [f"# Feedback: {self.score if self.score is not None else 'N/A'}/100"]
        if self.summary:
            lines.append("\n## Summary\n")
            lines.append(self.summary)
        if self.items:
            lines.append("\n## Detailed Feedback\n")
            for i, item in enumerate(self.items, 1):
                score_text = f" ({item.score} points)" if item.score is not None else ""
                lines.append(f"### {i}. {item.type.value.capitalize()}{score_text}\n")
                lines.append(item.text)
                lines.append("")  # Blank line
        return "\n".join(lines)

    def calculate_score(self) -> float | None:
        """
        Calculate the overall score based on feedback items.

        Returns:
            Calculated score or None if no scored items.
        """
        scored_items = [item for item in self.items if item.score is not None]
        if not scored_items:
            return None
        total_score = sum(item.score for item in scored_items)
        self.score = total_score
        self.updated_at = datetime.now()
        return total_score

    def update_gamification(self) -> None:
        """Update gamification based on this feedback."""
        try:
            # Import here to avoid circular imports.
            from quackster.core.gamification_service import GamificationService

            context = f"Feedback for submission {self.submission_id}"
            gamifier = GamificationService()
            result = gamifier.handle_feedback_submission(self.id, context)
            if result.message:
                logger.info(result.message)
        except Exception as e:
            logger.debug(f"Error integrating feedback with gamification: {str(e)}")


class FeedbackManager(BaseModel):
    """
    Manage a collection of feedback.

    This class provides functionality for loading, saving, and managing
    feedback for student submissions.
    """

    # Using a simple dict internally to store feedback items.
    feedback: dict[str, Feedback] = Field(default_factory=dict)
    by_submission: dict[str, Feedback] = Field(default_factory=dict)

    def add_feedback(self, feedback: Feedback) -> None:
        """
        Add feedback to the manager.

        Args:
            feedback: Feedback to add.
        """
        self.feedback[feedback.id] = feedback
        self.by_submission[feedback.submission_id] = feedback

    def get_feedback(self, feedback_id: str) -> Feedback | None:
        """
        Get feedback by ID.

        Args:
            feedback_id: ID of the feedback to get.

        Returns:
            Feedback if found, None otherwise.
        """
        return self.feedback.get(feedback_id)

    def get_feedback_by_submission(self, submission_id: str) -> Feedback | None:
        """
        Get feedback by submission ID.

        Args:
            submission_id: ID of the submission.

        Returns:
            Feedback if found, None otherwise.
        """
        return self.by_submission.get(submission_id)

    def add_multiple_feedback(self, feedback_items: Sequence[Feedback]) -> None:
        """
        Add multiple feedback items to the manager.

        Args:
            feedback_items: Sequence of feedback to add.
        """
        for feedback in feedback_items:
            self.add_feedback(feedback)

    def remove_feedback(self, feedback_id: str) -> bool:
        """
        Remove feedback from the manager.

        Args:
            feedback_id: ID of the feedback to remove.

        Returns:
            True if the feedback was removed, False if not found.
        """
        feedback = self.feedback.get(feedback_id)
        if feedback is None:
            return False
        del self.feedback[feedback_id]
        current = self.by_submission.get(feedback.submission_id)
        if current and current.id == feedback_id:
            del self.by_submission[feedback.submission_id]
        return True

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
            project_root = resolver.get_project_root()
            return fs._join_path(project_root, file_path)
        except FileNotFoundError as err:
            logger.warning(
                f"Project root not found: {err}. Falling back to current working directory."
            )
            return os.path.abspath(file_path)

    @classmethod
    def load_from_file(cls, file_path: str) -> "FeedbackManager":
        """
        Load feedback from a file.

        Args:
            file_path: Path to the file to load from.

        Returns:
            Loaded FeedbackManager instance.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the file format is invalid.
        """
        resolved_path = cls._resolve_file_path(file_path)
        result = fs.read_yaml(resolved_path)
        if not result.success:
            raise FileNotFoundError(
                f"Could not read feedback from {resolved_path}: {result.error}"
            )
        data = result.data
        if not isinstance(data, dict) or "feedback" not in data:
            raise ValueError(f"Invalid feedback format in {resolved_path}")
        manager = cls()
        for feedback_data in data["feedback"]:
            try:
                feedback = Feedback.model_validate(feedback_data)
                manager.add_feedback(feedback)
            except Exception as e:
                logger.warning(f"Error loading feedback: {e}")
        logger.info(
            f"Loaded {len(manager.feedback)} feedback items from {resolved_path}"
        )
        return manager

    def save_to_file(self, file_path: str) -> bool:
        """
        Save feedback to a file.

        Args:
            file_path: Path to save to.

        Returns:
            True if saved successfully, False otherwise.
        """
        resolved_path = self._resolve_file_path(file_path)
        data = {
            "feedback": [feedback.model_dump() for feedback in self.feedback.values()]
        }
        result = fs.write_yaml(resolved_path, data)
        if not result.success:
            logger.error(f"Error saving feedback to {resolved_path}: {result.error}")
            return False
        logger.info(f"Saved {len(self.feedback)} feedback items to {resolved_path}")
        return True
