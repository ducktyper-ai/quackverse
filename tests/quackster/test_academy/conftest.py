# tests/quackster/test_academy/conftest.py
"""
Fixtures for testing the QuackCore quackster academy module.
"""

import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from quackcore.integrations.github.models import GitHubRepo
from quackster.academy.assignment import Assignment, AssignmentType
from quackster.academy.context import (
    GitHubConfig,
    TeachingConfig,
    TeachingContext,
)
from quackster.academy.course import Course, CourseModule, ItemType, ModuleItem
from quackster.academy.feedback import (
    Annotation,
    AnnotationType,
    Feedback,
    FeedbackItem,
    FeedbackItemType,
)
from quackster.academy.grading import (
    GradeResult,
    GradingCriteria,
    GradingCriterion,
)
from quackster.academy.results import TeachingResult
from quackster.academy.student import Student, StudentSubmission


# Mock GitHub integration
class MockGitHub:
    """Mock GitHub integration for testing."""

    def __init__(self, success=True, error=None):
        self.success = success
        self.error = error
        self.client = MagicMock()
        self.repos = {}
        self.prs = {}

    def get_repo(self, repo_name):
        """Mock getting a repository."""
        if not self.success:
            return TeachingResult(success=False, error=self.error or "Mocked error")

        if repo_name in self.repos:
            return TeachingResult(success=True, content=self.repos[repo_name])

        # Create a mock repo for testing
        repo = GitHubRepo(
            id=str(uuid.uuid4()),
            name=repo_name.split("/")[-1],
            full_name=repo_name,
            html_url=f"https://github.com/{repo_name}",
            description=f"Mock repo for {repo_name}",
            private=True,
            fork=False,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            pushed_at=datetime.now().isoformat(),
            default_branch="main",
        )
        self.repos[repo_name] = repo
        return TeachingResult(success=True, content=repo)


@pytest.fixture
def mock_github():
    """Create a mock GitHub integration."""
    return MockGitHub()


@pytest.fixture
def mock_fs():
    """Mock QuackCore FS _operations."""
    with patch("quackcore.fs.service") as mock_fs:
        # Setup read_yaml and write_yaml mocks
        mock_fs.read_yaml.return_value = MagicMock(success=True, data={})
        mock_fs.write_yaml.return_value = MagicMock(success=True)
        mock_fs.expand_user_vars.side_effect = lambda x: x
        mock_fs.create_directory.return_value = MagicMock(success=True)
        mock_fs.join_path.side_effect = lambda base, path: os.path.join(base, path)
        yield mock_fs


@pytest.fixture
def mock_resolver():
    """Mock QuackCore Paths resolver."""
    with patch("quackcore.paths.resolver") as mock_resolver:
        mock_resolver.get_project_root.return_value = Path("/mock/project/root")
        yield mock_resolver


