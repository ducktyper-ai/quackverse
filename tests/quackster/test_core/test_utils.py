# tests/quackster/test_core/test_utils.py
"""
Tests for the QuackCore quackster core api module.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from quackster.core.models import UserProgress
from quackster.core.utils import (
    backup_progress,
    create_new_progress,
    get_github_username,
    get_progress_file_path,
    get_user_data_dir,
    load_progress,
    reset_progress,
    save_progress,
)


class TestGetUserDataDir:
    """Tests for the get_user_data_dir function."""

    def test_default_directory(self, mock_fs):
        """Test getting the default user data directory."""
        # Setup mock for fs.expand_user_vars and fs.create_directory
        mock_fs._expand_user_vars.return_value = "/home/user/.quack"
        mock_fs._create_directory.return_value = MagicMock(success=True)

        # Call the function
        result = get_user_data_dir()

        # Check the result and mock calls
        assert result == Path("/home/user/.quack")
        mock_fs._expand_user_vars.assert_called_once_with("~/.quack")
        mock_fs._create_directory.assert_called_once_with(
            Path("/home/user/.quack"), exist_ok=True
        )

    def test_custom_directory_from_env(self, mock_fs, monkeypatch):
        """Test getting a custom user data directory from environment variable."""
        # Set environment variable
        monkeypatch.setenv("QUACK_DATA_DIR", "~/custom_data")

        # Setup mock for fs.expand_user_vars and fs.create_directory
        mock_fs._expand_user_vars.return_value = "/home/user/custom_data"
        mock_fs._create_directory.return_value = MagicMock(success=True)

        # Call the function
        result = get_user_data_dir()

        # Check the result and mock calls
        assert result == Path("/home/user/custom_data")
        mock_fs._expand_user_vars.assert_called_once_with("~/custom_data")
        mock_fs._create_directory.assert_called_once_with(
            Path("/home/user/custom_data"), exist_ok=True
        )


class TestGetProgressFilePath:
    """Tests for the get_progress_file_path function."""

    def test_default_file_path(self, mock_fs):
        """Test getting the default progress file path."""
        # Setup mock for get_user_data_dir
        with patch("quackster.core.api.get_user_data_dir") as mock_get_dir:
            mock_get_dir.return_value = Path("/home/user/.quack")

            # Call the function
            result = get_progress_file_path()

            # Check the result
            assert result == Path("/home/user/.quack/ducktyper_user.json")

    def test_custom_file_name_from_env(self, mock_fs, monkeypatch):
        """Test getting a custom progress file path from environment variable."""
        # Set environment variable
        monkeypatch.setenv("QUACK_PROGRESS_FILE", "custom_progress.json")

        # Setup mock for get_user_data_dir
        with patch("quackster.core.api.get_user_data_dir") as mock_get_dir:
            mock_get_dir.return_value = Path("/home/user/.quack")

            # Call the function
            result = get_progress_file_path()

            # Check the result
            assert result == Path("/home/user/.quack/custom_progress.json")


class TestGetGithubUsername:
    """Tests for the get_github_username function."""

    def test_from_env_variable(self, monkeypatch):
        """Test getting the GitHub username from environment variable."""
        # Set environment variable
        monkeypatch.setenv("GITHUB_USERNAME", "test-user")

        # Call the function
        result = get_github_username()

        # Check the result
        assert result == "test-user"

    def test_from_git_config(self, monkeypatch):
        """Test getting the GitHub username from git config."""
        # Clear environment variable
        monkeypatch.delenv("GITHUB_USERNAME", raising=False)

        # Mock subprocess.run to return a git username
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "git-user\n"
            mock_run.return_value = mock_result

            # Call the function
            result = get_github_username()

            # Check the result
            assert result == "git-user"
            mock_run.assert_called_once_with(
                ["git", "config", "user.name"],
                capture_output=True,
                text=True,
                check=False,
            )

    def test_from_git_config_failure(self, monkeypatch):
        """Test handling git config failure."""
        # Clear environment variable
        monkeypatch.delenv("GITHUB_USERNAME", raising=False)

        # Mock subprocess.run to fail
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Git not found")

            # Mock input to provide a username
            with patch("builtins.input", return_value="input-user"):
                # Call the function
                result = get_github_username()

                # Check the result
                assert result == "input-user"

    def test_from_user_input(self, monkeypatch):
        """Test getting the GitHub username from user input."""
        # Clear environment variable
        monkeypatch.delenv("GITHUB_USERNAME", raising=False)

        # Mock subprocess.run to return empty result
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_run.return_value = mock_result

            # Mock input to provide a username
            with patch("builtins.input", return_value="input-user"):
                # Call the function
                result = get_github_username()

                # Check the result
                assert result == "input-user"

    def test_fallback_to_system_username(self, monkeypatch):
        """Test falling back to system username."""
        # Clear environment variable
        monkeypatch.delenv("GITHUB_USERNAME", raising=False)

        # Mock subprocess.run to return empty result
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_run.return_value = mock_result

            # Mock input to raise exception
            with patch("builtins.input", side_effect=Exception("No input")):
                # Mock getpass.getuser
                with patch("getpass.getuser", return_value="system-user"):
                    # Call the function
                    result = get_github_username()

                    # Check the result
                    assert result == "system-user"


class TestLoadProgress:
    """Tests for the load_progress function."""

    def test_load_existing_progress(self, mock_fs, mock_logger):
        """Test loading progress from an existing file."""
        # Setup mocks
        with patch("quackster.core.api.get_progress_file_path") as mock_get_path:
            mock_get_path.return_value = Path("/home/user/.quack/ducktyper_user.json")

            # Mock fs.get_file_info to indicate file exists
            mock_fs._get_file_info.return_value = MagicMock(success=True, exists=True)

            # Mock fs.read_json to return progress data
            progress_data = {
                "github_username": "test-user",
                "display_name": "Test User",
                "xp": 1000,
                "level": 2,
                "badges": [{"id": "badge1", "earned_at": "2023-01-01T12:00:00"}],
                "completed_quest_ids": ["quest1", "quest2"],
                "current_streak": 5,
                "longest_streak": 10,
                "last_active_date": "2023-01-15",
                "metadata": {"key": "value"},
            }
            mock_fs._read_json.return_value = MagicMock(
                success=True, data=progress_data
            )

            # Call the function
            result = load_progress()

            # Check the result
            assert isinstance(result, UserProgress)
            assert result.github_username == "test-user"
            assert result.display_name == "Test User"
            assert result.xp == 1000
            assert result.level == 2
            assert len(result.badges) == 1
            assert result.badges[0].id == "badge1"
            assert len(result.completed_quest_ids) == 2
            assert "quest1" in result.completed_quest_ids
            assert result.current_streak == 5
            assert result.longest_streak == 10
            assert result.metadata == {"key": "value"}

            # Verify mock calls
            mock_fs._get_file_info.assert_called_once_with(
                Path("/home/user/.quack/ducktyper_user.json")
            )
            mock_fs._read_json.assert_called_once_with(
                Path("/home/user/.quack/ducktyper_user.json")
            )

            # Verify log message
            assert any(
                "Loaded user progress" in str(call)
                for call in mock_logger.debug.call_args_list
            )

    def test_load_nonexistent_file(self, mock_fs, mock_logger):
        """Test loading progress when the file doesn't exist."""
        # Setup mocks
        with patch("quackster.core.api.get_progress_file_path") as mock_get_path:
            mock_get_path.return_value = Path("/home/user/.quack/ducktyper_user.json")

            # Mock fs.get_file_info to indicate file doesn't exist
            mock_fs._get_file_info.return_value = MagicMock(success=True, exists=False)

            # Mock create_new_progress
            with patch(
                "quackster.core.api.create_new_progress"
            ) as mock_create_progress:
                mock_progress = UserProgress(github_username="new-user")
                mock_create_progress.return_value = mock_progress

                # Call the function
                result = load_progress()

                # Check the result
                assert result is mock_progress

                # Verify mock calls
                mock_fs._get_file_info.assert_called_once_with(
                    Path("/home/user/.quack/ducktyper_user.json")
                )
                mock_create_progress.assert_called_once()

                # Verify log message
                assert any(
                    "Progress file not found" in str(call)
                    for call in mock_logger.debug.call_args_list
                )

    def test_load_invalid_file(self, mock_fs, mock_logger):
        """Test loading progress when the file has invalid format."""
        # Setup mocks
        with patch("quackster.core.api.get_progress_file_path") as mock_get_path:
            mock_get_path.return_value = Path("/home/user/.quack/ducktyper_user.json")

            # Mock fs.get_file_info to indicate file exists
            mock_fs._get_file_info.return_value = MagicMock(success=True, exists=True)

            # Mock fs.read_json to return error
            mock_fs._read_json.return_value = MagicMock(
                success=False, error="Invalid JSON"
            )

            # Mock create_new_progress
            with patch(
                "quackster.core.api.create_new_progress"
            ) as mock_create_progress:
                mock_progress = UserProgress(github_username="new-user")
                mock_create_progress.return_value = mock_progress

                # Call the function
                result = load_progress()

                # Check the result
                assert result is mock_progress

                # Verify mock calls
                mock_fs._get_file_info.assert_called_once_with(
                    Path("/home/user/.quack/ducktyper_user.json")
                )
                mock_fs._read_json.assert_called_once_with(
                    Path("/home/user/.quack/ducktyper_user.json")
                )
                mock_create_progress.assert_called_once()

                # Verify log message
                assert any(
                    "Failed to read progress file" in str(call)
                    for call in mock_logger.warning.call_args_list
                )

    def test_load_validation_error(self, mock_fs, mock_logger):
        """Test loading progress when the file content is invalid."""
        # Setup mocks
        with patch("quackster.core.api.get_progress_file_path") as mock_get_path:
            mock_get_path.return_value = Path("/home/user/.quack/ducktyper_user.json")

            # Mock fs.get_file_info to indicate file exists
            mock_fs._get_file_info.return_value = MagicMock(success=True, exists=True)

            # Mock fs.read_json to return invalid data
            invalid_data = {"invalid_field": "value"}  # Missing required fields
            mock_fs._read_json.return_value = MagicMock(success=True, data=invalid_data)

            # Mock create_new_progress
            with patch(
                "quackster.core.api.create_new_progress"
            ) as mock_create_progress:
                mock_progress = UserProgress(github_username="new-user")
                mock_create_progress.return_value = mock_progress

                # Call the function
                result = load_progress()

                # Check the result
                assert result is mock_progress

                # Verify mock calls
                mock_fs._get_file_info.assert_called_once_with(
                    Path("/home/user/.quack/ducktyper_user.json")
                )
                mock_fs._read_json.assert_called_once_with(
                    Path("/home/user/.quack/ducktyper_user.json")
                )
                mock_create_progress.assert_called_once()

                # Verify log message
                assert any(
                    "Error loading progress file" in str(call)
                    for call in mock_logger.warning.call_args_list
                )


