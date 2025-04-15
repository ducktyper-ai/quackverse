# tests/quackster/test_academy/test_student.py
"""
Tests for the Student module.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from quackster.academy.student import (
    Student,
    StudentRoster,
    StudentSubmission,
    SubmissionStatus,
)


class TestStudentSubmission:
    """Tests for the StudentSubmission class."""

    def test_create(self):
        """Test creating a student submission."""
        submission = StudentSubmission.create(
            student_id="student-1", assignment_id="assignment-1"
        )

        assert submission.student_id == "student-1"
        assert submission.assignment_id == "assignment-1"
        assert submission.id is not None
        assert submission.status == SubmissionStatus.NOT_SUBMITTED
        assert submission.submitted_at is None
        assert submission.graded_at is None
        assert submission.score is None
        assert submission.pr_url is None
        assert submission.repo_url is None
        assert submission.feedback_id is None
        assert submission.comments is None

    def test_mark_submitted(self):
        """Test marking a submission as submitted."""
        submission = StudentSubmission.create(
            student_id="student-1", assignment_id="assignment-1"
        )

        # Mark as submitted with PR URL and repo URL
        result = submission.mark_submitted(
            pr_url="https://github.com/org/repo/pull/1",
            repo_url="https://github.com/org/repo",
        )

        assert result == submission  # Method chaining works
        assert submission.status == SubmissionStatus.SUBMITTED
        assert submission.submitted_at is not None
        assert submission.pr_url == "https://github.com/org/repo/pull/1"
        assert submission.repo_url == "https://github.com/org/repo"

    def test_mark_graded(self):
        """Test marking a submission as graded."""
        submission = StudentSubmission.create(
            student_id="student-1", assignment_id="assignment-1"
        )
        submission.mark_submitted()

        # Mark as graded with score and feedback
        result = submission.mark_graded(score=85.5, feedback_id="feedback-1")

        assert result == submission  # Method chaining works
        assert submission.status == SubmissionStatus.GRADED
        assert submission.graded_at is not None
        assert submission.score == 85.5
        assert submission.feedback_id == "feedback-1"

    def test_update_gamification_not_submitted(self, mock_gamification_service):
        """Test update_gamification when submission is not submitted."""
        submission = StudentSubmission.create(
            student_id="student-1", assignment_id="assignment-1"
        )

        # Should not call gamification service
        submission.update_gamification()
        mock_gamification_service.return_value.handle_github_pr_submission.assert_not_called()
        mock_gamification_service.return_value.handle_assignment_completion.assert_not_called()

    def test_update_gamification_submitted_pr(self, mock_gamification_service):
        """Test update_gamification when submission has PR URL."""
        submission = StudentSubmission.create(
            student_id="student-1", assignment_id="assignment-1"
        )
        submission.mark_submitted(pr_url="https://github.com/org/repo/pull/123")

        # Should call handle_github_pr_submission
        submission.update_gamification()
        mock_gamification_service.return_value.handle_github_pr_submission.assert_called_once_with(
            123, "org/repo"
        )

    def test_update_gamification_graded(self, mock_gamification_service):
        """Test update_gamification when submission is graded."""
        submission = StudentSubmission.create(
            student_id="student-1", assignment_id="assignment-1"
        )
        submission.mark_submitted()
        submission.mark_graded(score=85.0)

        # Should call handle_assignment_completion
        submission.update_gamification()
        mock_gamification_service.return_value.handle_assignment_completion.assert_called_once()

        # Verify call arguments
        args, kwargs = (
            mock_gamification_service.return_value.handle_assignment_completion.call_args
        )
        assert kwargs["assignment_id"] == "assignment-1"
        assert kwargs["score"] == 85.0

    def test_update_gamification_error(self, mock_gamification_service):
        """Test update_gamification when an error occurs."""
        submission = StudentSubmission.create(
            student_id="student-1", assignment_id="assignment-1"
        )
        submission.mark_submitted(pr_url="https://github.com/org/repo/pull/invalid")

        # Mock handle_github_pr_submission to raise an exception
        mock_gamification_service.return_value.handle_github_pr_submission.side_effect = Exception(
            "Gamification error"
        )

        # Should not raise an exception
        submission.update_gamification()


class TestStudent:
    """Tests for the Student class."""

    def test_create(self):
        """Test creating a student."""
        # Basic create
        student = Student.create(github_username="student1", name="Student One")

        assert student.github_username == "student1"
        assert student.name == "Student One"
        assert student.id is not None
        assert student.email is None
        assert student.active is True
        assert student.group is None
        assert student.metadata == {}
        assert student.submissions == {}

        # Create with optional fields
        student = Student.create(
            github_username="student2",
            name="Student Two",
            email="student2@example.com",
            group="Group A",
        )

        assert student.github_username == "student2"
        assert student.name == "Student Two"
        assert student.id is not None
        assert student.email == "student2@example.com"
        assert student.active is True
        assert student.group == "Group A"

    def test_ensure_id(self):
        """Test that ID is generated if not provided."""
        # Create with no ID
        student = Student(github_username="student1", name="Student One")
        assert student.id is not None

        # Create with provided ID
        student = Student(
            id="custom-id", github_username="student1", name="Student One"
        )
        assert student.id == "custom-id"

    def test_add_submission(self):
        """Test adding a submission for a student."""
        student = Student.create(github_username="student1", name="Student One")

        submission = StudentSubmission.create(
            student_id=student.id, assignment_id="assignment-1"
        )

        # Add submission
        student.add_submission(submission)

        assert "assignment-1" in student.submissions
        assert student.submissions["assignment-1"] == submission

    def test_add_submission_wrong_student(self):
        """Test adding a submission for a different student."""
        student = Student.create(github_username="student1", name="Student One")

        submission = StudentSubmission.create(
            student_id="different-student", assignment_id="assignment-1"
        )

        # Add submission for different student should raise ValueError
        with pytest.raises(ValueError):
            student.add_submission(submission)

    def test_get_submission(self):
        """Test getting a student's submission for an assignment."""
        student = Student.create(github_username="student1", name="Student One")

        submission = StudentSubmission.create(
            student_id=student.id, assignment_id="assignment-1"
        )
        student.add_submission(submission)

        # Get existing submission
        result = student.get_submission("assignment-1")
        assert result == submission

        # Get non-existent submission
        result = student.get_submission("non-existent")
        assert result is None

    def test_sync_with_progress(self):
        """Test synchronizing student with progress system."""
        student = Student.create(github_username="student1", name="Student One")

        # Mock core_utils.load_progress and save_progress
        with patch("quackster.core.api.load_progress") as mock_load_progress:
            with patch("quackster.core.api.save_progress") as mock_save_progress:
                # Mock progress with different GitHub username
                mock_progress = MagicMock()
                mock_progress.github_username = "old-username"
                mock_load_progress.return_value = mock_progress

                # Sync should update GitHub username in progress
                student.sync_with_progress()

                mock_load_progress.assert_called_once()
                mock_save_progress.assert_called_once_with(mock_progress)
                assert mock_progress.github_username == "student1"

    def test_sync_with_progress_same_username(self):
        """Test synchronizing student when username is already correct."""
        student = Student.create(github_username="student1", name="Student One")

        # Mock core_utils.load_progress and save_progress
        with patch("quackster.core.api.load_progress") as mock_load_progress:
            with patch("quackster.core.api.save_progress") as mock_save_progress:
                # Mock progress with same GitHub username
                mock_progress = MagicMock()
                mock_progress.github_username = "student1"
                mock_load_progress.return_value = mock_progress

                # Sync should not update GitHub username
                student.sync_with_progress()

                mock_load_progress.assert_called_once()
                mock_save_progress.assert_not_called()

    def test_sync_with_progress_error(self, mock_logger):
        """Test synchronizing student when an error occurs."""
        student = Student.create(github_username="student1", name="Student One")

        # Mock core_utils.load_progress to raise an exception
        with patch("quackster.core.api.load_progress") as mock_load_progress:
            mock_load_progress.side_effect = Exception("Progress error")

            # Should not raise an exception
            student.sync_with_progress()

            # Should log error
            assert any(
                "Error syncing student with progress" in str(call)
                for call in mock_logger.debug.call_args_list
            )


