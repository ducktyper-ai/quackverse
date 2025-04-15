# tests/quackster/test_academy/test_assignment.py
"""
Tests for the Assignment module.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from quackster.academy.assignment import (
    Assignment,
    AssignmentManager,
    AssignmentStatus,
    AssignmentType,
)


class TestAssignment:
    """Tests for the Assignment class."""

    def test_create(self):
        """Test creating an assignment."""
        # Basic create
        assignment = Assignment.create(
            name="Test Assignment", description="Test description"
        )
        assert assignment.name == "Test Assignment"
        assert assignment.description == "Test description"
        assert assignment.id is not None
        assert assignment.status == AssignmentStatus.DRAFT
        assert assignment.assignment_type == AssignmentType.INDIVIDUAL
        assert assignment.due_date is None
        assert assignment.points == 100.0
        assert assignment.published_at is None
        assert assignment.template_repo is None
        assert assignment.starter_code_url is None
        assert assignment.instructions_url is None
        assert assignment.allow_late_submissions is True
        assert assignment.late_penalty_percentage == 10.0
        assert assignment.repositories == []

        # Create with optional fields
        due_date_str = "2023-01-31T23:59:59"
        assignment = Assignment.create(
            name="Advanced Assignment",
            description="Advanced topics",
            assignment_type=AssignmentType.GROUP,
            due_date=due_date_str,
            points=200.0,
        )
        assert assignment.name == "Advanced Assignment"
        assert assignment.description == "Advanced topics"
        assert assignment.id is not None
        assert assignment.status == AssignmentStatus.DRAFT
        assert assignment.assignment_type == AssignmentType.GROUP
        assert assignment.due_date == datetime.fromisoformat(due_date_str)
        assert assignment.points == 200.0

    def test_ensure_id(self):
        """Test that ID is generated if not provided."""
        # Create with no ID
        assignment = Assignment(name="Test Assignment")
        assert assignment.id is not None

        # Create with provided ID
        assignment = Assignment(id="custom-id", name="Test Assignment")
        assert assignment.id == "custom-id"

    def test_publish(self):
        """Test publishing an assignment."""
        assignment = Assignment.create(name="Test Assignment")
        assert assignment.status == AssignmentStatus.DRAFT
        assert assignment.published_at is None

        # Publish the assignment
        result = assignment.publish()

        assert result == assignment  # Method chaining works
        assert assignment.status == AssignmentStatus.PUBLISHED
        assert assignment.published_at is not None

    def test_close(self):
        """Test closing an assignment."""
        assignment = Assignment.create(name="Test Assignment")
        assignment.publish()

        # Close the assignment
        result = assignment.close()

        assert result == assignment  # Method chaining works
        assert assignment.status == AssignmentStatus.CLOSED

    def test_is_past_due(self):
        """Test checking if an assignment is past due."""
        now = datetime.now()

        # No due date
        assignment = Assignment.create(name="Test Assignment")
        assert assignment.is_past_due() is False

        # Due date in the future
        assignment = Assignment.create(
            name="Test Assignment", due_date=now + timedelta(days=1)
        )
        assert assignment.is_past_due() is False

        # Due date in the past
        assignment = Assignment.create(
            name="Test Assignment", due_date=now - timedelta(days=1)
        )
        assert assignment.is_past_due() is True

    def test_update_status(self):
        """Test updating assignment status based on date."""
        now = datetime.now()

        # DRAFT status should not change
        assignment = Assignment.create(name="Test Assignment")
        assert assignment.status == AssignmentStatus.DRAFT

        assignment.update_status()
        assert assignment.status == AssignmentStatus.DRAFT

        # CLOSED status should not change
        assignment.status = AssignmentStatus.CLOSED
        assignment.update_status()
        assert assignment.status == AssignmentStatus.CLOSED

        # PUBLISHED but not past due should become ACTIVE
        assignment = Assignment.create(name="Test Assignment")
        assignment.publish()
        assignment.due_date = now + timedelta(days=1)
        assignment.update_status()
        assert assignment.status == AssignmentStatus.ACTIVE

        # PUBLISHED and past due should become PAST_DUE
        assignment = Assignment.create(name="Test Assignment")
        assignment.publish()
        assignment.due_date = now - timedelta(days=1)
        assignment.update_status()
        assert assignment.status == AssignmentStatus.PAST_DUE

    def test_add_repository(self):
        """Test adding a repository to an assignment."""
        assignment = Assignment.create(name="Test Assignment")

        # Add a repository
        repo_name = "test-org/test-repo"
        assignment.add_repository(repo_name)

        assert repo_name in assignment.repositories

        # Adding the same repository again should not duplicate
        assignment.add_repository(repo_name)
        assert assignment.repositories.count(repo_name) == 1

    def test_get_student_repo_name(self):
        """Test getting the expected repository name for a student."""
        assignment = Assignment.create(name="Test Assignment")

        repo_name = assignment.get_student_repo_name("student1")
        assert repo_name == "test-assignment-student1"

        # Test with spaces and capitalization
        assignment = Assignment.create(name="Advanced Assignment 2")
        repo_name = assignment.get_student_repo_name("student2")
        assert repo_name == "advanced-assignment-2-student2"


class TestAssignmentManager:
    """Tests for the AssignmentManager class."""

    def test_init(self):
        """Test initialization of AssignmentManager."""
        manager = AssignmentManager()
        assert manager.assignments == {}
        assert manager.by_name == {}

    def test_add_assignment(self):
        """Test adding an assignment."""
        manager = AssignmentManager()
        assignment = Assignment.create(name="Test Assignment")

        manager.add_assignment(assignment)

        assert len(manager.assignments) == 1
        assert manager.assignments[assignment.id] == assignment
        assert manager.by_name["test assignment"] == assignment

    def test_get_assignment(self):
        """Test getting an assignment by ID."""
        manager = AssignmentManager()
        assignment = Assignment.create(name="Test Assignment")

        manager.add_assignment(assignment)

        # Get existing assignment
        result = manager.get_assignment(assignment.id)
        assert result == assignment

        # Get non-existent assignment
        result = manager.get_assignment("non-existent")
        assert result is None

    def test_get_assignment_by_name(self):
        """Test getting an assignment by name."""
        manager = AssignmentManager()
        assignment = Assignment.create(name="Test Assignment")

        manager.add_assignment(assignment)

        # Get existing assignment with exact name
        result = manager.get_assignment_by_name("Test Assignment")
        assert result == assignment

        # Get existing assignment with different case
        result = manager.get_assignment_by_name("TEST ASSIGNMENT")
        assert result == assignment

        # Get non-existent assignment
        result = manager.get_assignment_by_name("Non-existent")
        assert result is None

    def test_add_assignments(self):
        """Test adding multiple assignments."""
        manager = AssignmentManager()
        assignment1 = Assignment.create(name="Assignment 1")
        assignment2 = Assignment.create(name="Assignment 2")

        manager.add_assignments([assignment1, assignment2])

        assert len(manager.assignments) == 2
        assert manager.assignments[assignment1.id] == assignment1
        assert manager.assignments[assignment2.id] == assignment2
        assert manager.by_name["assignment 1"] == assignment1
        assert manager.by_name["assignment 2"] == assignment2

    def test_remove_assignment(self):
        """Test removing an assignment."""
        manager = AssignmentManager()
        assignment1 = Assignment.create(name="Assignment 1")
        assignment2 = Assignment.create(name="Assignment 2")

        manager.add_assignment(assignment1)
        manager.add_assignment(assignment2)

        # Remove existing assignment
        result = manager.remove_assignment(assignment1.id)
        assert result is True
        assert len(manager.assignments) == 1
        assert assignment1.id not in manager.assignments
        assert "assignment 1" not in manager.by_name
        assert assignment2.id in manager.assignments
        assert manager.by_name["assignment 2"] == assignment2

        # Remove non-existent assignment
        result = manager.remove_assignment("non-existent")
        assert result is False
        assert len(manager.assignments) == 1

    def test_update_statuses(self):
        """Test updating statuses of all assignments."""
        manager = AssignmentManager()
        now = datetime.now()

        # Create assignments with different statuses and dates
        assignment1 = Assignment.create(name="Assignment 1")  # DRAFT

        assignment2 = Assignment.create(name="Assignment 2")  # PUBLISHED, not past due
        assignment2.publish()
        assignment2.due_date = now + timedelta(days=1)

        assignment3 = Assignment.create(name="Assignment 3")  # PUBLISHED, past due
        assignment3.publish()
        assignment3.due_date = now - timedelta(days=1)

        assignment4 = Assignment.create(name="Assignment 4")  # CLOSED
        assignment4.close()

        manager.add_assignments([assignment1, assignment2, assignment3, assignment4])

        # Update statuses
        manager.update_statuses()

        # Check updated statuses
        assert assignment1.status == AssignmentStatus.DRAFT  # Unchanged
        assert assignment2.status == AssignmentStatus.ACTIVE  # Updated to ACTIVE
        assert assignment3.status == AssignmentStatus.PAST_DUE  # Updated to PAST_DUE
        assert assignment4.status == AssignmentStatus.CLOSED  # Unchanged

    def test_get_active_assignments(self):
        """Test getting active assignments."""
        manager = AssignmentManager()
        now = datetime.now()

        # Create assignments with different statuses
        assignment1 = Assignment.create(name="Assignment 1")  # DRAFT

        assignment2 = Assignment.create(name="Assignment 2")  # ACTIVE
        assignment2.publish()
        assignment2.due_date = now + timedelta(days=1)
        assignment2.status = AssignmentStatus.ACTIVE

        assignment3 = Assignment.create(name="Assignment 3")  # PAST_DUE
        assignment3.publish()
        assignment3.due_date = now - timedelta(days=1)
        assignment3.status = AssignmentStatus.PAST_DUE

        assignment4 = Assignment.create(name="Assignment 4")  # CLOSED
        assignment4.close()

        manager.add_assignments([assignment1, assignment2, assignment3, assignment4])

        # Get active assignments
        active = manager.get_active_assignments()

        # Should only return ACTIVE assignments
        assert len(active) == 1
        assert active[0] == assignment2

    def test_get_past_due_assignments(self):
        """Test getting past due assignments."""
        manager = AssignmentManager()
        now = datetime.now()

        # Create assignments with different statuses
        assignment1 = Assignment.create(name="Assignment 1")  # DRAFT

        assignment2 = Assignment.create(name="Assignment 2")  # ACTIVE
        assignment2.publish()
        assignment2.due_date = now + timedelta(days=1)
        assignment2.status = AssignmentStatus.ACTIVE

        assignment3 = Assignment.create(name="Assignment 3")  # PAST_DUE
        assignment3.publish()
        assignment3.due_date = now - timedelta(days=1)
        assignment3.status = AssignmentStatus.PAST_DUE

        assignment4 = Assignment.create(name="Assignment 4")  # CLOSED
        assignment4.close()

        manager.add_assignments([assignment1, assignment2, assignment3, assignment4])

        # Get past due assignments
        past_due = manager.get_past_due_assignments()

        # Should only return PAST_DUE assignments
        assert len(past_due) == 1
        assert past_due[0] == assignment3

    def test_load_from_file(self, mock_fs):
        """Test loading assignments from a file."""
        file_path = "/path/to/assignments.yaml"

        # Mock read_yaml to return success with assignments data
        assignments_data = {
            "assignments": [
                {
                    "id": "assignment-1",
                    "name": "Assignment 1",
                    "description": "Description 1",
                    "status": "DRAFT",
                    "assignment_type": "INDIVIDUAL",
                    "points": 100.0,
                },
                {
                    "id": "assignment-2",
                    "name": "Assignment 2",
                    "status": "PUBLISHED",
                    "assignment_type": "GROUP",
                    "points": 200.0,
                    "published_at": "2023-01-01T12:00:00",
                },
            ]
        }
        mock_fs._read_yaml.return_value = MagicMock(success=True, data=assignments_data)

        # Load from file
        manager = AssignmentManager.load_from_file(file_path)

        # Verify assignments were loaded
        assert len(manager.assignments) == 2
        assert "assignment-1" in manager.assignments
        assert "assignment-2" in manager.assignments

        # Verify assignment details
        assignment1 = manager.assignments["assignment-1"]
        assert assignment1.name == "Assignment 1"
        assert assignment1.description == "Description 1"
        assert assignment1.status == AssignmentStatus.DRAFT
        assert assignment1.assignment_type == AssignmentType.INDIVIDUAL
        assert assignment1.points == 100.0

        assignment2 = manager.assignments["assignment-2"]
        assert assignment2.name == "Assignment 2"
        assert assignment2.status == AssignmentStatus.PUBLISHED
        assert assignment2.assignment_type == AssignmentType.GROUP
        assert assignment2.points == 200.0
        assert assignment2.published_at == datetime.fromisoformat("2023-01-01T12:00:00")

    def test_load_from_file_file_not_found(self, mock_fs):
        """Test loading assignments when file is not found."""
        file_path = "/path/to/assignments.yaml"

        # Mock read_yaml to return failure
        mock_fs._read_yaml.return_value = MagicMock(
            success=False, error="File not found"
        )

        # Load from file should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            AssignmentManager.load_from_file(file_path)

    def test_load_from_file_invalid_format(self, mock_fs):
        """Test loading assignments with invalid file format."""
        file_path = "/path/to/assignments.yaml"

        # Mock read_yaml to return success with invalid data
        invalid_data = {"not_assignments": []}
        mock_fs._read_yaml.return_value = MagicMock(success=True, data=invalid_data)

        # Load from file should raise ValueError
        with pytest.raises(ValueError):
            AssignmentManager.load_from_file(file_path)

    def test_load_from_file_assignment_error(self, mock_fs, mock_logger):
        """Test loading assignments with error in assignment data."""
        file_path = "/path/to/assignments.yaml"

        # Mock read_yaml to return success with one invalid assignment
        assignments_data = {
            "assignments": [
                {"id": "assignment-1", "name": "Assignment 1"},
                {
                    # Missing required name field
                    "id": "assignment-2"
                },
            ]
        }
        mock_fs._read_yaml.return_value = MagicMock(success=True, data=assignments_data)

        # Load from file should still work, but log a warning and skip the invalid assignment
        manager = AssignmentManager.load_from_file(file_path)

        # Verify only valid assignment was loaded
        assert len(manager.assignments) == 1
        assert "assignment-1" in manager.assignments
        assert "assignment-2" not in manager.assignments

        # Verify warning was logged
        mock_logger.warning.assert_called_once()

    def test_save_to_file(self, mock_fs):
        """Test saving assignments to a file."""
        file_path = "/path/to/assignments.yaml"

        # Create manager with assignments
        manager = AssignmentManager()
        assignment1 = Assignment.create(name="Assignment 1")
        assignment2 = Assignment.create(name="Assignment 2")
        manager.add_assignments([assignment1, assignment2])

        # Mock write_yaml to return success
        mock_fs._write_yaml.return_value = MagicMock(success=True)

        # Save to file
        result = manager.save_to_file(file_path)

        # Verify result
        assert result is True

        # Verify write_yaml was called with correct data
        expected_data = {
            "assignments": [assignment1.model_dump(), assignment2.model_dump()]
        }
        mock_fs._write_yaml.assert_called_once_with(file_path, expected_data)

    def test_save_to_file_error(self, mock_fs, mock_logger):
        """Test saving assignments when write fails."""
        file_path = "/path/to/assignments.yaml"

        # Create manager with assignments
        manager = AssignmentManager()
        assignment = Assignment.create(name="Test Assignment")
        manager.add_assignment(assignment)

        # Mock write_yaml to return failure
        mock_fs._write_yaml.return_value = MagicMock(success=False, error="Write error")

        # Save to file
        result = manager.save_to_file(file_path)

        # Verify result
        assert result is False

        # Verify error was logged
        mock_logger.error.assert_called_once()
