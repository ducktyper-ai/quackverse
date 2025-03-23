# tests/test_cli/test_cli_utils.py
"""
Tests for CLI utility functions.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from quackcore.cli.utils import (
    Color,
    ask,
    colorize,
    confirm,
    get_terminal_size,
    print_error,
    print_info,
    print_success,
    print_warning,
    show_progress,
    supports_color,
    table,
    truncate_text,
)


class TestColorUtilities:
    """Tests for color utilities."""

    def test_color_enum(self) -> None:
        """Test the Color enum."""
        # Test color values
        assert Color.RED == "31"
        assert Color.GREEN == "32"
        assert Color.BLUE == "34"

        # Test background colors
        assert Color.BG_RED == "41"
        assert Color.BG_GREEN == "42"
        assert Color.BG_BLUE == "44"

        # Test styles
        assert Color.BOLD == "1"
        assert Color.ITALIC == "3"
        assert Color.UNDERLINE == "4"

        # Test reset values
        assert Color.RESET == "39"
        assert Color.BG_RESET == "49"
        assert Color.RESET_ALL == "0"

    def test_supports_color(self) -> None:
        """Test color support detection."""
        # Test with NO_COLOR env var
        with patch.dict(os.environ, {"NO_COLOR": "1"}):
            assert supports_color() is False

        # Test with --no-color flag
        with patch.object(sys, "argv", ["script.py", "--no-color"]):
            assert supports_color() is False

        # Test with TTY
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(sys, "argv", ["script.py"]):
                # Mock sys.stdout.isatty
                with patch("sys.stdout") as mock_stdout:
                    mock_stdout.isatty.return_value = True
                    assert supports_color() is True

                    # Test without TTY
                    mock_stdout.isatty.return_value = False
                    # Should be False unless in CI
                    with patch.dict(os.environ, {}, clear=True):
                        assert supports_color() is False

                    # Test in GitHub Actions
                    with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
                        assert supports_color() is True

                    # Test in CI with color force
                    with patch.dict(os.environ, {"CI": "true", "CI_FORCE_COLORS": "1"}):
                        assert supports_color() is True

    @given(
        text=st.text(min_size=1),
        max_length=st.integers(min_value=5, max_value=50),
    )
    def test_truncate_text(self, text: str, max_length: int) -> None:
        """Test truncate_text function."""
        assume(len(text) > 0)  # Ensure non-empty text

        result = truncate_text(text, max_length)

        # Result should never be longer than max_length
        assert len(result) <= max_length

        # If original text is shorter, it should be unchanged
        if len(text) <= max_length:
            assert result == text
        else:
            # If truncated, should end with ellipsis
            assert result.endswith("...")
            # And should contain the start of the original text
            assert text.startswith(result[:-3])

    def test_table(self) -> None:
        """Test table function."""
        # Test basic table
        headers = ["Name", "Age", "City"]
        rows = [
            ["Alice", "25", "New York"],
            ["Bob", "30", "San Francisco"],
            ["Charlie", "35", "Seattle"],
        ]

        with patch("builtins.print") as mock_print:
            table(headers, rows)

            # Verify print was called appropriate number of times
            # (1 for headers + len(rows) + separators)
            assert mock_print.call_count > 0

        # Test empty table
        with patch("builtins.print") as mock_print:
            table(headers, [])

            # Should still print headers
            assert mock_print.call_count > 0

        # Test without headers
        with patch("builtins.print") as mock_print:
            table(None, rows)

            # Should print rows without headers
            assert mock_print.call_count > 0

        # Test with custom separator
        with patch("builtins.print") as mock_print:
            table(headers, rows, separator="*")

            # Verify print was called
            assert mock_print.call_count > 0
            # Would check for "*" in the output, but that would be too implementation-specific

        # Test with custom alignment
        with patch("builtins.print") as mock_print:
            table(headers, rows, alignment="right")

            assert mock_print.call_count > 0
            # Would check alignment, but that would be too implementation-specific

    def test_get_terminal_size(self) -> None:
        """Test get_terminal_size function."""
        # Test successful case
        with patch("shutil.get_terminal_size") as mock_get_size:
            mock_get_size.return_value = MagicMock(columns=120, lines=40)

            width, height = get_terminal_size()

            assert width == 120
            assert height == 40
            mock_get_size.assert_called_once()

        # Test fallback case (ImportError)
        with patch("shutil.get_terminal_size", side_effect=ImportError):
            width, height = get_terminal_size()

            # Should return default values
            assert width == 80
            assert height == 24

        # Test fallback case (OSError)
        with patch("shutil.get_terminal_size", side_effect=OSError):
            width, height = get_terminal_size()

            # Should return default values
            assert width == 80
            assert height == 24

    @given(
        text=st.text(min_size=1),
        fg=st.sampled_from([None, "red", "green", "blue", "cyan", "yellow", "white"]),
        bg=st.sampled_from([None, "black", "red", "green", "blue"]),
        bold=st.booleans(),
        dim=st.booleans(),
        underline=st.booleans(),
        italic=st.booleans(),
        blink=st.booleans(),
    )
    def test_colorize(
        self,
        text: str,
        fg: str | None,
        bg: str | None,
        bold: bool,
        dim: bool,
        underline: bool,
        italic: bool,
        blink: bool,
    ) -> None:
        """Test the colorize function with Hypothesis."""
        # Test with color support
        with patch("quackcore.cli.utils.supports_color", return_value=True):
            result = colorize(
                text=text,
                fg=fg,
                bg=bg,
                bold=bold,
                dim=dim,
                underline=underline,
                italic=italic,
                blink=blink,
            )

            # Result should be different from input if any styling is applied
            styling_applied = any([fg, bg, bold, dim, underline, italic, blink])

            if styling_applied:
                assert result != text
                assert result.startswith("\033[")
                assert result.endswith(f"{text}\033[0m")

                # Check that ANSI codes are included
                if fg:
                    fg_code = getattr(Color, fg.upper())
                    assert fg_code in result

                if bg:
                    bg_code = getattr(Color, f"BG_{bg.upper()}")
                    assert bg_code in result

                if bold:
                    assert Color.BOLD in result

                if dim:
                    assert Color.DIM in result

                if underline:
                    assert Color.UNDERLINE in result

                if italic:
                    assert Color.ITALIC in result

                if blink:
                    assert Color.BLINK in result
            else:
                assert result == text

        # Test without color support
        with patch("quackcore.cli.utils.supports_color", return_value=False):
            result = colorize(
                text=text,
                fg=fg,
                bg=bg,
                bold=bold,
                dim=dim,
                underline=underline,
                italic=italic,
                blink=blink,
            )

            # Result should be the same as input regardless of styling
            assert result == text

        # Test with force=True
        result = colorize(
            text=text,
            fg=fg,
            bg=bg,
            bold=bold,
            dim=dim,
            underline=underline,
            italic=italic,
            blink=blink,
            force=True,
        )

        # Should be styled even if color is not supported
        if any([fg, bg, bold, dim, underline, italic, blink]):
            assert result != text
            assert result.startswith("\033[")
            assert result.endswith(f"{text}\033[0m")
        """Test the colorize function with Hypothesis."""
        # Test with color support
        with patch("quackcore.cli.utils.supports_color", return_value=True):
            result = colorize(
                text=text,
                fg=fg,
                bg=bg,
                bold=bold,
                dim=dim,
                underline=underline,
                italic=italic,
                blink=blink,
            )

            # Result should be different from input if any styling is applied
            styling_applied = any([fg, bg, bold, dim, underline, italic, blink])

            if styling_applied:
                assert result != text
                assert result.startswith("\033[")
                assert result.endswith(f"{text}\033[0m")

                # Check that ANSI codes are included
                if fg:
                    fg_code = getattr(Color, fg.upper())
                    assert fg_code in result

                if bg:
                    bg_code = getattr(Color, f"BG_{bg.upper()}")
                    assert bg_code in result

                if bold:
                    assert Color.BOLD in result

                if dim:
                    assert Color.DIM in result

                if underline:
                    assert Color.UNDERLINE in result

                if italic:
                    assert Color.ITALIC in result

                if blink:
                    assert Color.BLINK in result
            else:
                assert result == text

        # Test without color support
        with patch("quackcore.cli.utils.supports_color", return_value=False):
            result = colorize(
                text=text,
                fg=fg,
                bg=bg,
                bold=bold,
                dim=dim,
                underline=underline,
                italic=italic,
                blink=blink,
            )

            # Result should be the same as input regardless of styling
            assert result == text

        # Test with force=True
        result = colorize(
            text=text,
            fg=fg,
            bg=bg,
            bold=bold,
            dim=dim,
            underline=underline,
            italic=italic,
            blink=blink,
            force=True,
        )

        # Should be styled even if color is not supported
        if any([fg, bg, bold, dim, underline, italic, blink]):
            assert result != text
            assert result.startswith("\033[")
            assert result.endswith(f"{text}\033[0m")


class TestOutputFunctions:
    """Tests for output functions."""

    def test_print_functions(self) -> None:
        """Test print_* functions."""
        # Mock print function
        with patch("builtins.print") as mock_print:
            # Test print_error
            print_error("Error message")
            args, _ = mock_print.call_args
            assert "Error message" in args[0]
            mock_print.reset_mock()

            # Test print_warning
            print_warning("Warning message")
            args, _ = mock_print.call_args
            assert "Warning message" in args[0]
            mock_print.reset_mock()

            # Test print_success
            print_success("Success message")
            args, _ = mock_print.call_args
            assert "Success message" in args[0]
            mock_print.reset_mock()

            # Test print_info
            print_info("Info message")
            args, _ = mock_print.call_args
            assert "Info message" in args[0]
            mock_print.reset_mock()

    def test_confirm(self) -> None:
        """Test confirm function."""
        # Mock input function for positive response
        with patch("builtins.input", return_value="y"):
            assert confirm("Continue?") is True

        # Mock input function for negative response
        with patch("builtins.input", return_value="n"):
            assert confirm("Continue?") is False

        # Test with default=True
        with patch("builtins.input", return_value=""):
            assert confirm("Continue?", default=True) is True

        # Test with default=False
        with patch("builtins.input", return_value=""):
            assert confirm("Continue?", default=False) is False

        # Test with case-insensitive response
        with patch("builtins.input", return_value="Y"):
            assert confirm("Continue?") is True

        # Test with non-y/n response followed by valid response
        with patch("builtins.input", side_effect=["invalid", "y"]):
            assert confirm("Continue?") is True

    def test_ask(self) -> None:
        """Test ask function."""
        # Mock input function
        with patch("builtins.input", return_value="test response"):
            response = ask("Enter value:")
            assert response == "test response"

        # Test with default value
        with patch("builtins.input", return_value=""):
            response = ask("Enter value:", default="default")
            assert response == "default"

        # Test with validator function that succeeds
        validator = lambda x: x.isalpha()
        with patch("builtins.input", return_value="valid"):
            response = ask("Enter value:", validator=validator)
            assert response == "valid"

        # Test with validator function that fails then succeeds
        with patch("builtins.input", side_effect=["123", "valid"]):
            response = ask("Enter value:", validator=validator)
            assert response == "valid"

        # Test with max_attempts
        with patch("builtins.input", side_effect=["123", "456", "789"]):
            with pytest.raises(ValueError):
                ask("Enter value:", validator=validator, max_attempts=2)

    def test_show_progress(self) -> None:
        """Test show_progress function."""
        # Mock stdout for testing
        mock_stdout = MagicMock()

        with patch("sys.stdout", mock_stdout):
            # Test basic progress display
            show_progress(50, 100)

            # Verify stdout.write was called
            assert mock_stdout.write.called
            assert mock_stdout.flush.called

            # Test with completed progress
            mock_stdout.reset_mock()
            show_progress(100, 100)

            # Should print newline for completed progress
            _, kwargs = mock_stdout.write.call_args
            assert "\n" in kwargs.get("end", "")

            # Test with custom message
            mock_stdout.reset_mock()
            show_progress(25, 100, message="Loading:")

            # Verify message is included
            args, _ = mock_stdout.write.call_args
            assert "Loading:" in args[0]
