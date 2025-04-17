# tests/quackster/test_academy/test_feedback.py
"""
Tests for the Feedback module.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from quackster.academy.feedback import (
    Annotation,
    AnnotationType,
    Feedback,
    FeedbackItem,
    FeedbackItemType,
    FeedbackManager,
)


class TestAnnotation:
    """Tests for the Annotation class."""

    def test_create(self):
        """Test creating an annotation."""
        # Basic create
        annotation = Annotation.create(
            file_path="main.py",
            line_start=10,
            text="Consider using a more descriptive variable name",
        )

        assert annotation.file_path == "main.py"
        assert annotation.line_start == 10
        assert annotation.text == "Consider using a more descriptive variable name"
        assert annotation.id is not None
        assert annotation.type == AnnotationType.COMMENT  # Default
        assert annotation.line_end is None
        assert annotation.column_start is None
        assert annotation.column_end is None
        assert annotation.code_snippet is None
        assert annotation.suggestion is None

        # Create with optional fields
        annotation = Annotation.create(
            file_path="main.py",
            line_start=10,
            text="Consider using a more descriptive variable name",
            type=AnnotationType.SUGGESTION,
            line_end=12,
            suggestion="user_count = len(users)",
        )

        assert annotation.file_path == "main.py"
        assert annotation.line_start == 10
        assert annotation.text == "Consider using a more descriptive variable name"
        assert annotation.id is not None
        assert annotation.type == AnnotationType.SUGGESTION
        assert annotation.line_end == 12
        assert annotation.suggestion == "user_count = len(users)"

    def test_ensure_id(self):
        """Test that ID is generated if not provided."""
        # Create with no ID
        annotation = Annotation(
            file_path="main.py", line_start=10, text="Test annotation"
        )
        assert annotation.id is not None

        # Create with provided ID
        annotation = Annotation(
            id="custom-id", file_path="main.py", line_start=10, text="Test annotation"
        )
        assert annotation.id == "custom-id"

    def test_format_for_github_pr(self):
        """Test formatting annotation for GitHub PR comment."""
        # Test comment annotation
        annotation = Annotation.create(
            file_path="main.py",
            line_start=10,
            text="This is a comment",
            type=AnnotationType.COMMENT,
        )

        formatted = annotation.format_for_github_pr()
        assert formatted == "**COMMENT**: This is a comment"

        # Test suggestion annotation
        annotation = Annotation.create(
            file_path="main.py",
            line_start=10,
            text="Consider using a more descriptive variable name",
            type=AnnotationType.SUGGESTION,
            suggestion="user_count = len(users)",
        )

        formatted = annotation.format_for_github_pr()
        assert formatted.startswith(
            "**SUGGESTION**: Consider using a more descriptive variable name"
        )
        assert "```suggestion" in formatted
        assert "user_count = len(users)" in formatted

        # Test other annotation types
        annotation = Annotation.create(
            file_path="main.py",
            line_start=10,
            text="Warning message",
            type=AnnotationType.WARNING,
        )

        formatted = annotation.format_for_github_pr()
        assert formatted == "**WARNING**: Warning message"


class TestFeedbackItem:
    """Tests for the FeedbackItem class."""

    def test_create(self):
        """Test creating a feedback item."""
        # Basic create
        feedback_item = FeedbackItem.create(
            text="Your code is well-structured but could use more comments"
        )

        assert (
            feedback_item.text
            == "Your code is well-structured but could use more comments"
        )
        assert feedback_item.id is not None
        assert feedback_item.type == FeedbackItemType.GENERAL  # Default
        assert feedback_item.score is None
        assert feedback_item.annotations == []

        # Create with optional fields
        annotation = Annotation.create(
            file_path="main.py", line_start=10, text="Add a comment here"
        )

        feedback_item = FeedbackItem.create(
            text="Your code needs more comments",
            type=FeedbackItemType.DOCUMENTATION,
            score=8.5,
            annotations=[annotation],
        )

        assert feedback_item.text == "Your code needs more comments"
        assert feedback_item.id is not None
        assert feedback_item.type == FeedbackItemType.DOCUMENTATION
        assert feedback_item.score == 8.5
        assert len(feedback_item.annotations) == 1
        assert feedback_item.annotations[0] == annotation

    def test_ensure_id(self):
        """Test that ID is generated if not provided."""
        # Create with no ID
        feedback_item = FeedbackItem(text="Test feedback")
        assert feedback_item.id is not None

        # Create with provided ID
        feedback_item = FeedbackItem(id="custom-id", text="Test feedback")
        assert feedback_item.id == "custom-id"

    def test_add_annotation(self):
        """Test adding an annotation to a feedback item."""
        feedback_item = FeedbackItem.create(
            text="Your code is well-structured but could use more comments"
        )
        assert len(feedback_item.annotations) == 0

        # Add an annotation
        annotation = Annotation.create(
            file_path="main.py", line_start=10, text="Add a comment here"
        )
        feedback_item.add_annotation(annotation)

        assert len(feedback_item.annotations) == 1
        assert feedback_item.annotations[0] == annotation


class TestFeedback:
    """Tests for the Feedback class."""

    def test_create(self):
        """Test creating feedback."""
        # Basic create
        feedback = Feedback.create(
            submission_id="submission-1",
            student_id="student-1",
            assignment_id="assignment-1",
        )

        assert feedback.submission_id == "submission-1"
        assert feedback.student_id == "student-1"
        assert feedback.assignment_id == "assignment-1"
        assert feedback.id is not None
        assert feedback.created_at is not None
        assert feedback.updated_at is not None
        assert feedback.score is None
        assert feedback.summary is None
        assert feedback.items == []
        assert feedback.status == "draft"
        assert feedback.reviewer is None

        # Create with optional fields
        feedback = Feedback.create(
            submission_id="submission-1",
            student_id="student-1",
            assignment_id="assignment-1",
            score=85.0,
            summary="Overall good work with some areas for improvement",
            reviewer="instructor-1",
        )

        assert feedback.submission_id == "submission-1"
        assert feedback.student_id == "student-1"
        assert feedback.assignment_id == "assignment-1"
        assert feedback.id is not None
        assert feedback.created_at is not None
        assert feedback.updated_at is not None
        assert feedback.score == 85.0
        assert feedback.summary == "Overall good work with some areas for improvement"
        assert feedback.items == []
        assert feedback.status == "draft"
        assert feedback.reviewer == "instructor-1"

    def test_ensure_id(self):
        """Test that ID is generated if not provided."""
        # Create with no ID
        feedback = Feedback(
            submission_id="submission-1",
            student_id="student-1",
            assignment_id="assignment-1",
        )
        assert feedback.id is not None

        # Create with provided ID
        feedback = Feedback(
            id="custom-id",
            submission_id="submission-1",
            student_id="student-1",
            assignment_id="assignment-1",
        )
        assert feedback.id == "custom-id"

    def test_add_item(self):
        """Test adding a feedback item."""
        feedback = Feedback.create(
            submission_id="submission-1",
            student_id="student-1",
            assignment_id="assignment-1",
        )

        original_updated_at = feedback.updated_at

        # Wait a moment to ensure updated_at changes
        import time

        time.sleep(0.001)

        # Add an item
        feedback_item = FeedbackItem.create(
            text="Your code is well-structured but could use more comments"
        )
        feedback.add_item(feedback_item)

        assert len(feedback.items) == 1
        assert feedback.items[0] == feedback_item
        assert feedback.updated_at > original_updated_at

    def test_set_status(self):
        """Test setting feedback status."""
        feedback = Feedback.create(
            submission_id="submission-1",
            student_id="student-1",
            assignment_id="assignment-1",
        )
        assert feedback.status == "draft"

        original_updated_at = feedback.updated_at

        # Wait a moment to ensure updated_at changes
        import time

        time.sleep(0.001)

        # Set status
        feedback.set_status("reviewed")

        assert feedback.status == "reviewed"
        assert feedback.updated_at > original_updated_at

    def test_format_for_github_pr(self):
        """Test formatting feedback for GitHub PR comment."""
        # Create feedback with score and summary
        feedback = Feedback.create(
            submission_id="submission-1",
            student_id="student-1",
            assignment_id="assignment-1",
            score=85.0,
            summary="Overall good work with some areas for improvement",
        )

        # Add feedback items
        item1 = FeedbackItem.create(
            text="Your code is well-structured",
            type=FeedbackItemType.CODE_QUALITY,
            score=9.0,
        )

        item2 = FeedbackItem.create(
            text="Could use more comments",
            type=FeedbackItemType.DOCUMENTATION,
            score=7.5,
        )

        feedback.add_item(item1)
        feedback.add_item(item2)

        # Format for GitHub PR
        formatted = feedback.format_for_github_pr()

        # Verify formatted text includes essential information
        assert "# Feedback: 85.0/100" in formatted
        assert "## Summary" in formatted
        assert "Overall good work with some areas for improvement" in formatted
        assert "## Detailed Feedback" in formatted
        assert "1. Code quality (9.0 points)" in formatted
        assert "2. Documentation (7.5 points)" in formatted
        assert "Your code is well-structured" in formatted
        assert "Could use more comments" in formatted

    def test_calculate_score(self):
        """Test calculating overall score from feedback items."""
        feedback = Feedback.create(
            submission_id="submission-1",
            student_id="student-1",
            assignment_id="assignment-1",
        )

        # Add feedback items with scores
        item1 = FeedbackItem.create(text="Item 1", score=35.0)

        item2 = FeedbackItem.create(text="Item 2", score=45.0)

        item3 = FeedbackItem.create(
            text="Item 3 (no score)"  # No score
        )

        feedback.add_item(item1)
        feedback.add_item(item2)
        feedback.add_item(item3)

        # Calculate score
        original_updated_at = feedback.updated_at

        # Wait a moment to ensure updated_at changes
        import time

        time.sleep(0.001)

        score = feedback.calculate_score()

        assert score == 80.0  # 35.0 + 45.0
        assert feedback.score == 80.0
        assert feedback.updated_at > original_updated_at

    def test_calculate_score_no_scored_items(self):
        """Test calculating score when no items have scores."""
        feedback = Feedback.create(
            submission_id="submission-1",
            student_id="student-1",
            assignment_id="assignment-1",
        )

        # Add feedback items without scores
        item1 = FeedbackItem.create(text="Item 1 (no score)")

        item2 = FeedbackItem.create(text="Item 2 (no score)")

        feedback.add_item(item1)
        feedback.add_item(item2)

        # Calculate score
        score = feedback.calculate_score()

        assert score is None
        assert feedback.score is None

    def test_update_gamification(self, mock_gamification_service):
        """Test updating gamification based on feedback."""
        feedback = Feedback.create(
            submission_id="submission-1",
            student_id="student-1",
            assignment_id="assignment-1",
        )

        # Update gamification
        feedback.update_gamification()

        # Verify GamificationService.handle_feedback_submission was called
        mock_gamification_service.return_value.handle_feedback_submission.assert_called_once_with(
            feedback.id, "Feedback for submission submission-1"
        )

    def test_update_gamification_error(self, mock_gamification_service, mock_logger):
        """Test update_gamification when an error occurs."""
        feedback = Feedback.create(
            submission_id="submission-1",
            student_id="student-1",
            assignment_id="assignment-1",
        )

        # Mock handle_feedback_submission to raise an exception
        mock_gamification_service.return_value.handle_feedback_submission.side_effect = Exception(
            "Gamification error"
        )

        # Should not raise an exception
        feedback.update_gamification()

        # Should log error
        assert any(
            "Error integrating feedback with gamification" in str(call)
            for call in mock_logger.debug.call_args_list
        )


class TestFeedbackManager:
    """Tests for the FeedbackManager class."""

    def test_init(self):
        """Test initialization of FeedbackManager."""
        manager = FeedbackManager()
        assert manager.feedback == {}
        assert manager.by_submission == {}

    def test_add_feedback(self):
        """Test adding feedback."""
        manager = FeedbackManager()
        feedback = Feedback.create(
            submission_id="submission-1",
            student_id="student-1",
            assignment_id="assignment-1",
        )

        manager.add_feedback(feedback)

        assert feedback.id in manager.feedback
        assert manager.feedback[feedback.id] == feedback
        assert "submission-1" in manager.by_submission
        assert manager.by_submission["submission-1"] == feedback

    def test_get_feedback(self):
        """Test getting feedback by ID."""
        manager = FeedbackManager()
        feedback = Feedback.create(
            submission_id="submission-1",
            student_id="student-1",
            assignment_id="assignment-1",
        )

        manager.add_feedback(feedback)

        # Get existing feedback
        result = manager.get_feedback(feedback.id)
        assert result == feedback

        # Get non-existent feedback
        result = manager.get_feedback("non-existent")
        assert result is None

    def test_get_feedback_by_submission(self):
        """Test getting feedback by submission ID."""
        manager = FeedbackManager()
        feedback = Feedback.create(
            submission_id="submission-1",
            student_id="student-1",
            assignment_id="assignment-1",
        )

        manager.add_feedback(feedback)

        # Get existing feedback
        result = manager.get_feedback_by_submission("submission-1")
        assert result == feedback

        # Get non-existent feedback
        result = manager.get_feedback_by_submission("non-existent")
        assert result is None

    def test_add_multiple_feedback(self):
        """Test adding multiple feedback items."""
        manager = FeedbackManager()

        feedback1 = Feedback.create(
            submission_id="submission-1",
            student_id="student-1",
            assignment_id="assignment-1",
        )

        feedback2 = Feedback.create(
            submission_id="submission-2",
            student_id="student-2",
            assignment_id="assignment-2",
        )

        manager.add_multiple_feedback([feedback1, feedback2])

        assert len(manager.feedback) == 2
        assert feedback1.id in manager.feedback
        assert feedback2.id in manager.feedback
        assert "submission-1" in manager.by_submission
        assert "submission-2" in manager.by_submission

    def test_remove_feedback(self):
        """Test removing feedback."""
        manager = FeedbackManager()

        feedback1 = Feedback.create(
            submission_id="submission-1",
            student_id="student-1",
            assignment_id="assignment-1",
        )

        feedback2 = Feedback.create(
            submission_id="submission-2",
            student_id="student-2",
            assignment_id="assignment-2",
        )

        manager.add_feedback(feedback1)
        manager.add_feedback(feedback2)

        # Remove existing feedback
        result = manager.remove_feedback(feedback1.id)
        assert result is True
        assert feedback1.id not in manager.feedback
        assert "submission-1" not in manager.by_submission
        assert feedback2.id in manager.feedback
        assert "submission-2" in manager.by_submission

        # Remove non-existent feedback
        result = manager.remove_feedback("non-existent")
        assert result is False
        assert len(manager.feedback) == 1

    def test_resolve_file_path_absolute(self):
        """Test _resolve_file_path with absolute path."""
        path = "/absolute/path"
        resolved = FeedbackManager._resolve_file_path(path)
        assert resolved == Path(path)

    def test_resolve_file_path_relative(self, mock_resolver):
        """Test _resolve_file_path with relative path."""
        mock_resolver._get_project_root.return_value = Path("/project/root")

        path = "relative/path"
        resolved = FeedbackManager._resolve_file_path(path)
        assert resolved == Path("/project/root/relative/path")

    def test_resolve_file_path_relative_no_project_root(self, mock_resolver):
        """Test _resolve_file_path with relative path when project root fails."""
        mock_resolver._get_project_root.side_effect = Exception(
            "Project root not found"
        )

        with patch("pathlib.Path.resolve") as mock_resolve:
            mock_resolve.return_value = Path("/resolved/path")

            path = "relative/path"
            resolved = FeedbackManager._resolve_file_path(path)
            assert str(resolved).startswith("/resolved/")

    def test_load_from_file(self, mock_fs):
        """Test loading feedback from a file."""
        file_path = "/path/to/feedback.yaml"

        # Mock read_yaml to return success with feedback data
        feedback_data = {
            "feedback": [
                {
                    "id": "feedback-1",
                    "submission_id": "submission-1",
                    "student_id": "student-1",
                    "assignment_id": "assignment-1",
                    "created_at": "2023-01-01T12:00:00",
                    "updated_at": "2023-01-01T12:30:00",
                    "score": 85.0,
                    "summary": "Overall good work",
                    "status": "reviewed",
                    "reviewer": "instructor-1",
                    "items": [
                        {
                            "id": "item-1",
                            "type": "CODE_QUALITY",
                            "text": "Good code structure",
                            "score": 85.0,
                            "annotations": [
                                {
                                    "id": "annotation-1",
                                    "type": "COMMENT",
                                    "file_path": "main.py",
                                    "line_start": 10,
                                    "text": "Nice work here",
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        mock_fs.read_yaml.return_value = MagicMock(success=True, data=feedback_data)

        # Load from file
        with patch.object(FeedbackManager, "_resolve_file_path") as mock_resolve:
            mock_resolve.return_value = Path(file_path)
            manager = FeedbackManager.load_from_file(file_path)

            # Verify feedback was loaded
            assert len(manager.feedback) == 1
            assert "feedback-1" in manager.feedback
            assert "submission-1" in manager.by_submission

            # Verify feedback details
            feedback = manager.feedback["feedback-1"]
            assert feedback.id == "feedback-1"
            assert feedback.submission_id == "submission-1"
            assert feedback.student_id == "student-1"
            assert feedback.assignment_id == "assignment-1"
            assert feedback.score == 85.0
            assert feedback.summary == "Overall good work"
            assert feedback.status == "reviewed"
            assert feedback.reviewer == "instructor-1"
            assert len(feedback.items) == 1

            # Verify item details
            item = feedback.items[0]
            assert item.id == "item-1"
            assert item.type == FeedbackItemType.CODE_QUALITY
            assert item.text == "Good code structure"
            assert item.score == 85.0
            assert len(item.annotations) == 1

            # Verify annotation details
            annotation = item.annotations[0]
            assert annotation.id == "annotation-1"
            assert annotation.type == AnnotationType.COMMENT
            assert annotation.file_path == "main.py"
            assert annotation.line_start == 10
            assert annotation.text == "Nice work here"

    def test_load_from_file_file_not_found(self, mock_fs):
        """Test loading feedback when file is not found."""
        file_path = "/path/to/feedback.yaml"

        # Mock read_yaml to return failure
        mock_fs.read_yaml.return_value = MagicMock(
            success=False, error="File not found"
        )

        # Load from file should raise FileNotFoundError
        with patch.object(FeedbackManager, "_resolve_file_path") as mock_resolve:
            mock_resolve.return_value = Path(file_path)
            with pytest.raises(FileNotFoundError):
                FeedbackManager.load_from_file(file_path)

    def test_load_from_file_invalid_format(self, mock_fs):
        """Test loading feedback with invalid file format."""
        file_path = "/path/to/feedback.yaml"

        # Mock read_yaml to return success with invalid data
        invalid_data = {"not_feedback": []}
        mock_fs.read_yaml.return_value = MagicMock(success=True, data=invalid_data)

        # Load from file should raise ValueError
        with patch.object(FeedbackManager, "_resolve_file_path") as mock_resolve:
            mock_resolve.return_value = Path(file_path)
            with pytest.raises(ValueError):
                FeedbackManager.load_from_file(file_path)

    def test_load_from_file_feedback_error(self, mock_fs, mock_logger):
        """Test loading feedback with error in feedback data."""
        file_path = "/path/to/feedback.yaml"

        # Mock read_yaml to return success with one invalid feedback
        feedback_data = {
            "feedback": [
                {
                    "id": "feedback-1",
                    "submission_id": "submission-1",
                    "student_id": "student-1",
                    "assignment_id": "assignment-1",
                },
                {
                    # Missing required fields
                    "id": "feedback-2"
                },
            ]
        }
        mock_fs.read_yaml.return_value = MagicMock(success=True, data=feedback_data)

        # Load from file should still work, but log a warning and skip the invalid feedback
        with patch.object(FeedbackManager, "_resolve_file_path") as mock_resolve:
            mock_resolve.return_value = Path(file_path)
            manager = FeedbackManager.load_from_file(file_path)

            # Verify only valid feedback was loaded
            assert len(manager.feedback) == 1
            assert "feedback-1" in manager.feedback
            assert "feedback-2" not in manager.feedback

            # Verify warning was logged
            mock_logger.warning.assert_called_once()

    def test_save_to_file(self, mock_fs):
        """Test saving feedback to a file."""
        file_path = "/path/to/feedback.yaml"

        # Create manager with feedback
        manager = FeedbackManager()
        feedback1 = Feedback.create(
            submission_id="submission-1",
            student_id="student-1",
            assignment_id="assignment-1",
        )
        feedback2 = Feedback.create(
            submission_id="submission-2",
            student_id="student-2",
            assignment_id="assignment-2",
        )
        manager.add_multiple_feedback([feedback1, feedback2])

        # Mock write_yaml to return success
        mock_fs.write_yaml.return_value = MagicMock(success=True)

        # Save to file
        with patch.object(FeedbackManager, "_resolve_file_path") as mock_resolve:
            mock_resolve.return_value = Path(file_path)
            result = manager.save_to_file(file_path)

            # Verify result
            assert result is True

            # Verify write_yaml was called with correct data
            expected_data = {
                "feedback": [feedback1.model_dump(), feedback2.model_dump()]
            }
            mock_fs.write_yaml.assert_called_once_with(file_path, expected_data)

    def test_save_to_file_error(self, mock_fs, mock_logger):
        """Test saving feedback when write fails."""
        file_path = "/path/to/feedback.yaml"

        # Create manager with feedback
        manager = FeedbackManager()
        feedback = Feedback.create(
            submission_id="submission-1",
            student_id="student-1",
            assignment_id="assignment-1",
        )
        manager.add_feedback(feedback)

        # Mock write_yaml to return failure
        mock_fs.write_yaml.return_value = MagicMock(success=False, error="Write error")

        # Save to file
        with patch.object(FeedbackManager, "_resolve_file_path") as mock_resolve:
            mock_resolve.return_value = Path(file_path)
            result = manager.save_to_file(file_path)

            # Verify result
            assert result is False

            # Verify error was logged
            mock_logger.error.assert_called_once()