@pytest.fixture
def mock_logger():
    """Mock QuackCore logger."""
    with patch("quackcore.logging.get_logger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        yield mock_logger


@pytest.fixture
def mock_integration_registry():
    """Mock QuackCore integration registry."""
    with patch("quackcore.integrations.core.registry") as mock_registry:
        # Create mock GitHub integration
        mock_github_integration = MockGitHub()
        mock_registry.get_integration.return_value = mock_github_integration
        yield mock_registry


@pytest.fixture
def mock_gamification_service():
    """Mock GamificationService."""
    with patch(
        "quackster.core.gamification_service.GamificationService"
    ) as mock_gamification:
        mock_service = MagicMock()
        mock_service.handle_module_completion.return_value = MagicMock(
            success=True, message="Module completed"
        )
        mock_service.handle_course_completion.return_value = MagicMock(
            success=True, message="Course completed"
        )
        mock_service.handle_assignment_completion.return_value = MagicMock(
            success=True, message="Assignment completed"
        )
        mock_service.handle_feedback_submission.return_value = MagicMock(
            success=True, message="Feedback submitted"
        )
        mock_service.handle_github_pr_submission.return_value = MagicMock(
            success=True, message="PR submitted"
        )
        mock_service.handle_event.return_value = MagicMock(
            success=True, message="Event handled"
        )

        mock_gamification.return_value = mock_service
        yield mock_gamification


@pytest.fixture
def teaching_config():
    """Create a quackster configuration."""
    return TeachingConfig(
        course_name="Test Course",
        course_id="test-course",
        github=GitHubConfig(organization="test-org", auto_create_repos=True),
        assignments_dir="assignments",
        feedback_dir="feedback",
        grading_dir="grading",
        submissions_dir="submissions",
        students_file="students.yaml",
        course_config_file="course.yaml",
    )


@pytest.fixture
def teaching_context(
    teaching_config, mock_fs, mock_resolver, mock_integration_registry, temp_dir
):
    """Create a quackster context."""
    context = TeachingContext(teaching_config, temp_dir)
    return context


@pytest.fixture
def sample_course():
    """Create a sample course."""
    module1 = CourseModule.create(
        title="Module 1: Introduction",
        description="Introduction to the course",
        position=0,
        items=[
            ModuleItem.create(
                title="Welcome Lecture",
                type=ItemType.LECTURE,
                description="Welcome to the course",
            ),
            ModuleItem.create(
                title="Assignment 1",
                type=ItemType.ASSIGNMENT,
                description="First assignment",
                assignment_id="assignment-1",
                due_date=datetime.now() + timedelta(days=7),
                points=100.0,
            ),
        ],
    )

    module2 = CourseModule.create(
        title="Module 2: Advanced Topics",
        description="Advanced topics in the course",
        position=1,
        items=[
            ModuleItem.create(
                title="Advanced Lecture",
                type=ItemType.LECTURE,
                description="Advanced topics lecture",
            ),
            ModuleItem.create(
                title="Assignment 2",
                type=ItemType.ASSIGNMENT,
                description="Second assignment",
                assignment_id="assignment-2",
                due_date=datetime.now() + timedelta(days=14),
                points=100.0,
            ),
        ],
    )

    course = Course.create(
        name="Test Course",
        code="TEST101",
        description="A test course",
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=90),
        instructors=["test-instructor"],
    )

    course.add_module(module1)
    course.add_module(module2)

    return course


@pytest.fixture
def sample_assignment():
    """Create a sample assignment."""
    return Assignment.create(
        name="Test Assignment",
        description="A test assignment",
        assignment_type=AssignmentType.INDIVIDUAL,
        due_date=datetime.now() + timedelta(days=7),
        points=100.0,
    )


@pytest.fixture
def sample_student():
    """Create a sample student."""
    return Student.create(
        github_username="test-student", name="Test Student", email="test@example.com"
    )


@pytest.fixture
def sample_submission(sample_student, sample_assignment):
    """Create a sample submission."""
    submission = StudentSubmission.create(
        student_id=sample_student.id, assignment_id=sample_assignment.id
    )
    return submission


@pytest.fixture
def sample_grading_criteria():
    """Create sample grading criteria."""
    criterion1 = GradingCriterion.create(
        name="Code Quality",
        points=40.0,
        description="Quality of the code",
        category="quality",
    )

    criterion2 = GradingCriterion.create(
        name="Functionality",
        points=60.0,
        description="Functionality of the solution",
        category="functionality",
        required=True,
    )

    criteria = GradingCriteria.create(
        name="Assignment Criteria",
        assignment_id="test-assignment",
        criteria=[criterion1, criterion2],
        passing_threshold=0.7,
    )

    return criteria


@pytest.fixture
def sample_grade_result(sample_student, sample_assignment):
    """Create a sample grade result."""
    return GradeResult.create(
        submission_id="test-submission",
        student_id=sample_student.id,
        assignment_id=sample_assignment.id,
        score=85.0,
        max_points=100.0,
        passed=True,
        criterion_scores={"criterion1": 35.0, "criterion2": 50.0},
        comments="Good work overall",
    )


@pytest.fixture
def sample_feedback(sample_student, sample_assignment):
    """Create sample feedback."""
    annotation = Annotation.create(
        file_path="test_file.py",
        line_start=10,
        text="Consider using a more descriptive variable name",
        type=AnnotationType.SUGGESTION,
        suggestion="user_count = len(users)",
    )

    feedback_item = FeedbackItem.create(
        text="Your code is well-structured but could use more descriptive variable names",
        type=FeedbackItemType.CODE_QUALITY,
        score=8.5,
        annotations=[annotation],
    )

    feedback = Feedback.create(
        submission_id="test-submission",
        student_id=sample_student.id,
        assignment_id=sample_assignment.id,
        score=85.0,
        summary="Good work overall with some minor suggestions for improvement",
    )

    feedback.add_item(feedback_item)

    return feedback
