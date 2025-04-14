# src/quackster/academy/grading.py
"""
Grading module for quackster applications.

This module provides classes and utilities for defining grading criteria
and evaluating student submissions against those criteria.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

# Use QuackCore FS for file operations and path expansion.
from quackcore.fs import service as fs
from quackcore.logging import get_logger

logger = get_logger(__name__)


class GradingCriterion(BaseModel):
    """A single grading criterion for evaluating student work."""

    id: str = Field(description="Unique identifier for the criterion")
    name: str = Field(description="Name of the criterion")
    description: str | None = Field(
        default=None, description="Description of the criterion"
    )
    points: float = Field(description="Maximum points possible for this criterion")
    required: bool = Field(
        default=False, description="Whether this criterion is required to pass"
    )
    category: str | None = Field(
        default=None,
        description="Category for the criterion (e.g., 'style', 'functionality')",
    )
    rubric: dict | None = Field(
        default=None,
        description="Optional rubric with point values for different levels",
    )

    @model_validator(mode="after")
    def ensure_id(self) -> "GradingCriterion":
        """Ensure the criterion ID is set, generating one if needed."""
        if not self.id:
            self.id = str(uuid.uuid4())
        return self

    @classmethod
    def create(
        cls,
        name: str,
        points: float,
        description: str | None = None,
        required: bool = False,
        category: str | None = None,
        rubric: dict | None = None,
    ) -> "GradingCriterion":
        """
        Create a new grading criterion.

        Args:
            name: Name of the criterion
            points: Maximum points possible
            description: Optional description
            required: Whether this criterion is required to pass
            category: Optional category
            rubric: Optional rubric with point values for different levels

        Returns:
            New grading criterion instance
        """
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            points=points,
            required=required,
            category=category,
            rubric=rubric,
        )


class FileCheckCriterion(GradingCriterion):
    """A criterion that checks for the presence of required files."""

    files: list[str] = Field(description="List of files that should be present")

    @model_validator(mode="after")
    def expand_file_paths(self) -> "FileCheckCriterion":
        """
        Expand any shell-style variables (e.g. '~') in file paths using QuackCore FS.

        Returns:
            The instance with all file paths expanded.
        """
        self.files = [fs.expand_user_vars(f) for f in self.files]
        return self

    @classmethod
    def create(
        cls,
        name: str,
        points: float,
        description: str | None = None,
        required: bool = False,
        category: str | None = None,
        rubric: dict | None = None,
        files: list[str] | None = None,  # extra parameter made optional
    ) -> "FileCheckCriterion":
        """
        Create a new file check criterion.

        Args:
            name: Name of the criterion.
            points: Maximum points possible.
            description: Optional description.
            required: Whether this criterion is required to pass.
            category: Ignored (will be set to "files").
            rubric: Optional rubric (passed to the base for consistency).
            files: List of files that should be present.

        Returns:
            New file check criterion instance.
        """
        if files is None:
            raise ValueError("files must be provided")
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            description=description or f"Check for required files: {', '.join(files)}",
            points=points,
            required=required,
            category="files",
            rubric=rubric,
            files=files,
        )


class PatternCheckCriterion(GradingCriterion):
    """A criterion that checks for patterns in code files."""

    patterns: list[dict] = Field(description="List of patterns to check for")
    file_patterns: list[str] = Field(
        default_factory=lambda: ["*.py"],
        description="File patterns to check (e.g., '*.py')",
    )

    @model_validator(mode="after")
    def expand_file_patterns(self) -> "PatternCheckCriterion":
        """
        Expand any shell-style variables in file pattern strings.

        Returns:
            The instance with file patterns expanded.
        """
        self.file_patterns = [fs.expand_user_vars(fp) for fp in self.file_patterns]
        return self

    @classmethod
    def create(
        cls,
        name: str,
        points: float,
        description: str | None = None,
        required: bool = False,
        category: str | None = None,
        rubric: dict | None = None,
        patterns: list[dict] | None = None,  # extra parameter made optional
        file_patterns: list[str] | None = None,  # extra parameter made optional
    ) -> "PatternCheckCriterion":
        """
        Create a new pattern check criterion.

        Args:
            name: Name of the criterion.
            points: Maximum points possible.
            description: Optional description.
            required: Whether this criterion is required to pass.
            category: Ignored (will be set to "patterns").
            rubric: Optional rubric (passed to the base for consistency).
            patterns: List of pattern dicts with keys 'pattern' and 'description'.
            file_patterns: Optional list of file patterns to check.

        Returns:
            New pattern check criterion instance.
        """
        if patterns is None:
            raise ValueError("patterns must be provided")
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            description=description
            or f"Check for code patterns in {file_patterns or ['*.py']} files",
            points=points,
            required=required,
            category="patterns",
            rubric=rubric,
            patterns=patterns,
            file_patterns=file_patterns or ["*.py"],
        )


class GradingCriteria(BaseModel):
    """A collection of grading criteria for an assignment."""

    id: str = Field(description="Unique identifier for the criteria set")
    name: str = Field(description="Name of the criteria set")
    assignment_id: str = Field(description="ID of the associated assignment")
    total_points: float = Field(description="Total points possible across all criteria")
    passing_threshold: float = Field(
        default=0.6, description="Minimum score ratio (0-1) required to pass"
    )
    criteria: list[GradingCriterion] = Field(
        default_factory=list, description="List of grading criteria"
    )

    @model_validator(mode="after")
    def ensure_id(self) -> "GradingCriteria":
        """Ensure the criteria set ID is set, generating one if needed."""
        if not self.id:
            self.id = str(uuid.uuid4())
        return self

    @classmethod
    def create(
        cls,
        name: str,
        assignment_id: str,
        criteria: list[GradingCriterion] | None = None,
        passing_threshold: float = 0.6,
    ) -> "GradingCriteria":
        """
        Create a new grading criteria set.

        Args:
            name: Name of the criteria set
            assignment_id: ID of the associated assignment
            criteria: Optional list of grading criteria
            passing_threshold: Minimum score ratio (0-1) required to pass

        Returns:
            New grading criteria set instance
        """
        criteria_list = criteria or []
        total_points = sum(c.points for c in criteria_list)
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            assignment_id=assignment_id,
            total_points=total_points,
            passing_threshold=passing_threshold,
            criteria=criteria_list,
        )

    def add_criterion(self, criterion: GradingCriterion) -> None:
        """
        Add a grading criterion to the set.

        Args:
            criterion: Criterion to add
        """
        self.criteria.append(criterion)
        self.total_points += criterion.points

    def remove_criterion(self, criterion_id: str) -> bool:
        """
        Remove a grading criterion from the set.

        Args:
            criterion_id: ID of the criterion to remove

        Returns:
            True if the criterion was removed, False if not found
        """
        for i, criterion in enumerate(self.criteria):
            if criterion.id == criterion_id:
                removed = self.criteria.pop(i)
                self.total_points -= removed.points
                return True
        return False

    def get_criterion(self, criterion_id: str) -> GradingCriterion | None:
        """
        Get a criterion by ID.

        Args:
            criterion_id: ID of the criterion to get

        Returns:
            Criterion if found, None otherwise
        """
        for criterion in self.criteria:
            if criterion.id == criterion_id:
                return criterion
        return None

    def get_criteria_by_category(self, category: str) -> list[GradingCriterion]:
        """
        Get criteria by category.

        Args:
            category: Category to filter by

        Returns:
            List of criteria in the category.
        """
        return [
            criterion for criterion in self.criteria if criterion.category == category
        ]


class GradeResult(BaseModel):
    """Result of grading a student submission."""

    id: str = Field(description="Unique identifier for the grade result")
    submission_id: str = Field(description="ID of the graded submission")
    student_id: str = Field(description="ID of the student")
    assignment_id: str = Field(description="ID of the assignment")
    graded_at: datetime = Field(
        default_factory=datetime.now, description="When the submission was graded"
    )
    grader: str | None = Field(default=None, description="ID or name of the grader")
    score: float = Field(description="Total score")
    max_points: float = Field(description="Maximum possible points")
    passed: bool = Field(description="Whether the submission passed")
    criterion_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Scores for individual criteria (criterion ID -> score)",
    )
    comments: str | None = Field(default=None, description="Overall comments")
    criterion_comments: dict[str, str] = Field(
        default_factory=dict,
        description="Comments for individual criteria (criterion ID -> comment)",
    )

    @model_validator(mode="after")
    def ensure_id(self) -> "GradeResult":
        """Ensure the grade result ID is set, generating one if needed."""
        if not self.id:
            self.id = str(uuid.uuid4())
        return self

    @classmethod
    def create(
        cls,
        submission_id: str,
        student_id: str,
        assignment_id: str,
        score: float,
        max_points: float,
        passed: bool,
        criterion_scores: dict[str, float] | None = None,
        grader: str | None = None,
        comments: str | None = None,
        criterion_comments: dict[str, str] | None = None,
    ) -> "GradeResult":
        """
        Create a new grade result.

        Args:
            submission_id: ID of the graded submission
            student_id: ID of the student
            assignment_id: ID of the assignment
            score: Total score
            max_points: Maximum possible points
            passed: Whether the submission passed
            criterion_scores: Optional scores for individual criteria
            grader: Optional ID or name of the grader
            comments: Optional overall comments
            criterion_comments: Optional comments for individual criteria

        Returns:
            New grade result instance.
        """
        return cls(
            id=str(uuid.uuid4()),
            submission_id=submission_id,
            student_id=student_id,
            assignment_id=assignment_id,
            score=score,
            max_points=max_points,
            passed=passed,
            criterion_scores=criterion_scores or {},
            grader=grader,
            comments=comments,
            criterion_comments=criterion_comments or {},
        )

    def format_for_feedback(self) -> str:
        """
        Format the grade result for feedback.

        Returns:
            Formatted text for feedback.
        """
        lines = [
            f"# Grade: {self.score:.1f}/{self.max_points} ({(self.score / self.max_points) * 100:.1f}%)",
            f"**Result: {'PASS' if self.passed else 'FAIL'}**\n",
        ]
        if self.comments:
            lines.append("## Overall Comments\n")
            lines.append(self.comments)
            lines.append("")
        if self.criterion_scores:
            lines.append("## Criterion Scores\n")
            for criterion_id, score in self.criterion_scores.items():
                comment = self.criterion_comments.get(criterion_id, "")
                lines.append(f"### {criterion_id}")
                lines.append(f"**Score: {score}**")
                if comment:
                    lines.append(f"\n{comment}")
                lines.append("")
        return "\n".join(lines)

    def update_gamification(self) -> None:
        """Update gamification based on this grade result."""
        try:
            # Import here to avoid circular imports
            from quackster.core.gamification_service import GamificationService
            from quackster.core.models import XPEvent

            # Create a gamification service
            gamifier = GamificationService()

            # Create an XP event for the grade
            # Scale XP based on score - between 10 and 50 points
            score_ratio = self.score / self.max_points if self.max_points > 0 else 0
            xp_points = int(10 + score_ratio * 40)

            event = XPEvent(
                id=f"academy-grade-{self.id}",
                label=f"Graded assignment score: {self.score}/{self.max_points}",
                points=xp_points,
                metadata={
                    "assignment_id": self.assignment_id,
                    "submission_id": self.submission_id,
                    "score": self.score,
                    "max_score": self.max_points,
                    "passed": self.passed,
                },
            )

            # Handle the event
            result = gamifier.handle_event(event)

            # Log the result
            if result.message:
                logger.info(result.message)

        except Exception as e:
            logger.debug(f"Error integrating grade with gamification: {str(e)}")