class TestSaveProgress:
    """Tests for the save_progress function."""

    def test_save_progress_success(self, mock_fs, mock_logger):
        """Test saving progress successfully."""
        # Create test progress
        progress = UserProgress(
            github_username="test-user",
            display_name="Test User",
            xp=1000,
            level=2,
            completed_quest_ids=["quest1", "quest2"],
        )

        # Setup mocks
        with patch("quackster.core.api.get_progress_file_path") as mock_get_path:
            mock_get_path.return_value = Path("/home/user/.quack/ducktyper_user.json")

            # Mock fs.write_json to succeed
            mock_fs._write_json.return_value = MagicMock(success=True)

            # Call the function
            result = save_progress(progress)

            # Check the result
            assert result is True

            # Verify mock calls
            mock_fs._write_json.assert_called_once_with(
                Path("/home/user/.quack/ducktyper_user.json"), progress.model_dump()
            )

            # Verify log message
            assert any(
                "Saved user progress" in str(call)
                for call in mock_logger.debug.call_args_list
            )

    def test_save_progress_failure(self, mock_fs, mock_logger):
        """Test handling save failure."""
        # Create test progress
        progress = UserProgress(github_username="test-user")

        # Setup mocks
        with patch("quackster.core.api.get_progress_file_path") as mock_get_path:
            mock_get_path.return_value = Path("/home/user/.quack/ducktyper_user.json")

            # Mock fs.write_json to fail
            mock_fs._write_json.return_value = MagicMock(
                success=False, error="Write error"
            )

            # Call the function
            result = save_progress(progress)

            # Check the result
            assert result is False

            # Verify mock calls
            mock_fs._write_json.assert_called_once_with(
                Path("/home/user/.quack/ducktyper_user.json"), progress.model_dump()
            )

            # Verify log message
            assert any(
                "Failed to save progress file" in str(call)
                for call in mock_logger.error.call_args_list
            )

    def test_save_progress_exception(self, mock_fs, mock_logger):
        """Test handling unexpected exception."""
        # Create test progress
        progress = UserProgress(github_username="test-user")

        # Setup mocks
        with patch("quackster.core.api.get_progress_file_path") as mock_get_path:
            mock_get_path.return_value = Path("/home/user/.quack/ducktyper_user.json")

            # Mock fs.write_json to raise exception
            mock_fs._write_json.side_effect = Exception("Unexpected error")

            # Call the function
            result = save_progress(progress)

            # Check the result
            assert result is False

            # Verify mock calls
            mock_fs._write_json.assert_called_once_with(
                Path("/home/user/.quack/ducktyper_user.json"), progress.model_dump()
            )

            # Verify log message
            assert any(
                "Error saving progress file" in str(call)
                for call in mock_logger.error.call_args_list
            )