class TestStudentRoster:
    """Tests for the StudentRoster class."""

    def test_init(self):
        """Test initialization of StudentRoster."""
        roster = StudentRoster()
        assert roster.students == {}
        assert roster.by_github == {}

    def test_add_student(self):
        """Test adding a student."""
        roster = StudentRoster()
        student = Student.create(github_username="student1", name="Student One")

        # Mock sync_with_progress
        with patch.object(Student, "sync_with_progress") as mock_sync:
            roster.add_student(student)

            assert student.id in roster.students
            assert roster.students[student.id] == student
            assert "student1" in roster.by_github
            assert roster.by_github["student1"] == student

            # Verify sync_with_progress was called
            mock_sync.assert_called_once()

    def test_get_student(self):
        """Test getting a student by ID."""
        roster = StudentRoster()
        student = Student.create(github_username="student1", name="Student One")

        with patch.object(Student, "sync_with_progress"):
            roster.add_student(student)

        # Get existing student
        result = roster.get_student(student.id)
        assert result == student

        # Get non-existent student
        result = roster.get_student("non-existent")
        assert result is None

    def test_get_student_by_github(self):
        """Test getting a student by GitHub username."""
        roster = StudentRoster()
        student = Student.create(
            github_username="Student1",  # Mixed case
            name="Student One",
        )

        with patch.object(Student, "sync_with_progress"):
            roster.add_student(student)

        # Get existing student with exact username
        result = roster.get_student_by_github("Student1")
        assert result == student

        # Get existing student with different case
        result = roster.get_student_by_github("student1")
        assert result == student

        # Get non-existent student
        result = roster.get_student_by_github("non-existent")
        assert result is None

    def test_add_students(self):
        """Test adding multiple students."""
        roster = StudentRoster()
        student1 = Student.create(github_username="student1", name="Student One")
        student2 = Student.create(github_username="student2", name="Student Two")

        with patch.object(Student, "sync_with_progress"):
            roster.add_students([student1, student2])

        assert len(roster.students) == 2
        assert student1.id in roster.students
        assert student2.id in roster.students
        assert "student1" in roster.by_github
        assert "student2" in roster.by_github

    def test_remove_student(self):
        """Test removing a student."""
        roster = StudentRoster()
        student1 = Student.create(github_username="student1", name="Student One")
        student2 = Student.create(github_username="student2", name="Student Two")

        with patch.object(Student, "sync_with_progress"):
            roster.add_students([student1, student2])

        # Remove existing student
        result = roster.remove_student(student1.id)
        assert result is True
        assert student1.id not in roster.students
        assert "student1" not in roster.by_github
        assert student2.id in roster.students
        assert "student2" in roster.by_github

        # Remove non-existent student
        result = roster.remove_student("non-existent")
        assert result is False
        assert len(roster.students) == 1

    def test_get_active_students(self):
        """Test getting active students."""
        roster = StudentRoster()
        student1 = Student.create(
            github_username="student1",
            name="Student One",
        )
        student1.active = True

        student2 = Student.create(
            github_username="student2",
            name="Student Two",
        )
        student2.active = False

        with patch.object(Student, "sync_with_progress"):
            roster.add_students([student1, student2])

        active = roster.get_active_students()
        assert len(active) == 1
        assert active[0] == student1

    def test_get_students_by_group(self):
        """Test getting students by group."""
        roster = StudentRoster()
        student1 = Student.create(
            github_username="student1", name="Student One", group="Group A"
        )

        student2 = Student.create(
            github_username="student2", name="Student Two", group="Group B"
        )

        student3 = Student.create(
            github_username="student3", name="Student Three", group="Group A"
        )

        with patch.object(Student, "sync_with_progress"):
            roster.add_students([student1, student2, student3])

        group_a = roster.get_students_by_group("Group A")
        assert len(group_a) == 2
        assert student1 in group_a
        assert student3 in group_a

        group_b = roster.get_students_by_group("Group B")
        assert len(group_b) == 1
        assert group_b[0] == student2

        group_c = roster.get_students_by_group("Group C")
        assert len(group_c) == 0

    def test_resolve_file_path_absolute(self):
        """Test _resolve_file_path with absolute path."""
        path = "/absolute/path"
        resolved = StudentRoster._resolve_file_path(path)
        assert resolved == Path(path)

    def test_resolve_file_path_relative(self, mock_resolver):
        """Test _resolve_file_path with relative path."""
        mock_resolver._get_project_root.return_value = Path("/project/root")

        path = "relative/path"
        resolved = StudentRoster._resolve_file_path(path)
        assert resolved == Path("/project/root/relative/path")

    def test_resolve_file_path_relative_no_project_root(self, mock_resolver):
        """Test _resolve_file_path with relative path when project root fails."""
        mock_resolver._get_project_root.side_effect = Exception("Project root not found")

        with patch("pathlib.Path.resolve") as mock_resolve:
            mock_resolve.return_value = Path("/resolved/path")

            path = "relative/path"
            resolved = StudentRoster._resolve_file_path(path)
            assert str(resolved).startswith("/resolved/")

    def test_load_from_file(self, mock_fs):
        """Test loading students from a file."""
        file_path = "/path/to/students.yaml"

        # Mock read_yaml to return success with students data
        students_data = {
            "students": [
                {
                    "id": "student-1",
                    "github_username": "student1",
                    "name": "Student One",
                    "email": "student1@example.com",
                    "active": True,
                    "group": "Group A",
                    "submissions": {
                        "assignment-1": {
                            "id": "submission-1",
                            "student_id": "student-1",
                            "assignment_id": "assignment-1",
                            "status": "SUBMITTED",
                            "submitted_at": "2023-01-01T12:00:00",
                        }
                    },
                },
                {
                    "id": "student-2",
                    "github_username": "student2",
                    "name": "Student Two",
                    "active": False,
                },
            ]
        }
        mock_fs._read_yaml.return_value = MagicMock(success=True, data=students_data)

        # Load from file
        with patch.object(Student, "sync_with_progress"):
            with patch.object(StudentRoster, "_resolve_file_path") as mock_resolve:
                mock_resolve.return_value = Path(file_path)
                roster = StudentRoster.load_from_file(file_path)

                # Verify students were loaded
                assert len(roster.students) == 2
                assert "student-1" in roster.students
                assert "student-2" in roster.students
                assert "student1" in roster.by_github
                assert "student2" in roster.by_github

                # Verify student details
                student1 = roster.students["student-1"]
                assert student1.github_username == "student1"
                assert student1.name == "Student One"
                assert student1.email == "student1@example.com"
                assert student1.active is True
                assert student1.group == "Group A"
                assert len(student1.submissions) == 1
                assert "assignment-1" in student1.submissions

                # Verify submission details
                submission = student1.submissions["assignment-1"]
                assert submission.id == "submission-1"
                assert submission.student_id == "student-1"
                assert submission.assignment_id == "assignment-1"
                assert submission.status == SubmissionStatus.SUBMITTED
                assert submission.submitted_at == datetime.fromisoformat(
                    "2023-01-01T12:00:00"
                )

    def test_load_from_file_file_not_found(self, mock_fs):
        """Test loading students when file is not found."""
        file_path = "/path/to/students.yaml"

        # Mock read_yaml to return failure
        mock_fs._read_yaml.return_value = MagicMock(
            success=False, error="File not found"
        )

        # Load from file should raise FileNotFoundError
        with patch.object(StudentRoster, "_resolve_file_path") as mock_resolve:
            mock_resolve.return_value = Path(file_path)
            with pytest.raises(FileNotFoundError):
                StudentRoster.load_from_file(file_path)

    def test_load_from_file_invalid_format(self, mock_fs):
        """Test loading students with invalid file format."""
        file_path = "/path/to/students.yaml"

        # Mock read_yaml to return success with invalid data
        invalid_data = {"not_students": []}
        mock_fs._read_yaml.return_value = MagicMock(success=False, data=invalid_data)
