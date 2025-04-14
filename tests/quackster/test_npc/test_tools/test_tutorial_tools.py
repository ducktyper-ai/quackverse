# tests/quackster/test_npc/test_tools/test_tutorial_tools.py
"""
Tests for the tutorial tools in quackcore.quackster.npc.tools.tutorial_tools.

This module tests the functions for retrieving and displaying tutorial content
on various topics related to the QuackVerse ecosystem.
"""

from quackster.npc.tools import TutorialOutput, tutorial_tools


class TestTutorialTools:
    """Tests for tutorial tools functionality."""

    def test_get_tutorial_basic(self, mocker):
        """Test the get_tutorial function with a basic topic."""
        # Mock dependencies
        mock_rag = mocker.patch("quackcore.quackster.npc.tools.tutorial_tools.rag")
        mock_rag.get_tutorial_topic.return_value = {
            "title": "Python Tutorial",
            "description": "Learn Python basics",
            "content": "Python is a versatile programming language...",
        }

        mock_registry = mocker.patch(
            "quackcore.quackster.npc.tools.tutorial_tools.DialogueRegistry"
        )
        mock_registry.render_template.return_value = "Rendered Python tutorial"

        # Mock standardize_tool_output
        mock_standardize = mocker.patch(
            "quackcore.quackster.npc.tools.tutorial_tools.standardize_tool_output"
        )
        mock_standardize.return_value = TutorialOutput(
            name="get_tutorial",
            result=mocker.MagicMock(),
            formatted_text="Python tutorial output",
        )

        # Call the function
        result = tutorial_tools.get_tutorial("python")

        # Verify dependencies were called correctly
        mock_rag.get_tutorial_topic.assert_called_once_with("python")
        mock_registry.render_template.assert_called_once()
        mock_standardize.assert_called_once()

        # Check the data passed to standardize_tool_output
        args = mock_standardize.call_args[0]
        assert args[0] == "get_tutorial"
        assert args[1]["topic"] == "python"
        assert args[1]["title"] == "Python Tutorial"
        assert args[1]["description"] == "Learn Python basics"
        assert args[1]["content"] == "Python is a versatile programming language..."
        assert args[1]["formatted_text"] == "Rendered Python tutorial"

        # Verify result
        assert isinstance(result, TutorialOutput)

    def test_get_tutorial_missing_content(self, mocker):
        """Test get_tutorial with missing content."""
        # Mock dependencies
        mock_rag = mocker.patch("quackcore.quackster.npc.tools.tutorial_tools.rag")
        mock_rag.get_tutorial_topic.return_value = {
            "title": "Unknown Topic",
            # No description or content
        }

        mock_registry = mocker.patch(
            "quackcore.quackster.npc.tools.tutorial_tools.DialogueRegistry"
        )
        mock_registry.render_template.return_value = (
            "Rendered tutorial with default content"
        )

        # Mock standardize_tool_output
        mock_standardize = mocker.patch(
            "quackcore.quackster.npc.tools.tutorial_tools.standardize_tool_output"
        )
        mock_standardize.return_value = TutorialOutput(
            name="get_tutorial",
            result=mocker.MagicMock(),
            formatted_text="Tutorial with default content",
        )

        # Call the function
        result = tutorial_tools.get_tutorial("unknown")

        # Verify dependencies were called correctly
        mock_rag.get_tutorial_topic.assert_called_once_with("unknown")
        mock_registry.render_template.assert_called_once()
        mock_standardize.assert_called_once()

        # Check the data passed to standardize_tool_output
        args = mock_standardize.call_args[0]
        assert args[0] == "get_tutorial"
        assert args[1]["topic"] == "unknown"
        assert args[1]["title"] == "Unknown Topic"
        assert args[1]["description"] == ""  # Default empty string
        assert "No tutorial content available" in args[1]["content"]  # Default message
        assert args[1]["formatted_text"] == "Rendered tutorial with default content"

        # Verify result
        assert isinstance(result, TutorialOutput)

    def test_get_tutorial_render_failure(self, mocker):
        """Test get_tutorial when template rendering fails."""
        # Mock dependencies
        mock_rag = mocker.patch("quackcore.quackster.npc.tools.tutorial_tools.rag")
        mock_rag.get_tutorial_topic.return_value = {
            "title": "Python Tutorial",
            "description": "Learn Python basics",
            "content": "Python is a versatile programming language...",
        }

        mock_registry = mocker.patch(
            "quackcore.quackster.npc.tools.tutorial_tools.DialogueRegistry"
        )
        # Simulate a rendering error
        mock_registry.render_template.side_effect = Exception("Rendering error")

        # Mock logger
        mock_logger = mocker.patch(
            "quackcore.quackster.npc.tools.tutorial_tools.logger"
        )

        # Mock standardize_tool_output
        mock_standardize = mocker.patch(
            "quackcore.quackster.npc.tools.tutorial_tools.standardize_tool_output"
        )
        mock_standardize.return_value = TutorialOutput(
            name="get_tutorial",
            result=mocker.MagicMock(),
            formatted_text="Tutorial fallback output",
        )

        # Call the function
        result = tutorial_tools.get_tutorial("python")

        # Verify dependencies were called correctly
        mock_rag.get_tutorial_topic.assert_called_once_with("python")
        mock_registry.render_template.assert_called_once()
        mock_logger.error.assert_called_once()
        mock_standardize.assert_called_once()

        # Check the data passed to standardize_tool_output - should use fallback format
        args = mock_standardize.call_args[0]
        assert args[0] == "get_tutorial"
        assert "# Python Tutorial" in args[1]["formatted_text"]
        assert "Learn Python basics" in args[1]["formatted_text"]
        assert (
            "Python is a versatile programming language..." in args[1]["formatted_text"]
        )

        # Verify result
        assert isinstance(result, TutorialOutput)

    def test_get_tutorial_empty_response(self, mocker):
        """Test get_tutorial with an empty response from RAG."""
        # Mock dependencies
        mock_rag = mocker.patch("quackcore.quackster.npc.tools.tutorial_tools.rag")
        mock_rag.get_tutorial_topic.return_value = {}  # Empty response

        mock_registry = mocker.patch(
            "quackcore.quackster.npc.tools.tutorial_tools.DialogueRegistry"
        )
        mock_registry.render_template.return_value = "Rendered empty tutorial"

        # Mock standardize_tool_output
        mock_standardize = mocker.patch(
            "quackcore.quackster.npc.tools.tutorial_tools.standardize_tool_output"
        )
        mock_standardize.return_value = TutorialOutput(
            name="get_tutorial",
            result=mocker.MagicMock(),
            formatted_text="Empty tutorial output",
        )

        # Call the function
        result = tutorial_tools.get_tutorial("nonexistent")

        # Verify dependencies were called correctly
        mock_rag.get_tutorial_topic.assert_called_once_with("nonexistent")
        mock_registry.render_template.assert_called_once()
        mock_standardize.assert_called_once()

        # Check the data passed to standardize_tool_output
        args = mock_standardize.call_args[0]
        assert args[0] == "get_tutorial"
        assert args[1]["topic"] == "nonexistent"
        assert args[1]["title"] == f"Tutorial on nonexistent"  # Default title
        assert args[1]["description"] == ""  # Default empty string
        assert "No tutorial content available" in args[1]["content"]  # Default message

        # Verify result
        assert isinstance(result, TutorialOutput)
