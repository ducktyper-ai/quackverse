# quackster/src/quackster/github/models.py

"""GitHub integration data models for QuackCore."""

from typing import Any

from pydantic import BaseModel, Field


class GradeResult(BaseModel):
    """Model representing the result of grading a submission."""

    score: float = Field(description="Score between 0.0 and 1.0")
    passed: bool = Field(description="Whether the submission passed")
    comments: str = Field(description="Feedback comments")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Detailed grading information"
    )
