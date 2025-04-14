# tests/quackster/test_academy/test_plugin.py
"""
Tests for the Teaching plugin module.
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from quackster.academy.plugin import TeachingPlugin
from quackster.academy.results import AssignmentResult, TeachingResult


class TestTeachingPlugin:
    """Tests for the TeachingPlugin class."""

    def test_init(self):
        """Test initialization of TeachingPlugin."""
        plugin = TeachingPlugin()
        assert plugin._service is not None
        assert plugin._initialized is False

    def test_info(self):
        """Test getting plugin information."""
        plugin = TeachingPlugin()
        info = plugin.info

        assert info.name == "quackster"
        assert info.description == "Teaching module for QuackCore"
        assert "github" in info.dependencies

    def test_initialize_success(self):
        """Test successful initialization of plugin."""
        plugin = TeachingPlugin()

        # Mock _service.initialize to return success
        plugin._service.initialize = MagicMock(
            return_value=TeachingResult(
                success=True, message="Initialization successful"
            )
        )

        # Initialize the plugin
        result = plugin.initialize(
            {"config_path": "/path/to/config.yaml", "base_dir": "/base/dir"}
        )

        assert result.success is True
        assert "Initialization successful" in result.message
        assert plugin._initialized is True

        # Verify _service.initialize was called with correct arguments
        plugin._service.initialize.assert_called_once_with(
            "/path/to/config.yaml", "/base/dir"
        )

    def test_initialize_already_initialized(self):
        """Test initializing when already initialized."""
        plugin = TeachingPlugin()
        plugin._initialized = True

        # Mock _service.initialize should not be called
        plugin._service.initialize = MagicMock()

        result = plugin.initialize()

        assert result.success is True
        assert "already initialized" in result.message
        plugin._service.initialize.assert_not_called()

    def test_initialize_failure(self):
        """Test initialization failure."""
        plugin = TeachingPlugin()

        # Mock _service.initialize to return failure
        plugin._service.initialize = MagicMock(
            return_value=TeachingResult(success=False, error="Initialization error")
        )

        # Initialize the plugin
        result = plugin.initialize()

        assert result.success is False
        assert "Initialization error" in result.error
        assert plugin._initialized is False

    def test_initialize_with_fs_expansion(self, mock_fs):
        """Test initialization with path expansion."""
        plugin = TeachingPlugin()

        # Mock expand_user_vars
        mock_fs.expand_user_vars.return_value = "/expanded/path/config.yaml"

        # Mock _service.initialize
        plugin._service.initialize = MagicMock(
            return_value=TeachingResult(success=True)
        )

        # Initialize with path that needs expansion
        plugin.initialize({"config_path": "~/config.yaml"})

        # Verify expand_user_vars was called
        mock_fs.expand_user_vars.assert_called_once_with("~/config.yaml")

        # Verify _service.initialize was called with expanded path
        plugin._service.initialize.assert_called_once_with(
            "/expanded/path/config.yaml", None
        )

    def test_initialize_with_relative_base_dir(self, mock_resolver):
        """Test initialization with relative base_dir."""
        plugin = TeachingPlugin()
        mock_resolver.get_project_root.return_value = Path("/project/root")

        # Mock _service.initialize
        plugin._service.initialize = MagicMock(
            return_value=TeachingResult(success=True)
        )

        # Initialize with relative base_dir
        plugin.initialize({"base_dir": "relative/dir"})

        # Verify _service.initialize was called with resolved path
        plugin._service.initialize.assert_called_once_with(
            None, "/project/root/relative/dir"
        )

    def test_create_context_success(self):
        """Test successful create_context."""
        plugin = TeachingPlugin()

        # Mock _service.create_context
        plugin._service.create_context = MagicMock(
            return_value=TeachingResult(success=True, message="Context created")
        )

        # Create context
        result = plugin.create_context("Test Course", "test-org", "/base/dir")

        assert result.success is True
        assert "Context created" in result.message

        # Verify _service.create_context was called with correct arguments
        plugin._service.create_context.assert_called_once_with(
            "Test Course", "test-org", "/base/dir"
        )

    def test_create_context_with_relative_base_dir(self, mock_resolver):
        """Test create_context with relative base_dir."""
        plugin = TeachingPlugin()
        mock_resolver.get_project_root.return_value = Path("/project/root")

        # Mock _service.create_context
        plugin._service.create_context = MagicMock(
            return_value=TeachingResult(success=True)
        )

        # Create context with relative base_dir
        plugin.create_context("Test Course", "test-org", "relative/dir")

        # Verify _service.create_context was called with resolved path
        plugin._service.create_context.assert_called_once_with(
            "Test Course", "test-org", "/project/root/relative/dir"
        )

    def test_create_assignment_not_initialized(self):
        """Test create_assignment when not initialized."""
        plugin = TeachingPlugin()
        plugin._initialized = False

        # Mock _service.create_assignment_from_template
        plugin._service.create_assignment_from_template = MagicMock()

        result = plugin.create_assignment(
            "Test Assignment", "template-repo", students=["student1"]
        )

        assert result.success is False
        assert "not initialized" in result.error
        plugin._service.create_assignment_from_template.assert_not_called()

    def test_create_assignment_success(self):
        """Test successful create_assignment."""
        plugin = TeachingPlugin()
        plugin._initialized = True

        # Mock _service.create_assignment_from_template
        expected_result = AssignmentResult(
            success=True, message="Assignment created", repositories=[MagicMock()]
        )
        plugin._service.create_assignment_from_template = MagicMock(
            return_value=expected_result
        )

        # Create assignment
        result = plugin.create_assignment(
            "Test Assignment",
            "template-repo",
            description="Assignment description",
            due_date="2023-12-31",
            students=["student1", "student2"],
        )

        assert result is expected_result

        # Verify _service.create_assignment_from_template was called with correct arguments
        plugin._service.create_assignment_from_template.assert_called_once_with(
            assignment_name="Test Assignment",
            template_repo="template-repo",
            description="Assignment description",
            due_date="2023-12-31",
            students=["student1", "student2"],
        )

    def test_find_student_submissions_not_initialized(self):
        """Test find_student_submissions when not initialized."""
        plugin = TeachingPlugin()
        plugin._initialized = False

        # Mock _service.find_student_submissions
        plugin._service.find_student_submissions = MagicMock()

        result = plugin.find_student_submissions("Assignment", "student1")

        assert result.success is False
        assert "not initialized" in result.error
        plugin._service.find_student_submissions.assert_not_called()

    def test_find_student_submissions_success(self):
        """Test successful find_student_submissions."""
        plugin = TeachingPlugin()
        plugin._initialized = True

        # Mock _service.find_student_submissions
        expected_result = TeachingResult(
            success=True, message="Submission found", content=MagicMock()
        )
        plugin._service.find_student_submissions = MagicMock(
            return_value=expected_result
        )

        # Find student submissions
        result = plugin.find_student_submissions("Assignment", "student1")

        assert result is expected_result

        # Verify _service.find_student_submissions was called with correct arguments
        plugin._service.find_student_submissions.assert_called_once_with(
            "Assignment", "student1"
        )

    def test_get_context_not_initialized(self):
        """Test get_context when not initialized."""
        plugin = TeachingPlugin()
        plugin._initialized = False

        context = plugin.get_context()

        assert context is None

    def test_get_context_success(self):
        """Test successful get_context."""
        plugin = TeachingPlugin()
        plugin._initialized = True

        # Mock _service.context
        expected_context = MagicMock()
        plugin._service.context = expected_context

        context = plugin.get_context()

        assert context is expected_context

    def test_call_valid_method(self):
        """Test calling a valid method."""
        plugin = TeachingPlugin()

        # Mock create_context
        expected_result = TeachingResult(success=True)
        plugin.create_context = MagicMock(return_value=expected_result)

        # Call create_context through call method
        result = plugin.call(
            "create_context",
            course_name="Test Course",
            github_org="test-org",
            base_dir="/base/dir",
        )

        assert result is expected_result

        # Verify create_context was called with correct arguments
        plugin.create_context.assert_called_once_with(
            course_name="Test Course", github_org="test-org", base_dir="/base/dir"
        )

    def test_call_invalid_method(self):
        """Test calling an invalid method."""
        plugin = TeachingPlugin()

        # Call non-existent method
        with pytest.raises(AttributeError) as exc_info:
            plugin.call("non_existent_method")

        assert "has no method" in str(exc_info.value)


def test_create_plugin():
    """Test create_plugin function."""
    from quackcore.teaching.academy.plugin import create_plugin

    plugin = create_plugin()

    assert isinstance(plugin, TeachingPlugin)
