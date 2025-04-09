# src/quackcore/integrations/github/models.py
"""GitHub integration data models for QuackCore."""

from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, HttpUrl


class PullRequestStatus(str, Enum):
    """Status of a pull request."""
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


class GitHubUser(BaseModel):
    """Model representing a GitHub user."""
    username: str = Field(description="GitHub username")
    url: HttpUrl = Field(description="GitHub profile URL")
    name: str | None = Field(default=None, description="User's full name if available")
    email: str | None = Field(default=None, description="User's email if available")
    avatar_url: HttpUrl | None = Field(default=None, description="URL to user's avatar")


class GitHubRepo(BaseModel):
    """Model representing a GitHub repository."""
    name: str = Field(description="Repository name without owner")
    full_name: str = Field(description="Full repository name with owner (owner/repo)")
    url: HttpUrl = Field(description="Repository URL")
    clone_url: HttpUrl = Field(description="Git clone URL")
    default_branch: str = Field(default="main", description="Default branch")
    description: str | None = Field(default=None, description="Repository description")
    fork: bool = Field(default=False, description="Whether this repo is a fork")
    forks_count: int = Field(default=0, description="Number of forks")
    stargazers_count: int = Field(default=0, description="Number of stars")
    owner: GitHubUser = Field(description="Repository owner")


class PullRequest(BaseModel):
    """Model representing a GitHub pull request."""
    number: int = Field(description="Pull request number")
    title: str = Field(description="Pull request title")
    url: HttpUrl = Field(description="Pull request URL")
    author: GitHubUser = Field(description="Pull request author")
    status: PullRequestStatus = Field(description="Pull request status")
    body: str | None = Field(default=None, description="Pull request body")
    created_at: datetime = Field(description="Pull request creation date")
    updated_at: datetime = Field(description="Last update date")
    merged_at: datetime | None = Field(default=None, description="Merge date if merged")
    base_repo: str = Field(description="Base repository full name")
    head_repo: str = Field(description="Head repository full name")
    base_branch: str = Field(description="Base branch")
    head_branch: str = Field(description="Head branch")


class GradeResult(BaseModel):
    """Model representing the result of grading a submission."""
    score: float = Field(description="Score between 0.0 and 1.0")
    passed: bool = Field(description="Whether the submission passed")
    comments: str = Field(description="Feedback comments")
    details: dict[str, Any] = Field(default_factory=dict,
                                    description="Detailed grading information")