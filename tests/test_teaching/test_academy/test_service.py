# tests/test_teaching/test_academy/test_service.py
"""
Tests for the TeachingService class.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from quackcore.errors import QuackError
from quackcore.teaching.academy.results import TeachingResult
from quackcore.teaching.academy.service import TeachingService


class TestTeachingService:
    """Tests for the TeachingService class."""

    def test_init(self):
        """Test initialization of TeachingService."""
        service = TeachingService()
        assert service._context is None
        assert service._github is None

    def test_initialize_success(self, mock_fs, mock_resolver, teaching_config):
        """Test successful initialization."""
        service = TeachingService()

        # Mock TeachingContext.from_config
        with patch(
            "quackcore.teaching.academy.context.TeachingContext.from_config"
        ) as mock_from_config:
            mock_context = MagicMock()
            mock_context.config.course_name = "Test Course"
            mock_from_config.return_value = mock_context

            # Initialize the service
            result = service.initialize("/path/to/config.yaml", "/base/dir")

            # Verify TeachingContext.from_config was called
            mock_from_config.assert_called_once_with(
                "/path/to/config.yaml", "/base/dir"
            )

            # Verify the result
            assert result.success
            assert "Test Course" in result.message
            assert service._context == mock_context

    def test_initialize_expand_user_vars(self, mock_fs):
        """Test that user variables are expanded in config_path."""
        service = TeachingService()
        mock_fs.expand_user_vars.return_value = "/expanded/path"

        with patch("quackcore.teaching.academy.context.TeachingContext.from_config"):
            service.initialize("~/config.yaml")

            # Verify expand_user_vars was called
            mock_fs.expand_user_vars.assert_called_once_with("~/config.yaml")

    def test_initialize_relative_base_dir(self, mock_fs, mock_resolver):
        """Test initialization with relative base_dir."""
        service = TeachingService()
        mock_resolver.get_project_root.return_value = Path("/project/root")

        with patch(
            "quackcore.teaching.academy.context.TeachingContext.from_config"
        ) as mock_from_config:
            service.initialize(base_dir="relative/dir")

            # Verify base_dir was resolved relative to project root
            mock_from_config.assert_called_once()
            # Check the base_dir parameter in the call
            _, kwargs = mock_from_config.call_args
            assert kwargs.get("base_dir") == str(Path("/project/root/relative/dir"))

    def test_initialize_relative_base_dir_no_project_root(self, mock_fs, mock_resolver):
        """Test initialization with relative base_dir when project root fails."""
        service = TeachingService()
        mock_resolver.get_project_root.side_effect = Exception("Project root not found")

        with patch(
            "quackcore.teaching.academy.context.TeachingContext.from_config"
        ) as mock_from_config:
            with patch("pathlib.Path.resolve") as mock_resolve:
                mock_resolve.return_value = Path("/resolved/path")
                service.initialize(base_dir="relative/dir")

                # Verify TeachingContext.from_config was called
                mock_from_config.assert_called_once()
                # Check the base_dir parameter contains the resolved path
                _, kwargs = mock_from_config.call_args
                assert str(kwargs.get("base_dir")).startswith("/resolved/")

    def test_initialize_error(self, mock_fs, mock_resolver):
        """Test initialization when an error occurs."""
        service = TeachingService()

        # Mock TeachingContext.from_config to raise an error
        with patch(
            "quackcore.teaching.academy.context.TeachingContext.from_config"
        ) as mock_from_config:
            mock_from_config.side_effect = QuackError("Configuration error")

            # Initialize the service
            result = service.initialize("/path/to/config.yaml")

            # Verify the result
            assert not result.success
            assert "Failed to initialize teaching service" in result.message
            assert "Configuration error" in result.error
            assert service._context is None

    def test_create_context_success(self, mock_fs, mock_resolver):
        """Test successful context creation."""
        service = TeachingService()

        # Mock TeachingContext.create_default
        with patch(
            "quackcore.teaching.academy.context.TeachingContext.create_default"
        ) as mock_create_default:
            mock_context = MagicMock()
            mock_create_default.return_value = mock_context

            # Create a context
            result = service.create_context("Test Course", "test-org", "/base/dir")

            # Verify TeachingContext.create_default was called
            mock_create_default.assert_called_once_with(
                "Test Course", "test-org", "/base/dir"
            )

            # Verify the result
            assert result.success
            assert "Test Course" in result.message
            assert service._context == mock_context

    def test_create_context_relative_base_dir(self, mock_fs, mock_resolver):
        """Test context creation with relative base_dir."""
        service = TeachingService()
        mock_resolver.get_project_root.return_value = Path("/project/root")

        with patch(
            "quackcore.teaching.academy.context.TeachingContext.create_default"
        ) as mock_create_default:
            service.create_context("Test Course", "test-org", "relative/dir")

            # Verify base_dir was resolved relative to project root
            mock_create_default.assert_called_once_with(
                "Test Course", "test-org", "/project/root/relative/dir"
            )

    def test_create_context_error(self, mock_fs, mock_resolver):
        """Test context creation when an error occurs."""
        service = TeachingService()

        # Mock TeachingContext.create_default to raise an error
        with patch(
            "quackcore.teaching.academy.context.TeachingContext.create_default"
        ) as mock_create_default:
            mock_create_default.side_effect = Exception("Creation error")

            # Create a context
            result = service.create_context("Test Course", "test-org")

            # Verify the result
            assert not result.success
            assert "Failed to create teaching context" in result.message
            assert "Creation error" in result.error

    def test_context_property(self):
        """Test the context property."""
        service = TeachingService()

        # Without initialization
        assert service.context is None

        # After initialization
        mock_context = MagicMock()
        service._context = mock_context
        assert service.context is mock_context

    def test_github_property(self):
        """Test the github property."""
        service = TeachingService()

        # Without initialization
        assert service.github is None

        # With initialization but no github
        service._context = MagicMock()
        service._context.github = None
        assert service.github is None

        # With initialization and github
        mock_github = MagicMock()
        service._context.github = mock_github
        assert service.github is mock_github

    def test_github_property_error(self):
        """Test the github property when an error occurs."""
        service = TeachingService()
        service._context = MagicMock()
        service._context.github = MagicMock(side_effect=QuackError("GitHub error"))
        assert service.github is None

    def test_integrate_with_gamification(self, mock_gamification_service):
        """Test integration with gamification."""
        service = TeachingService()

        # Test module completion
        service._integrate_with_gamification(
            "module_completion",
            course_id="course-1",
            module_id="module-1",
            module_name="Test Module",
        )
        mock_gamification_service.return_value.handle_module_completion.assert_called_once_with(
            course_id="course-1", module_id="module-1", module_name="Test Module"
        )

        # Test course completion
        service._integrate_with_gamification(
            "course_completion", course_id="course-1", course_name="Test Course"
        )
        mock_gamification_service.return_value.handle_course_completion.assert_called_once_with(
            course_id="course-1", course_name="Test Course"
        )

        # Test assignment completion
        service._integrate_with_gamification(
            "assignment_completion",
            assignment_id="assignment-1",
            assignment_name="Test Assignment",
            score=85.0,
            max_score=100.0,
        )
        mock_gamification_service.return_value.handle_assignment_completion.assert_called_once_with(
            assignment_id="assignment-1",
            assignment_name="Test Assignment",
            score=85.0,
            max_score=100.0,
        )

        # Test feedback submission
        service._integrate_with_gamification(
            "feedback_submission",
            feedback_id="feedback-1",
            context="Assignment feedback",
        )
        mock_gamification_service.return_value.handle_feedback_submission.assert_called_once_with(
            feedback_id="feedback-1", context="Assignment feedback"
        )

    def test_integrate_with_gamification_error(self, mock_gamification_service):
        """Test integration with gamification when an error occurs."""
        service = TeachingService()
        mock_gamification_service.return_value.handle_module_completion.side_effect = (
            Exception("Gamification error")
        )

        # Should not raise an exception
        service._integrate_with_gamification(
            "module_completion",
            course_id="course-1",
            module_id="module-1",
            module_name="Test Module",
        )

    def test_ensure_repo_exists_not_initialized(self):
        """Test ensure_repo_exists when service is not initialized."""
        service = TeachingService()
        result = service.ensure_repo_exists("repo-name")

        assert not result.success
        assert "Teaching service not initialized" in result.error

    def test_ensure_repo_exists_no_github(self):
        """Test ensure_repo_exists when GitHub integration is not available."""
        service = TeachingService()
        service._context = MagicMock()
        service._github = None

        result = service.ensure_repo_exists("repo-name")

        assert not result.success
        assert "GitHub integration not available" in result.error

    def test_ensure_repo_exists_success(self, mock_github):
        """Test successful ensure_repo_exists."""
        service = TeachingService()
        service._context = MagicMock()
        service._context.config.github.organization = "test-org"
        service._github = mock_github

        # Mock get_repo to return success
        mock_repo = MagicMock()
        mock_github.get_repo.return_value = TeachingResult(
            success=True, content=mock_repo
        )

        result = service.ensure_repo_exists("repo-name")

        assert result.success
        assert result.content == mock_repo
        mock_github.get_repo.assert_called_once_with("test-org/repo-name")

    def test_ensure_repo_exists_not_found_auto_create_disabled(self, mock_github):
        """Test ensure_repo_exists when repo not found and auto-creation disabled."""
        service = TeachingService()
        service._context = MagicMock()
        service._context.config.github.organization = "test-org"
        service._context.config.github.auto_create_repos = False
        service._github = mock_github

        # Mock get_repo to return failure
        mock_github.get_repo.return_value = TeachingResult(
            success=False, error="Repo not found"
        )

        result = service.ensure_repo_exists("repo-name")

        assert not result.success
        assert "auto-creation is disabled" in result.error

    def test_ensure_repo_exists_not_found_auto_create_enabled(self, mock_github):
        """Test ensure_repo_exists when repo not found and auto-creation enabled."""
        service = TeachingService()
        service._context = MagicMock()
        service._context.config.github.organization = "test-org"
        service._context.config.github.auto_create_repos = True
        service._github = mock_github

        # Mock get_repo to return failure
        mock_github.get_repo.return_value = TeachingResult(
            success=False, error="Repo not found"
        )

        result = service.ensure_repo_exists("repo-name")

        assert not result.success
        assert "not yet implemented" in result.message

    def test_ensure_repo_exists_error(self, mock_github):
        """Test ensure_repo_exists when an error occurs."""
        service = TeachingService()
        service._context = MagicMock()
        service._context.config.github.organization = "test-org"
        service._github = mock_github

        # Mock get_repo to raise an exception
        mock_github.get_repo.side_effect = Exception("GitHub error")

        result = service.ensure_repo_exists("repo-name")

        assert not result.success
        assert "GitHub error" in result.error

    def test_create_assignment_from_template_not_initialized(self):
        """Test create_assignment_from_template when service is not initialized."""
        service = TeachingService()
        result = service.create_assignment_from_template(
            "Assignment", "template-repo", students=["student1"]
        )

        assert not result.success
        assert "Teaching service not initialized" in result.error

    def test_create_assignment_from_template_no_github(self):
        """Test create_assignment_from_template when GitHub integration is not available."""
        service = TeachingService()
        service._context = MagicMock()
        service._github = None

        result = service.create_assignment_from_template(
            "Assignment", "template-repo", students=["student1"]
        )

        assert not result.success
        assert "GitHub integration not available" in result.error

    def test_create_assignment_from_template_template_not_found(self, mock_github):
        """Test create_assignment_from_template when template repo not found."""
        service = TeachingService()
        service._context = MagicMock()
        service._context.config.github.organization = "test-org"
        service._github = mock_github

        # Mock get_repo to return failure for template
        mock_github.get_repo.return_value = TeachingResult(
            success=False, error="Template not found"
        )

        result = service.create_assignment_from_template(
            "Assignment", "template-repo", students=["student1"]
        )

        assert not result.success
        assert "Template repository" in result.error

    def test_create_assignment_from_template_no_students(self, mock_github):
        """Test create_assignment_from_template when no students provided."""
        service = TeachingService()
        service._context = MagicMock()
        service._context.config.github.organization = "test-org"
        service._github = mock_github

        # Mock get_repo to return success for template
        mock_github.get_repo.return_value = TeachingResult(
            success=True, content=MagicMock()
        )

        result = service.create_assignment_from_template("Assignment", "template-repo")

        assert not result.success
        assert "Student list not provided" in result.error

    def test_create_assignment_from_template_success(
        self, mock_github, mock_gamification_service
    ):
        """Test successful create_assignment_from_template."""
        service = TeachingService()
        service._context = MagicMock()
        service._context.config.github.organization = "test-org"
        service._github = mock_github

        # Mock get_repo to return success for template
        mock_template = MagicMock()
        mock_github.get_repo.return_value = TeachingResult(
            success=True, content=mock_template
        )

        # Mock get_repo for student repos
        student_repos = []
        for i in range(2):
            repo = MagicMock()
            student_repos.append(repo)
            mock_github.get_repo.side_effect = [
                TeachingResult(success=True, content=mock_template),  # Template repo
                TeachingResult(
                    success=True, content=student_repos[0]
                ),  # Student 1 repo
                TeachingResult(
                    success=True, content=student_repos[1]
                ),  # Student 2 repo
            ]

        result = service.create_assignment_from_template(
            "Test Assignment", "template-repo", students=["student1", "student2"]
        )

        assert result.success
        assert "Successfully created 2 assignment repositories" in result.message
        assert result.repositories == student_repos

        # Verify gamification integration
        mock_gamification_service.return_value.handle_assignment_completion.assert_called_once()

    def test_create_assignment_from_template_partial_success(
        self, mock_github, mock_gamification_service
    ):
        """Test create_assignment_from_template with some failures."""
        service = TeachingService()
        service._context = MagicMock()
        service._context.config.github.organization = "test-org"
        service._github = mock_github

        # Mock get_repo to return success for template and first student, failure for second student
        mock_template = MagicMock()
        mock_student1_repo = MagicMock()
        mock_github.get_repo.side_effect = [
            TeachingResult(success=True, content=mock_template),  # Template repo
            TeachingResult(success=True, content=mock_student1_repo),  # Student 1 repo
            Exception("GitHub error"),  # Student 2 repo fails
        ]

        result = service.create_assignment_from_template(
            "Test Assignment", "template-repo", students=["student1", "student2"]
        )

        assert not result.success
        assert "Successfully created 1 repositories" in result.message
        assert result.repositories == [mock_student1_repo]
        assert "student2" in result.failed_students

        # Verify gamification integration was not called (no students succeeded)
        mock_gamification_service.return_value.handle_assignment_creation.assert_not_called()

    def test_create_assignment_from_template_all_failures(self, mock_github):
        """Test create_assignment_from_template when all students fail."""
        service = TeachingService()
        service._context = MagicMock()
        service._context.config.github.organization = "test-org"
        service._github = mock_github

        # Mock get_repo to return success for template but failure for students
        mock_template = MagicMock()
        mock_github.get_repo.side_effect = [
            TeachingResult(success=True, content=mock_template),  # Template repo
            Exception("GitHub error"),  # Student 1 repo fails
            Exception("GitHub error"),  # Student 2 repo fails
        ]

        result = service.create_assignment_from_template(
            "Test Assignment", "template-repo", students=["student1", "student2"]
        )

        assert not result.success
        assert "No repositories created" in result.error
        assert result.repositories == []
        assert set(result.failed_students) == {"student1", "student2"}

    def test_find_student_submissions_not_initialized(self):
        """Test find_student_submissions when service is not initialized."""
        service = TeachingService()
        result = service.find_student_submissions("assignment", "student")

        assert not result.success
        assert "Teaching service not initialized" in result.error

    def test_find_student_submissions_no_github(self):
        """Test find_student_submissions when GitHub integration is not available."""
        service = TeachingService()
        service._context = MagicMock()
        service._github = None

        result = service.find_student_submissions("assignment", "student")

        assert not result.success
        assert "GitHub integration not available" in result.error

    def test_find_student_submissions_success(self, mock_github):
        """Test successful find_student_submissions."""
        service = TeachingService()
        service._context = MagicMock()
        service._context.config.github.organization = "test-org"
        service._github = mock_github

        # Mock get_repo to return success
        mock_repo = MagicMock()
        mock_github.get_repo.return_value = TeachingResult(
            success=True, content=mock_repo
        )

        result = service.find_student_submissions("Test Assignment", "student1")

        assert result.success
        assert result.content == mock_repo
        mock_github.get_repo.assert_called_once_with(
            "test-org/test-assignment-student1"
        )

    def test_find_student_submissions_not_found(self, mock_github):
        """Test find_student_submissions when repo not found."""
        service = TeachingService()
        service._context = MagicMock()
        service._context.config.github.organization = "test-org"
        service._github = mock_github

        # Mock get_repo to return failure
        mock_github.get_repo.return_value = TeachingResult(
            success=False, error="Repo not found"
        )

        result = service.find_student_submissions("Test Assignment", "student1")

        assert not result.success
        assert "No repository found" in result.message

    def test_find_student_submissions_no_student(self, mock_github):
        """Test find_student_submissions without specifying a student."""
        service = TeachingService()
        service._context = MagicMock()
        service._context.config.github.organization = "test-org"
        service._github = mock_github

        result = service.find_student_submissions("Test Assignment")

        assert not result.success
        assert "Finding all submissions is not yet implemented" in result.error

    def test_record_module_completion(self, mock_gamification_service):
        """Test record_module_completion."""
        service = TeachingService()

        # Not initialized
        result = service.record_module_completion("course-1", "module-1", "Test Module")
        assert not result.success
        assert "Teaching service not initialized" in result.error

        # Initialized
        service._context = MagicMock()
        result = service.record_module_completion("course-1", "module-1", "Test Module")

        assert result.success
        assert "Successfully recorded completion" in result.message
        mock_gamification_service.return_value.handle_module_completion.assert_called_once_with(
            course_id="course-1", module_id="module-1", module_name="Test Module"
        )

    def test_record_course_completion(self, mock_gamification_service):
        """Test record_course_completion."""
        service = TeachingService()

        # Not initialized
        result = service.record_course_completion("course-1", "Test Course")
        assert not result.success
        assert "Teaching service not initialized" in result.error

        # Initialized
        service._context = MagicMock()
        result = service.record_course_completion("course-1", "Test Course")

        assert result.success
        assert "Successfully recorded completion" in result.message
        mock_gamification_service.return_value.handle_course_completion.assert_called_once_with(
            course_id="course-1", course_name="Test Course"
        )

    def test_grade_student_assignment(self, mock_gamification_service):
        """Test grade_student_assignment."""
        service = TeachingService()

        # Not initialized
        result = service.grade_student_assignment("assignment-1", "student1", 85.0)
        assert not result.success
        assert "Teaching service not initialized" in result.error

        # Initialized
        service._context = MagicMock()
        result = service.grade_student_assignment(
            "assignment-1", "student1", 85.0, "Good work"
        )

        assert result.success
        assert "Successfully graded assignment" in result.message
        mock_gamification_service.return_value.handle_assignment_completion.assert_called_once()

    def test_resolve_file_path_absolute(self):
        """Test _resolve_file_path with absolute path."""
        path = "/absolute/path"
        resolved = TeachingService._resolve_file_path(path)
        assert resolved == Path(path)

    def test_resolve_file_path_relative(self, mock_resolver):
        """Test _resolve_file_path with relative path."""
        mock_resolver.get_project_root.return_value = Path("/project/root")

        path = "relative/path"
        resolved = TeachingService._resolve_file_path(path)
        assert resolved == Path("/project/root/relative/path")

    def test_resolve_file_path_relative_no_project_root(self, mock_resolver):
        """Test _resolve_file_path with relative path when project root fails."""
        mock_resolver.get_project_root.side_effect = Exception("Project root not found")

        with patch("pathlib.Path.resolve") as mock_resolve:
            mock_resolve.return_value = Path("/resolved/path")

            path = "relative/path"
            resolved = TeachingService._resolve_file_path(path)
            assert str(resolved).startswith("/resolved/")

    def test_save_config_not_initialized(self):
        """Test save_config when service is not initialized."""
        service = TeachingService()
        result = service.save_config()

        assert not result.success
        assert "Teaching service not initialized" in result.error

    def test_save_config_success(self, mock_fs):
        """Test successful save_config."""
        service = TeachingService()
        service._context = MagicMock()
        service._context.base_dir = Path("/base/dir")
        service._context.config.model_dump.return_value = {"key": "value"}

        # Mock write_yaml to return success
        mock_fs.write_yaml.return_value = MagicMock(success=True)

        # Test with default path
        result = service.save_config()

        assert result.success
        assert "Configuration saved" in result.message
        mock_fs.write_yaml.assert_called_once_with(
            "/base/dir/teaching_config.yaml", {"key": "value"}
        )

    def test_save_config_custom_path(self, mock_fs):
        """Test save_config with custom path."""
        service = TeachingService()
        service._context = MagicMock()
        service._context.config.model_dump.return_value = {"key": "value"}

        # Mock write_yaml to return success
        mock_fs.write_yaml.return_value = MagicMock(success=True)

        # Test with custom path
        with patch.object(TeachingService, "_resolve_file_path") as mock_resolve:
            mock_resolve.return_value = Path("/custom/path/config.yaml")
            result = service.save_config("/custom/path/config.yaml")

            assert result.success
            assert "Configuration saved" in result.message
            mock_fs.write_yaml.assert_called_once_with(
                "/custom/path/config.yaml", {"key": "value"}
            )

    def test_save_config_error(self, mock_fs):
        """Test save_config when write fails."""
        service = TeachingService()
        service._context = MagicMock()
        service._context.base_dir = Path("/base/dir")
        service._context.config.model_dump.return_value = {"key": "value"}

        # Mock write_yaml to return failure
        mock_fs.write_yaml.return_value = MagicMock(success=False, error="Write error")

        result = service.save_config()

        assert not result.success
        assert "Could not save configuration" in result.message
        assert "Write error" in result.error

    def test_save_config_exception(self, mock_fs):
        """Test save_config when an exception occurs."""
        service = TeachingService()
        service._context = MagicMock()
        service._context.base_dir = Path("/base/dir")
        service._context.config.model_dump.return_value = {"key": "value"}

        # Mock write_yaml to raise an exception
        mock_fs.write_yaml.side_effect = Exception("Unexpected error")

        result = service.save_config()

        assert not result.success
        assert "Failed to save configuration" in result.message
        assert "Unexpected error" in result.error
