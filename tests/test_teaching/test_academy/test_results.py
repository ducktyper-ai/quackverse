# tests/test_teaching/test_academy/test_results.py
"""
Tests for the Results module.
"""

from quackcore.integrations.github.models import GitHubRepo, PullRequest
from quackcore.teaching.academy.results import (
    AssignmentResult,
    CourseResult,
    FeedbackResult,
    StudentResult,
    SubmissionResult,
    TeachingResult,
)


class TestTeachingResult:
    """Tests for the TeachingResult class."""

    def test_init(self):
        """Test initialization of TeachingResult."""
        # Basic init with success
        result = TeachingResult(success=True)
        assert result.success is True
        assert result.message == ""
        assert result.error is None
        assert result.content is None

        # Init with all fields
        result = TeachingResult(
            success=False,
            message="Operation failed",
            error="Error details",
            content={"key": "value"},
        )
        assert result.success is False
        assert result.message == "Operation failed"
        assert result.error == "Error details"
        assert result.content == {"key": "value"}

    def test_bool_conversion(self):
        """Test boolean conversion of TeachingResult."""
        # Success should be True
        result = TeachingResult(success=True)
        assert bool(result) is True

        # Failure should be False
        result = TeachingResult(success=False)
        assert bool(result) is False


class TestAssignmentResult:
    """Tests for the AssignmentResult class."""

    def test_init(self):
        """Test initialization of AssignmentResult."""
        # Basic init with success
        result = AssignmentResult(success=True)
        assert result.success is True
        assert result.message == ""
        assert result.error is None
        assert result.content is None
        assert result.repositories == []
        assert result.failed_students == []

        # Init with all fields
        repo1 = GitHubRepo(id="repo1", name="repo1")
        repo2 = GitHubRepo(id="repo2", name="repo2")

        result = AssignmentResult(
            success=False,
            message="Assignment creation partially failed",
            error="Some repositories could not be created",
            content={"key": "value"},
            repositories=[repo1, repo2],
            failed_students=["student3", "student4"],
        )
        assert result.success is False
        assert result.message == "Assignment creation partially failed"
        assert result.error == "Some repositories could not be created"
        assert result.content == {"key": "value"}
        assert result.repositories == [repo1, repo2]
        assert result.failed_students == ["student3", "student4"]


class TestSubmissionResult:
    """Tests for the SubmissionResult class."""

    def test_init(self):
        """Test initialization of SubmissionResult."""
        # Basic init with success
        result = SubmissionResult(success=True)
        assert result.success is True
        assert result.message == ""
        assert result.error is None
        assert result.content is None
        assert result.pull_request is None
        assert result.student_github is None
        assert result.assignment_id is None

        # Init with all fields
        pr = PullRequest(id=1, number=42, title="Test PR")

        result = SubmissionResult(
            success=True,
            message="Submission successful",
            error=None,
            content={"key": "value"},
            pull_request=pr,
            student_github="student1",
            assignment_id="assignment-1",
        )
        assert result.success is True
        assert result.message == "Submission successful"
        assert result.error is None
        assert result.content == {"key": "value"}
        assert result.pull_request == pr
        assert result.student_github == "student1"
        assert result.assignment_id == "assignment-1"


class TestFeedbackResult:
    """Tests for the FeedbackResult class."""

    def test_init(self):
        """Test initialization of FeedbackResult."""
        # Basic init with success
        result = FeedbackResult(success=True)
        assert result.success is True
        assert result.message == ""
        assert result.error is None
        assert result.content is None
        assert result.feedback_id is None
        assert result.submission_id is None
        assert result.score is None

        # Init with all fields
        result = FeedbackResult(
            success=True,
            message="Feedback provided",
            error=None,
            content={"key": "value"},
            feedback_id="feedback-1",
            submission_id="submission-1",
            score=85.0,
        )
        assert result.success is True
        assert result.message == "Feedback provided"
        assert result.error is None
        assert result.content == {"key": "value"}
        assert result.feedback_id == "feedback-1"
        assert result.submission_id == "submission-1"
        assert result.score == 85.0


class TestStudentResult:
    """Tests for the StudentResult class."""

    def test_init(self):
        """Test initialization of StudentResult."""
        # Basic init with success
        result = StudentResult(success=True)
        assert result.success is True
        assert result.message == ""
        assert result.error is None
        assert result.content is None
        assert result.student_id is None
        assert result.github_username is None

        # Init with all fields
        result = StudentResult(
            success=True,
            message="Student operation successful",
            error=None,
            content={"key": "value"},
            student_id="student-1",
            github_username="student1",
        )
        assert result.success is True
        assert result.message == "Student operation successful"
        assert result.error is None
        assert result.content == {"key": "value"}
        assert result.student_id == "student-1"
        assert result.github_username == "student1"


class TestCourseResult:
    """Tests for the CourseResult class."""

    def test_init(self):
        """Test initialization of CourseResult."""
        # Basic init with success
        result = CourseResult(success=True)
        assert result.success is True
        assert result.message == ""
        assert result.error is None
        assert result.content is None
        assert result.course_id is None
        assert result.course_name is None

        # Init with all fields
        result = CourseResult(
            success=True,
            message="Course operation successful",
            error=None,
            content={"key": "value"},
            course_id="course-1",
            course_name="Python 101",
        )
        assert result.success is True
        assert result.message == "Course operation successful"
        assert result.error is None
        assert result.content == {"key": "value"}
        assert result.course_id == "course-1"
        assert result.course_name == "Python 101"
