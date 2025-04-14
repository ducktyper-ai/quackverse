# tests/quackster/test_npc/test_tools/test_progress_tools.py
"""
Tests for the progress tools in quackster.npc.tools.progress_tools.

This module tests the functions for checking user progress, XP, and level information.
"""

import pytest

from quackster.npc.schema import UserMemory
from quackster.npc.tools import ProgressOutput, progress_tools


class TestProgressTools:
    """Tests for progress tools functionality."""

    @pytest.fixture
    def user_memory_basic(self):
        """Create a basic UserMemory object for testing."""
        return UserMemory(
            github_username="testuser",
            xp=150,
            level=2,
            custom_data={"xp_to_next_level": 50},
        )

    @pytest.fixture
    def user_memory_advanced(self):
        """Create an advanced UserMemory object for testing."""
        return UserMemory(
            github_username="advanceduser",
            xp=350,
            level=4,
            custom_data={"xp_to_next_level": 25},
        )

    @pytest.fixture
    def user_memory_no_next_level(self):
        """Create a UserMemory object without xp_to_next_level."""
        return UserMemory(
            github_username="newuser",
            xp=50,
            level=1,
            custom_data={},
        )

    def test_list_xp_and_level_basic(self, mocker, user_memory_basic):
        """Test list_xp_and_level function with basic user memory."""
        # Mock standardize_tool_output
        mock_standardize = mocker.patch(
            "quackster.npc.tools.progress_tools.standardize_tool_output"
        )
        mock_standardize.return_value = ProgressOutput(
            name="list_xp_and_level",
            result=mocker.MagicMock(),
            formatted_text="Progress info output",
        )

        # Call the function
        result = progress_tools.list_xp_and_level(user_memory_basic)

        # Verify standardize_tool_output was called correctly
        mock_standardize.assert_called_once()

        # Check the data passed to standardize_tool_output
        args = mock_standardize.call_args[0]
        assert args[0] == "list_xp_and_level"
        assert args[1]["level"] == 2
        assert args[1]["xp"] == 150
        assert args[1]["next_level"] == 3
        assert args[1]["xp_needed"] == 50
        assert "progress_pct" in args[1]
        assert "progress_bar" in args[1]
        assert "formatted_text" in args[1]

        # Verify result
        assert isinstance(result, ProgressOutput)

    def test_list_xp_and_level_advanced(self, mocker, user_memory_advanced):
        """Test list_xp_and_level function with advanced user memory."""
        # Mock standardize_tool_output
        mock_standardize = mocker.patch(
            "quackster.npc.tools.progress_tools.standardize_tool_output"
        )
        mock_standardize.return_value = ProgressOutput(
            name="list_xp_and_level",
            result=mocker.MagicMock(),
            formatted_text="Advanced progress info output",
        )

        # Call the function
        result = progress_tools.list_xp_and_level(user_memory_advanced)

        # Verify standardize_tool_output was called correctly
        mock_standardize.assert_called_once()

        # Check the data passed to standardize_tool_output
        args = mock_standardize.call_args[0]
        assert args[0] == "list_xp_and_level"
        assert args[1]["level"] == 4
        assert args[1]["xp"] == 350
        assert args[1]["next_level"] == 5
        assert args[1]["xp_needed"] == 25
        assert "progress_pct" in args[1]
        assert "progress_bar" in args[1]
        assert "formatted_text" in args[1]

        # Verify result
        assert isinstance(result, ProgressOutput)

    def test_list_xp_and_level_default_next_level(
        self, mocker, user_memory_no_next_level
    ):
        """Test list_xp_and_level with no xp_to_next_level in custom_data."""
        # Mock standardize_tool_output
        mock_standardize = mocker.patch(
            "quackster.npc.tools.progress_tools.standardize_tool_output"
        )
        mock_standardize.return_value = ProgressOutput(
            name="list_xp_and_level",
            result=mocker.MagicMock(),
            formatted_text="Default next level progress info",
        )

        # Call the function
        result = progress_tools.list_xp_and_level(user_memory_no_next_level)

        # Verify standardize_tool_output was called correctly
        mock_standardize.assert_called_once()

        # Check the data passed to standardize_tool_output - should use default 100
        args = mock_standardize.call_args[0]
        assert args[0] == "list_xp_and_level"
        assert args[1]["level"] == 1
        assert args[1]["xp"] == 50
        assert args[1]["next_level"] == 2
        assert args[1]["xp_needed"] == 100  # Default value
        assert "progress_pct" in args[1]
        assert "progress_bar" in args[1]
        assert "formatted_text" in args[1]

        # Verify result
        assert isinstance(result, ProgressOutput)

    def test_progress_percentage_calculation(self, mocker, user_memory_basic):
        """Test progress percentage calculation."""
        # Mock standardize_tool_output to capture the calculated values
        mock_standardize = mocker.patch(
            "quackster.npc.tools.progress_tools.standardize_tool_output"
        )
        mock_standardize.return_value = ProgressOutput(
            name="list_xp_and_level",
            result=mocker.MagicMock(),
            formatted_text="Progress calculation test",
        )

        # Call the function
        progress_tools.list_xp_and_level(user_memory_basic)

        # Check the progress percentage calculation
        args = mock_standardize.call_args[0]
        progress_pct = args[1]["progress_pct"]

        # XP needed is 50, next level is 3, so formula is:
        # 100 - (50 / (3 * 100) * 100) = 100 - (50 / 300 * 100) = 100 - 16.67 = 83.33
        # The actual implementation might round differently
        assert 80 <= progress_pct <= 85

    def test_progress_bar_generation(self, mocker, user_memory_basic):
        """Test progress bar generation."""
        # Mock standardize_tool_output to capture the generated progress bar
        mock_standardize = mocker.patch(
            "quackster.npc.tools.progress_tools.standardize_tool_output"
        )
        mock_standardize.return_value = ProgressOutput(
            name="list_xp_and_level",
            result=mocker.MagicMock(),
            formatted_text="Progress bar test",
        )

        # Call the function
        progress_tools.list_xp_and_level(user_memory_basic)

        # Check the progress bar generation
        args = mock_standardize.call_args[0]
        progress_bar = args[1]["progress_bar"]

        # Progress is around 83%, so bar should have 16-17 filled blocks
        filled_blocks = progress_bar.count("█")
        empty_blocks = progress_bar.count("░")

        assert filled_blocks + empty_blocks == 20  # Total should be 20 blocks
        assert 16 <= filled_blocks <= 17  # Around 83% of 20
        assert 3 <= empty_blocks <= 4  # Remainder

    def test_formatted_text_structure(self, mocker, user_memory_basic):
        """Test the structure of the formatted text."""
        # Create a real standardize_tool_output to pass through the actual value
        original_standardize = progress_tools.standardize_tool_output

        def mock_standardize(*args, **kwargs):
            return original_standardize(*args, **kwargs)

        mock_standardize_patch = mocker.patch(
            "quackster.npc.tools.progress_tools.standardize_tool_output",
            side_effect=mock_standardize,
        )

        # Call the function
        result = progress_tools.list_xp_and_level(user_memory_basic)

        # Check structure of the formatted text
        formatted_text = result.result.model_dump()["formatted_text"]

        # Should contain level and XP
        assert f"Level {user_memory_basic.level}" in formatted_text
        assert f"{user_memory_basic.xp} XP" in formatted_text

        # Should contain progress bar
        assert "█" in formatted_text
        assert "░" in formatted_text

        # Should contain XP needed for next level
        assert (
            f"{user_memory_basic.custom_data['xp_to_next_level']} XP needed"
            in formatted_text
        )
        assert f"Level {user_memory_basic.level + 1}" in formatted_text