class TestCreateNewProgress:
    """Tests for the create_new_progress function."""

    def test_create_new_progress(self):
        """Test creating new progress."""
        # Setup mocks
        with patch("quackster.core.api.get_github_username") as mock_get_username:
            mock_get_username.return_value = "test-user"

            # Mock save_progress
            with patch("quackster.core.api.save_progress") as mock_save:
                mock_save.return_value = True

                # Call the function
                result = create_new_progress()

                # Check the result
                assert isinstance(result, UserProgress)
                assert result.github_username == "test-user"
                assert result.xp == 0
                assert result.level == 0
                assert result.completed_quest_ids == []

                # Verify mock calls
                mock_get_username.assert_called_once()
                mock_save.assert_called_once_with(result)


class TestResetProgress:
    """Tests for the reset_progress function."""

    def test_reset_existing_progress(self, mock_fs, mock_logger):
        """Test resetting existing progress."""
        # Setup mocks
        with patch("quackster.core.api.get_progress_file_path") as mock_get_path:
            mock_get_path.return_value = Path("/home/user/.quack/ducktyper_user.json")

            # Mock fs.get_file_info to indicate file exists
            mock_fs._get_file_info.return_value = MagicMock(success=True, exists=True)

            # Mock fs.delete to succeed
            mock_fs._delete.return_value = MagicMock(success=True)

            # Call the function
            result = reset_progress()

            # Check the result
            assert result is True

            # Verify mock calls
            mock_fs._get_file_info.assert_called_once_with(
                Path("/home/user/.quack/ducktyper_user.json")
            )
            mock_fs._delete.assert_called_once_with(
                Path("/home/user/.quack/ducktyper_user.json")
            )

            # Verify log message
            assert any(
                "Reset user progress" in str(call)
                for call in mock_logger.info.call_args_list
            )

    def test_reset_nonexistent_progress(self, mock_fs, mock_logger):
        """Test resetting when progress file doesn't exist."""
        # Setup mocks
        with patch("quackster.core.api.get_progress_file_path") as mock_get_path:
            mock_get_path.return_value = Path("/home/user/.quack/ducktyper_user.json")

            # Mock fs.get_file_info to indicate file doesn't exist
            mock_fs._get_file_info.return_value = MagicMock(success=True, exists=False)

            # Call the function
            result = reset_progress()

            # Check the result
            assert result is True

            # Verify mock calls
            mock_fs._get_file_info.assert_called_once_with(
                Path("/home/user/.quack/ducktyper_user.json")
            )
            mock_fs._delete.assert_not_called()

            # Verify log message
            assert any(
                "No progress file to reset" in str(call)
                for call in mock_logger.debug.call_args_list
            )

    def test_reset_progress_failure(self, mock_fs, mock_logger):
        """Test handling reset failure."""
        # Setup mocks
        with patch("quackster.core.api.get_progress_file_path") as mock_get_path:
            mock_get_path.return_value = Path("/home/user/.quack/ducktyper_user.json")

            # Mock fs.get_file_info to indicate file exists
            mock_fs._get_file_info.return_value = MagicMock(success=True, exists=True)

            # Mock fs.delete to fail
            mock_fs._delete.return_value = MagicMock(success=False, error="Delete error")

            # Call the function
            result = reset_progress()

            # Check the result
            assert result is False

            # Verify mock calls
            mock_fs._get_file_info.assert_called_once_with(
                Path("/home/user/.quack/ducktyper_user.json")
            )
            mock_fs._delete.assert_called_once_with(
                Path("/home/user/.quack/ducktyper_user.json")
            )

            # Verify log message
            assert any(
                "Failed to delete progress file" in str(call)
                for call in mock_logger.error.call_args_list
            )


