# src/quackcore/integrations/github/operations/__init__.py
"""GitHub API operations."""

from .repositories import (
    get_repo,
    star_repo,
    unstar_repo,
    is_repo_starred,
    fork_repo,
    check_repository_exists,
    get_repository_file_content,
    update_repository_file
)
from .users import get_user
from .pull_requests import (
    create_pull_request,
    list_pull_requests,
    get_pull_request
)
from .issues import (
    create_issue,
    list_issues,
    get_issue,
    add_issue_comment
)

__all__ = [
    # Repository operations
    "get_repo",
    "star_repo",
    "unstar_repo",
    "is_repo_starred",
    "fork_repo",
    "check_repository_exists",
    "get_repository_file_content",
    "update_repository_file",

    # User operations
    "get_user",

    # Pull request operations
    "create_pull_request",
    "list_pull_requests",
    "get_pull_request",

    # Issue operations
    "create_issue",
    "list_issues",
    "get_issue",
    "add_issue_comment",
]