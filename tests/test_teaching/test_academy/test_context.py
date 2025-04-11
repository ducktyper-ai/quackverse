# tests/test_teaching/test_academy/test_context.py
"""
Tests for the TeachingContext class.
"""
from pathlib import Path
import os
import pytest
from unittest.mock import patch, MagicMock

from quackcore.errors import QuackConfigurationError
from quackcore.teaching.academy.context import TeachingContext, TeachingConfig, \
    GitHubConfig


class TestTeachingConfig:
    """Tests for the TeachingConfig class."""

    def test_ensure_course_id(self):
        """Test that course_id is generated from course_name if not provided."""
        # With course_id provided
        config = TeachingConfig(
            course_name="Test Course",
            course_id="custom-id",
            github=GitHubConfig(organization="test-org")
        )
        assert config.course_id == "custom-id"

        # Without course_id provided - should generate from course_name
        config = TeachingConfig(
            course_name="Test Course",
            github=GitHubConfig(organization="test-org")
        )
        assert config.course_id == "test-course"


class TestTeachingContext:
    """Tests for the TeachingContext class."""

    def test_init(self, teaching_config, mock_fs, mock_resolver, temp_dir):
        """Test initialization of TeachingContext."""
        context = TeachingContext(teaching_config, temp_dir)

        # Check base directory
        assert context.base_dir == temp_dir

        # Check directories are resolved correctly
        assert context.assignments_dir == Path(os.path.join(temp_dir, "assignments"))
        assert context.feedback_dir == Path(os.path.join(temp_dir, "feedback"))
        assert context.grading_dir == Path(os.path.join(temp_dir, "grading"))
        assert context.submissions_dir == Path(os.path.join(temp_dir, "submissions"))
        assert context.students_file == Path(os.path.join(temp_dir, "students.yaml"))
        assert context.course_config_file == Path(os.path.join(temp_dir, "course.yaml"))

    def test_init_without_base_dir(self, teaching_config, mock_resolver):
        """Test initialization without providing base_dir."""
        mock_resolver.get_project_root.return_value = Path("/mock/project/root")
        context = TeachingContext(teaching_config)

        # Should use project root as base_dir
        assert context.base_dir == Path("/mock/project/root")

    def test_init_with_project_root_error(self, teaching_config, mock_resolver):
        """Test initialization when project root detection fails."""
        mock_resolver.get_project_root.side_effect = Exception("Project root not found")
        with patch("pathlib.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/mock/current/dir")
            context = TeachingContext(teaching_config)

            # Should fallback to current working directory
            assert context.base_dir == Path("/mock/current/dir")

    def test_resolve_path_absolute(self, teaching_config, temp_dir):
        """Test _resolve_path with absolute path."""
        context = TeachingContext(teaching_config, temp_dir)
        absolute_path = "/absolute/path"

        # Absolute paths should be returned as-is
        assert context._resolve_path(absolute_path) == Path(absolute_path)

    def test_resolve_path_relative(self, teaching_config, temp_dir, mock_fs):
        """Test _resolve_path with relative path."""
        context = TeachingContext(teaching_config, temp_dir)
        relative_path = "relative/path"

        mock_fs.join_path.return_value = os.path.join(str(temp_dir), relative_path)
        resolved = context._resolve_path(relative_path)

        # Relative paths should be joined with base_dir
        assert resolved == Path(os.path.join(str(temp_dir), relative_path))
        mock_fs.join_path.assert_called_once_with(str(temp_dir), relative_path)

    def test_ensure_directories(self, teaching_context, mock_fs):
        """Test ensure_directories creates necessary directories."""
        teaching_context.ensure_directories()

        # Check each directory is created
        expected_calls = [
            ((str(teaching_context.assignments_dir),), {'exist_ok': True}),
            ((str(teaching_context.feedback_dir),), {'exist_ok': True}),
            ((str(teaching_context.grading_dir),), {'exist_ok': True}),
            ((str(teaching_context.submissions_dir),), {'exist_ok': True}),
        ]

        # Check that create_directory was called for each path
        assert mock_fs.create_directory.call_count == 4
        for call in expected_calls:
            mock_fs.create_directory.assert_any_call(*call[0], **call[1])

    def test_github_property_success(self, teaching_context, mock_integration_registry):
        """Test the github property when integration is available."""
        # Get the github property
        github = teaching_context.github

        # Verify it requested the GitHub integration
        mock_integration_registry.get_integration.assert_called_once_with("GitHub")

        # Verify we got the mock GitHub object
        assert github is mock_integration_registry.get_integration.return_value

    def test_github_property_not_available(self, teaching_context,
                                           mock_integration_registry):
        """Test the github property when integration is not available."""
        mock_integration_registry.get_integration.return_value = None

        # Attempting to get github should raise an error
        with pytest.raises(QuackConfigurationError) as exc_info:
            teaching_context.github

        assert "GitHub integration not available" in str(exc_info.value)

    def test_github_property_initialization_error(self, teaching_context,
                                                  mock_integration_registry):
        """Test the github property when initialization fails."""
        mock_github = MagicMock()
        mock_github.client = None
        mock_github.initialize.return_value = MagicMock(success=False,
                                                        error="Initialization error")
        mock_integration_registry.get_integration.return_value = mock_github

        # Attempting to get github should raise an error
        with pytest.raises(QuackConfigurationError) as exc_info:
            teaching_context.github

        assert "Failed to initialize GitHub integration" in str(exc_info.value)

    def test_from_config_success(self, mock_fs, mock_resolver, teaching_config):
        """Test creating context from config file."""
        config_path = "/path/to/config.yaml"

        # Mock loading the config
        mock_fs.expand_user_vars.side_effect = lambda x: x

        with patch("quackcore.config.loader.load_yaml_config") as mock_load_config:
            mock_load_config.return_value = teaching_config.model_dump()

            # Create context from config
            context = TeachingContext.from_config(config_path, "/base/dir")

            # Verify config was loaded
            mock_load_config.assert_called_once_with(config_path)

            # Verify context was created with correct config
            assert context.config.course_name == teaching_config.course_name
            assert context.config.github.organization == teaching_config.github.organization
            assert context.base_dir == Path("/base/dir")

    def test_from_config_infer_base_dir(self, mock_fs, mock_resolver, teaching_config):
        """Test creating context from config file with inferred base_dir."""
        config_path = "/path/to/config.yaml"

        # Mock loading the config
        with patch("quackcore.config.loader.load_yaml_config") as mock_load_config:
            mock_load_config.return_value = teaching_config.model_dump()

            # Create context from config without specifying base_dir
            context = TeachingContext.from_config(config_path)

            # Verify base_dir was inferred from config path
            assert context.base_dir == Path("/path/to")

    def test_from_config_env_var(self, monkeypatch, mock_fs, mock_resolver,
                                 teaching_config):
        """Test creating context from config file specified by environment variable."""
        env_config_path = "/env/path/config.yaml"
        monkeypatch.setenv("QUACK_TEACHING_CONFIG", env_config_path)

        # Mock loading the config
        with patch("quackcore.config.loader.load_yaml_config") as mock_load_config:
            mock_load_config.return_value = teaching_config.model_dump()

            # Create context from config without specifying path
            context = TeachingContext.from_config()

            # Verify config was loaded from env var path
            mock_load_config.assert_called_once_with(env_config_path)

    def test_from_config_search_paths(self, monkeypatch, mock_fs, mock_resolver,
                                      teaching_config):
        """Test creating context from config file by searching standard paths."""
        # Clear environment variable
        monkeypatch.delenv("QUACK_TEACHING_CONFIG", raising=False)

        # Mock Path.exists to return True for one of the standard paths
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.side_effect = lambda: False
            mock_exists.side_effect = [False, True, False]  # Second path exists

            # Mock loading the config
            with patch("quackcore.config.loader.load_yaml_config") as mock_load_config:
                mock_load_config.return_value = teaching_config.model_dump()

                # Create context from config without specifying path
                with patch("pathlib.Path.cwd") as mock_cwd:
                    mock_cwd.return_value = Path("/current/dir")

                    with patch("pathlib.Path.home") as mock_home:
                        mock_home.return_value = Path("/home/user")

                        context = TeachingContext.from_config()

                        # Verify config was loaded from the second standard path
                        assert mock_load_config.call_args[0][0] == Path(
                            "/current/dir/config/teaching.yaml")

    def test_from_config_no_config_found(self, monkeypatch, mock_fs, mock_resolver):
        """Test creating context when no config file is found."""
        # Clear environment variable
        monkeypatch.delenv("QUACK_TEACHING_CONFIG", raising=False)

        # Mock Path.exists to return False for all standard paths
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = False

            # Attempting to create context should raise an error
            with pytest.raises(QuackConfigurationError) as exc_info:
                TeachingContext.from_config()

            assert "No teaching configuration file found" in str(exc_info.value)

    def test_from_config_load_error(self, mock_fs, mock_resolver):
        """Test creating context when config loading fails."""
        config_path = "/path/to/config.yaml"

        # Mock loading the config to fail
        with patch("quackcore.config.loader.load_yaml_config") as mock_load_config:
            mock_load_config.side_effect = Exception("Config loading error")

            # Attempting to create context should raise an error
            with pytest.raises(QuackConfigurationError) as exc_info:
                TeachingContext.from_config(config_path)

            assert "Failed to load teaching configuration" in str(exc_info.value)

    def test_create_default(self, mock_fs, mock_resolver):
        """Test creating a default context."""
        course_name = "Test Course"
        github_org = "test-org"
        base_dir = "/base/dir"

        # Create default context
        context = TeachingContext.create_default(course_name, github_org, base_dir)

        # Verify context was created with correct config
        assert context.config.course_name == course_name
        assert context.config.course_id == "test-course"
        assert context.config.github.organization == github_org
        assert context.base_dir == Path(base_dir)