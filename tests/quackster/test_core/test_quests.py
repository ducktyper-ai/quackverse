# tests/quackster/test_core/test_quests.py
"""
Tests for the quackster utilities module.

This module tests the utility functions in quackster.core.utils.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from quackster.core import utils
from quackster.core.models import UserProgress


class TestTeachingUtils:
    """Tests for quackster utility functions."""

    @patch("quackster.core.utils.os.environ.get")
    @patch("quackster.core.utils.fs.expand_user_vars")
    @patch("quackster.core.utils.Path")
    @patch("quackster.core.utils.fs.create_directory")
    def test_get_user_data_dir_default(
        self, mock_create_dir, mock_path, mock_expand, mock_env_get
    ):
        """Test getting the user data directory with default path."""
        # Setup
        mock_env_get.return_value = None
        mock_expand.return_value = "/home/user/.quack"
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance

        # Act
        result = utils.get_user_data_dir()

        # Assert
        mock_env_get.assert_called_with("QUACK_DATA_DIR")
        mock_expand.assert_called_with(utils.DEFAULT_DATA_DIR)
        mock_path.assert_called_with("/home/user/.quack")
        mock_create_dir.assert_called_with(mock_path_instance, exist_ok=True)
        assert result == mock_path_instance

    @patch("quackster.core.utils.os.environ.get")
    @patch("quackster.core.utils.fs.expand_user_vars")
    @patch("quackster.core.utils.Path")
    @patch("quackster.core.utils.fs.create_directory")
    def test_get_user_data_dir_custom(
        self, mock_create_dir, mock_path, mock_expand, mock_env_get
    ):
        """Test getting the user data directory with custom path."""
        # Setup
        mock_env_get.return_value = "/custom/path"
        mock_expand.return_value = "/custom/path"
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance

        # Act
        result = utils.get_user_data_dir()

        # Assert
        mock_env_get.assert_called_with("QUACK_DATA_DIR")
        mock_expand.assert_called_with("/custom/path")
        mock_path.assert_called_with("/custom/path")
        mock_create_dir.assert_called_with(mock_path_instance, exist_ok=True)
        assert result == mock_path_instance

    def test_get_progress_file_path(self):
        """Test getting the path to the user progress file."""
        # Setup
        mock_data_dir = MagicMock(spec=Path)
        expected_file_path = MagicMock(spec=Path)
        mock_data_dir.__truediv__.return_value = expected_file_path

        # Mock the get_user_data_dir function
        with patch(
            "quackster.core.utils.get_user_data_dir",
            return_value=mock_data_dir,
        ):
            with patch("quackster.core.utils.os.environ.get", return_value=None):
                # Act
                result = utils.get_progress_file_path()

                # Assert
                mock_data_dir.__truediv__.assert_called_with(
                    utils.DEFAULT_PROGRESS_FILE
                )
                assert result == expected_file_path

    @patch("quackster.core.utils.os.environ.get")
    def test_get_github_username_from_env(self, mock_env_get):
        """Test getting GitHub username from environment variable."""
        # Setup
        mock_env_get.return_value = "test-user"

        # Act
        result = utils.get_github_username()

        # Assert
        mock_env_get.assert_called_with("GITHUB_USERNAME")
        assert result == "test-user"

    @patch("quackster.core.utils.os.environ.get")
    @patch("quackster.core.utils.subprocess.run")
    def test_get_github_username_from_git_config(self, mock_run, mock_env_get):
        """Test getting GitHub username from git config."""
        # Setup
        mock_env_get.return_value = None
        mock_run.return_value = MagicMock(returncode=0, stdout="test-user\n", stderr="")

        # Act
        result = utils.get_github_username()

        # Assert
        mock_env_get.assert_called_with("GITHUB_USERNAME")
        mock_run.assert_called_with(
            ["git", "config", "user.name"], capture_output=True, text=True, check=False
        )
        assert result == "test-user"

    @patch("quackster.core.utils.os.environ.get")
    @patch("quackster.core.utils.subprocess.run")
    @patch("builtins.input")
    def test_get_github_username_from_input(self, mock_input, mock_run, mock_env_get):
        """Test getting GitHub username from user input."""
        # Setup
        mock_env_get.return_value = None
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")
        mock_input.return_value = "test-user"

        # Act
        result = utils.get_github_username()

        # Assert
        mock_env_get.assert_called_with("GITHUB_USERNAME")
        mock_run.assert_called_with(
            ["git", "config", "user.name"], capture_output=True, text=True, check=False
        )
        mock_input.assert_called_with("Enter your GitHub username: ")
        assert result == "test-user"

    @patch("quackster.core.utils.os.environ.get")
    @patch("quackster.core.utils.subprocess.run")
    @patch("builtins.input")
    @patch("quackster.core.utils.getpass.getuser")
    def test_get_github_username_fallback(
        self, mock_getuser, mock_input, mock_run, mock_env_get
    ):
        """Test fallback to system username when other methods fail."""
        # Setup
        mock_env_get.return_value = None
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")
        mock_input.side_effect = Exception("Input error")
        mock_getuser.return_value = "system-user"

        # Act
        result = utils.get_github_username()

        # Assert
        mock_env_get.assert_called_with("GITHUB_USERNAME")
        mock_run.assert_called_with(
            ["git", "config", "user.name"], capture_output=True, text=True, check=False
        )
        mock_input.assert_called_with("Enter your GitHub username: ")
        mock_getuser.assert_called_once()
        assert result == "system-user"

    @patch("quackster.core.utils.get_progress_file_path")
    @patch("quackster.core.utils.fs.get_file_info")
    @patch("quackster.core.utils.create_new_progress")
    def test_load_progress_file_not_found(
        self, mock_create_new, mock_get_file_info, mock_get_path
    ):
        """Test loading progress when file doesn't exist."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_get_path.return_value = mock_path
        mock_get_file_info.return_value = MagicMock(
            success=True, exists=False, is_file=False
        )
        expected_progress = UserProgress(github_username="test-user")
        mock_create_new.return_value = expected_progress

        # Act
        result = utils.load_progress()

        # Assert
        mock_get_path.assert_called_once()
        mock_get_file_info.assert_called_with(mock_path)
        mock_create_new.assert_called_once()
        assert result == expected_progress

    @patch("quackster.core.utils.get_progress_file_path")
    @patch("quackster.core.utils.fs.get_file_info")
    @patch("quackster.core.utils.fs.read_json")
    @patch("quackster.core.utils.UserProgress.model_validate")
    @patch("quackster.core.utils.logger")
    def test_load_progress_success(
        self,
        mock_logger,
        mock_validate,
        mock_read_json,
        mock_get_file_info,
        mock_get_path,
    ):
        """Test successfully loading progress from file."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_get_path.return_value = mock_path
        mock_get_file_info.return_value = MagicMock(
            success=True, exists=True, is_file=True
        )

        progress_data = {
            "github_username": "test-user",
            "xp": 100,
            "completed_quest_ids": ["quest1", "quest2"],
        }
        mock_read_json.return_value = MagicMock(success=True, data=progress_data)

        expected_progress = UserProgress(
            github_username="test-user",
            xp=100,
            completed_quest_ids=["quest1", "quest2"],
        )
        mock_validate.return_value = expected_progress

        # Act
        result = utils.load_progress()

        # Assert
        mock_get_path.assert_called_once()
        mock_get_file_info.assert_called_with(mock_path)
        mock_read_json.assert_called_with(mock_path)
        mock_validate.assert_called_with(progress_data)
        mock_logger.debug.assert_called()
        assert result == expected_progress

    @patch("quackster.core.utils.get_progress_file_path")
    @patch("quackster.core.utils.fs.get_file_info")
    @patch("quackster.core.utils.fs.read_json")
    @patch("quackster.core.utils.create_new_progress")
    @patch("quackster.core.utils.logger")
    def test_load_progress_read_error(
        self,
        mock_logger,
        mock_create_new,
        mock_read_json,
        mock_get_file_info,
        mock_get_path,
    ):
        """Test handling errors when reading progress file."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_get_path.return_value = mock_path
        mock_get_file_info.return_value = MagicMock(
            success=True, exists=True, is_file=True
        )
        mock_read_json.return_value = MagicMock(success=False, error="Read error")

        expected_progress = UserProgress(github_username="test-user")
        mock_create_new.return_value = expected_progress

        # Act
        result = utils.load_progress()

        # Assert
        mock_read_json.assert_called_with(mock_path)
        mock_logger.warning.assert_called()
        mock_create_new.assert_called_once()
        assert result == expected_progress

    @patch("quackster.core.utils.get_progress_file_path")
    @patch("quackster.core.utils.fs.write_json")
    @patch("quackster.core.utils.logger")
    def test_save_progress_error(self, mock_logger, mock_write_json, mock_get_path):
        """Test handling errors when saving progress."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_get_path.return_value = mock_path
        mock_write_json.return_value = MagicMock(success=False, error="Write error")

        progress = UserProgress(github_username="test-user")

        # Act
        result = utils.save_progress(progress)

        # Assert
        mock_write_json.assert_called_with(mock_path, progress.model_dump())
        mock_logger.error.assert_called()
        assert result is False

    @patch("quackster.core.utils.get_progress_file_path")
    @patch("quackster.core.utils.fs.get_file_info")
    @patch("quackster.core.utils.fs.delete")
    @patch("quackster.core.utils.logger")
    def test_reset_progress_success(
        self, mock_logger, mock_delete, mock_get_file_info, mock_get_path
    ):
        """Test successfully resetting progress."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_get_path.return_value = mock_path
        mock_get_file_info.return_value = MagicMock(success=True, exists=True)
        mock_delete.return_value = MagicMock(success=True)

        # Act
        result = utils.reset_progress()

        # Assert
        mock_get_path.assert_called_once()
        mock_get_file_info.assert_called_with(mock_path)
        mock_delete.assert_called_with(mock_path)
        mock_logger.info.assert_called()
        assert result is True

    @patch("quackster.core.utils.get_progress_file_path")
    @patch("quackster.core.utils.fs.get_file_info")
    @patch("quackster.core.utils.logger")
    def test_reset_progress_no_file(
        self, mock_logger, mock_get_file_info, mock_get_path
    ):
        """Test resetting progress when file doesn't exist."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_get_path.return_value = mock_path
        mock_get_file_info.return_value = MagicMock(success=True, exists=False)

        # Act
        result = utils.reset_progress()

        # Assert
        mock_get_file_info.assert_called_with(mock_path)
        mock_logger.debug.assert_called()
        assert result is True

    @patch("quackster.core.utils.get_progress_file_path")
    @patch("quackster.core.utils.fs.get_file_info")
    @patch("quackster.core.utils.fs.delete")
    @patch("quackster.core.utils.logger")
    def test_reset_progress_error(
        self, mock_logger, mock_delete, mock_get_file_info, mock_get_path
    ):
        """Test handling errors when resetting progress."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_get_path.return_value = mock_path
        mock_get_file_info.return_value = MagicMock(success=True, exists=True)
        mock_delete.return_value = MagicMock(success=False, error="Delete error")

        # Act
        result = utils.reset_progress()

        # Assert
        mock_delete.assert_called_with(mock_path)
        mock_logger.error.assert_called()
        assert result is False

    @patch("quackster.core.utils.get_user_data_dir")
    @patch("quackster.core.utils.get_progress_file_path")
    @patch("quackster.core.utils.fs.get_file_info")
    @patch("quackster.core.utils.fs.copy")
    @patch("quackster.core.utils.logger")
    @patch("quackster.core.utils.datetime")
    def test_backup_progress_success(
        self,
        mock_datetime,
        mock_logger,
        mock_copy,
        mock_get_file_info,
        mock_get_path,
        mock_get_data_dir,
    ):
        """Test successfully backing up progress."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_get_path.return_value = mock_path
        mock_get_file_info.return_value = MagicMock(success=True, exists=True)

        mock_datetime.datetime.now.return_value.strftime.return_value = (
            "20250410_123456"
        )

        mock_data_dir = MagicMock(spec=Path)
        mock_get_data_dir.return_value = mock_data_dir
        mock_backup_path = MagicMock(spec=Path)
        mock_data_dir.__truediv__.return_value = mock_backup_path

        mock_copy.return_value = MagicMock(success=True)

        # Act
        result = utils.backup_progress()

        # Assert
        mock_get_path.assert_called_once()
        mock_get_file_info.assert_called_with(mock_path)
        mock_datetime.datetime.now.assert_called_once()
        mock_datetime.datetime.now.return_value.strftime.assert_called_with(
            "%Y%m%d_%H%M%S"
        )
        mock_data_dir.__truediv__.assert_called_with(
            f"ducktyper_user_20250410_123456.json"
        )
        mock_copy.assert_called_with(mock_path, mock_backup_path)
        mock_logger.info.assert_called()
        assert result is True

    @patch("quackster.core.utils.get_progress_file_path")
    @patch("quackster.core.utils.fs.get_file_info")
    @patch("quackster.core.utils.logger")
    def test_backup_progress_no_file(
        self, mock_logger, mock_get_file_info, mock_get_path
    ):
        """Test backing up progress when file doesn't exist."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_get_path.return_value = mock_path
        mock_get_file_info.return_value = MagicMock(success=True, exists=False)

        # Act
        result = utils.backup_progress()

        # Assert
        mock_get_file_info.assert_called_with(mock_path)
        mock_logger.debug.assert_called()
        assert result is False

    @patch("quackster.core.utils.get_user_data_dir")
    @patch("quackster.core.utils.get_progress_file_path")
    @patch("quackster.core.utils.fs.get_file_info")
    @patch("quackster.core.utils.fs.copy")
    @patch("quackster.core.utils.logger")
    def test_backup_progress_custom_name(
        self,
        mock_logger,
        mock_copy,
        mock_get_file_info,
        mock_get_path,
        mock_get_data_dir,
    ):
        """Test backing up progress with a custom backup name."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_get_path.return_value = mock_path
        mock_get_file_info.return_value = MagicMock(success=True, exists=True)

        mock_data_dir = MagicMock(spec=Path)
        mock_get_data_dir.return_value = mock_data_dir
        mock_backup_path = MagicMock(spec=Path)
        mock_data_dir.__truediv__.return_value = mock_backup_path

        mock_copy.return_value = MagicMock(success=True)

        custom_name = "my_custom_backup.json"

        # Act
        result = utils.backup_progress(custom_name)

        # Assert
        mock_data_dir.__truediv__.assert_called_with(custom_name)
        mock_copy.assert_called_with(mock_path, mock_backup_path)
        mock_logger.info.assert_called()
        assert result is True

    @patch("quackster.core.utils.get_user_data_dir")
    @patch("quackster.core.utils.get_progress_file_path")
    @patch("quackster.core.utils.fs.get_file_info")
    @patch("quackster.core.utils.fs.copy")
    @patch("quackster.core.utils.logger")
    def test_backup_progress_error(
        self,
        mock_logger,
        mock_copy,
        mock_get_file_info,
        mock_get_path,
        mock_get_data_dir,
    ):
        """Test handling errors when backing up progress."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_get_path.return_value = mock_path
        mock_get_file_info.return_value = MagicMock(success=True, exists=True)

        mock_data_dir = MagicMock(spec=Path)
        mock_get_data_dir.return_value = mock_data_dir
        mock_backup_path = MagicMock(spec=Path)
        mock_data_dir.__truediv__.return_value = mock_backup_path

        mock_copy.return_value = MagicMock(success=False, error="Copy error")

        # Act
        result = utils.backup_progress()

        # Assert
        mock_copy.assert_called_with(mock_path, mock_backup_path)
        mock_logger.error.assert_called()
        assert result is False

    @patch("quackster.core.utils.get_progress_file_path")
    @patch("quackster.core.utils.fs.get_file_info")
    @patch("quackster.core.utils.fs.read_json")
    @patch("quackster.core.utils.UserProgress.model_validate")
    @patch("quackster.core.utils.logger")
    def test_load_progress_success(
        self,
        mock_logger,
        mock_validate,
        mock_read_json,
        mock_get_file_info,
        mock_get_path,
    ):
        """Test successfully loading progress from file."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_get_path.return_value = mock_path
        mock_get_file_info.return_value = MagicMock(
            success=True, exists=True, is_file=True
        )

        progress_data = {
            "github_username": "test-user",
            "xp": 100,
            "completed_quest_ids": ["quest1", "quest2"],
        }
        mock_read_json.return_value = MagicMock(success=True, data=progress_data)

        expected_progress = UserProgress(
            github_username="test-user",
            xp=100,
            completed_quest_ids=["quest1", "quest2"],
        )
        mock_validate.return_value = expected_progress

        # Act
        result = utils.load_progress()

        # Assert
        mock_get_path.assert_called_once()
        mock_get_file_info.assert_called_with(mock_path)
        mock_read_json.assert_called_with(mock_path)
        mock_validate.assert_called_with(progress_data)
        mock_logger.debug.assert_called()
        assert result == expected_progress

    @patch("quackster.core.utils.get_progress_file_path")
    @patch("quackster.core.utils.fs.get_file_info")
    @patch("quackster.core.utils.fs.read_json")
    @patch("quackster.core.utils.create_new_progress")
    @patch("quackster.core.utils.logger")
    def test_load_progress_read_error(
        self,
        mock_logger,
        mock_create_new,
        mock_read_json,
        mock_get_file_info,
        mock_get_path,
    ):
        """Test handling errors when reading progress file."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_get_path.return_value = mock_path
        mock_get_file_info.return_value = MagicMock(
            success=True, exists=True, is_file=True
        )
        mock_read_json.return_value = MagicMock(success=False, error="Read error")

        expected_progress = UserProgress(github_username="test-user")
        mock_create_new.return_value = expected_progress

        # Act
        result = utils.load_progress()

        # Assert
        mock_read_json.assert_called_with(mock_path)
        mock_logger.warning.assert_called()
        mock_create_new.assert_called_once()
        assert result == expected_progress

    @patch("quackster.core.utils.get_github_username")
    @patch("quackster.core.utils.save_progress")
    def test_create_new_progress(self, mock_save, mock_get_username):
        """Test creating new user progress."""
        # Setup
        mock_get_username.return_value = "test-user"

        # Act
        result = utils.create_new_progress()

        # Assert
        mock_get_username.assert_called_once()
        mock_save.assert_called_once()
        assert result.github_username == "test-user"
        assert result.xp == 0
        assert result.completed_event_ids == []
        assert result.completed_quest_ids == []
        assert result.earned_badge_ids == []

    @patch("quackster.core.utils.get_progress_file_path")
    @patch("quackster.core.utils.fs.write_json")
    @patch("quackster.core.utils.logger")
    def test_save_progress_success(self, mock_logger, mock_write_json, mock_get_path):
        """Test successfully saving progress to file."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_get_path.return_value = mock_path
        mock_write_json.return_value = MagicMock(success=True)

        progress = UserProgress(
            github_username="test-user",
            xp=100,
            completed_quest_ids=["quest1", "quest2"],
        )

        # Act
        result = utils.save_progress(progress)

        # Assert
        mock_get_path.assert_called_once()
        mock_write_json.assert_called_with(mock_path, progress.model_dump())
        mock_logger.debug.assert_called()
        assert result is True