class TestBackupProgress:
    """Tests for the backup_progress function."""

    def test_backup_with_default_name(self, mock_fs, mock_logger):
        """Test backing up progress with default name."""
        # Setup mocks
        with patch("quackster.core.api.get_progress_file_path") as mock_get_path:
            mock_get_path.return_value = Path("/home/user/.quack/ducktyper_user.json")

            # Mock fs.get_file_info to indicate file exists
            mock_fs._get_file_info.return_value = MagicMock(success=True, exists=True)

            # Mock get_user_data_dir
            with patch("quackster.core.api.get_user_data_dir") as mock_get_dir:
                mock_get_dir.return_value = Path("/home/user/.quack")

                # Mock fs.copy to succeed
                mock_fs._copy.return_value = MagicMock(success=True)

                # Mock datetime
                with patch("datetime.datetime") as mock_datetime:
                    mock_now = MagicMock()
                    mock_now.strftime.return_value = "20230101_120000"
                    mock_datetime.now.return_value = mock_now

                    # Call the function
                    result = backup_progress()

                    # Check the result
                    assert result is True

                    # Verify mock calls
                    mock_fs._get_file_info.assert_called_once_with(
                        Path("/home/user/.quack/ducktyper_user.json")
                    )
                    mock_fs._copy.assert_called_once_with(
                        Path("/home/user/.quack/ducktyper_user.json"),
                        Path("/home/user/.quack/ducktyper_user_20230101_120000.json"),
                    )

                    # Verify log message
                    assert any(
                        "Created backup of user progress" in str(call)
                        for call in mock_logger.info.call_args_list
                    )

    def test_backup_with_custom_name(self, mock_fs, mock_logger):
        """Test backing up progress with custom name."""
        # Setup mocks
        with patch("quackster.core.api.get_progress_file_path") as mock_get_path:
            mock_get_path.return_value = Path("/home/user/.quack/ducktyper_user.json")

            # Mock fs.get_file_info to indicate file exists
            mock_fs._get_file_info.return_value = MagicMock(success=True, exists=True)

            # Mock get_user_data_dir
            with patch("quackster.core.api.get_user_data_dir") as mock_get_dir:
                mock_get_dir.return_value = Path("/home/user/.quack")

                # Mock fs.copy to succeed
                mock_fs._copy.return_value = MagicMock(success=True)

                # Call the function with custom name
                result = backup_progress("custom_backup.json")

                # Check the result
                assert result is True

                # Verify mock calls
                mock_fs._get_file_info.assert_called_once_with(
                    Path("/home/user/.quack/ducktyper_user.json")
                )
                mock_fs._copy.assert_called_once_with(
                    Path("/home/user/.quack/ducktyper_user.json"),
                    Path("/home/user/.quack/custom_backup.json"),
                )

                # Verify log message
                assert any(
                    "Created backup of user progress" in str(call)
                    for call in mock_logger.info.call_args_list
                )

    def test_backup_nonexistent_file(self, mock_fs, mock_logger):
        """Test backing up when progress file doesn't exist."""
        # Setup mocks
        with patch("quackster.core.api.get_progress_file_path") as mock_get_path:
            mock_get_path.return_value = Path("/home/user/.quack/ducktyper_user.json")

            # Mock fs.get_file_info to indicate file doesn't exist
            mock_fs._get_file_info.return_value = MagicMock(success=True, exists=False)

            # Call the function
            result = backup_progress()

            # Check the result
            assert result is False

            # Verify mock calls
            mock_fs._get_file_info.assert_called_once_with(
                Path("/home/user/.quack/ducktyper_user.json")
            )
            mock_fs._copy.assert_not_called()

            # Verify log message
            assert any(
                "No progress file to backup" in str(call)
                for call in mock_logger.debug.call_args_list
            )

    def test_backup_failure(self, mock_fs, mock_logger):
        """Test handling backup failure."""
        # Setup mocks
        with patch("quackster.core.api.get_progress_file_path") as mock_get_path:
            mock_get_path.return_value = Path("/home/user/.quack/ducktyper_user.json")

            # Mock fs.get_file_info to indicate file exists
            mock_fs._get_file_info.return_value = MagicMock(success=True, exists=True)

            # Mock get_user_data_dir
            with patch("quackster.core.api.get_user_data_dir") as mock_get_dir:
                mock_get_dir.return_value = Path("/home/user/.quack")

                # Mock fs.copy to fail
                mock_fs._copy.return_value = MagicMock(success=False, error="Copy error")

                # Call the function
                result = backup_progress()

                # Check the result
                assert result is False

                # Verify mock calls
                mock_fs._get_file_info.assert_called_once_with(
                    Path("/home/user/.quack/ducktyper_user.json")
                )
                mock_fs._copy.assert_called_once()

                # Verify log message
                assert any(
                    "Failed to create backup" in str(call)
                    for call in mock_logger.error.call_args_list
                )
