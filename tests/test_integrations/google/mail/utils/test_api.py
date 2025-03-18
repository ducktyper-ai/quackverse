# tests/test_integrations/google/mail/utils/test_api.py
"""
Tests for Gmail API utility functions.

This module tests the API utilities for the Google Mail integration,
including request execution and exponential backoff.
"""

from unittest.mock import MagicMock, patch

import pytest
from googleapiclient.errors import HttpError

from quackcore.errors import QuackApiError
from quackcore.integrations.google.mail.utils.api import (
    execute_api_request,
    with_exponential_backoff,
)


class TestGmailApiUtils:
    """Tests for Gmail API utilities."""

    def test_execute_api_request(self) -> None:
        """Test executing a Gmail API request."""
        # Mock request object
        mock_request = MagicMock()
        mock_request.execute.return_value = {"id": "msg1", "payload": {}}

        # Test successful execution
        result = execute_api_request(
            mock_request,
            "Failed to get message",
            "users.messages.get",
        )

        assert result == {"id": "msg1", "payload": {}}
        mock_request.execute.assert_called_once()

        # Test with HttpError
        resp = MagicMock()
        resp.status = 403
        mock_request.execute.side_effect = HttpError(resp=resp,
                                                     content=b"Permission denied")

        with pytest.raises(QuackApiError) as excinfo:
            execute_api_request(
                mock_request,
                "Failed to get message",
                "users.messages.get",
            )

        assert "Failed to get message" in str(excinfo.value)
        assert "Permission denied" in str(excinfo.value)
        assert excinfo.value.api_method == "users.messages.get"

        # Test with generic exception
        mock_request.execute.side_effect = Exception("Unexpected error")

        with pytest.raises(QuackApiError) as excinfo:
            execute_api_request(
                mock_request,
                "Failed to get message",
                "users.messages.get",
            )

        assert "Failed to get message" in str(excinfo.value)
        assert "Unexpected error" in str(excinfo.value)
        assert excinfo.value.api_method == "users.messages.get"

    def test_with_exponential_backoff(self) -> None:
        """Test the exponential backoff decorator."""
        # Create a function that fails with HttpError a few times, then succeeds
        mock_func = MagicMock()

        # First 2 calls fail with status 429 (rate limit), third call succeeds
        resp1 = MagicMock()
        resp1.status = 429
        resp2 = MagicMock()
        resp2.status = 429

        mock_func.side_effect = [
            HttpError(resp=resp1, content=b"Rate limit exceeded"),
            HttpError(resp=resp2, content=b"Rate limit exceeded"),
            "success",
        ]

        # Apply the decorator
        decorated_func = with_exponential_backoff(
            mock_func,
            max_retries=3,
            initial_delay=0.01,  # Use small values for testing
            max_delay=0.05,
        )

        # Mock time.sleep to avoid actual delays
        with patch("time.sleep") as mock_sleep:
            result = decorated_func("arg1", arg2="value")

            assert result == "success"
            assert mock_func.call_count == 3
            assert mock_sleep.call_count == 2

            # Check backoff timing
            assert mock_sleep.call_args_list[0][0][0] == 0.01  # Initial delay
            assert mock_sleep.call_args_list[1][0][0] == 0.02  # Doubled delay

        # Test with non-retryable status code
        mock_func.reset_mock()
        resp = MagicMock()
        resp.status = 400  # Bad request - not retryable
        mock_func.side_effect = HttpError(resp=resp, content=b"Bad request")

        with pytest.raises(HttpError):
            decorated_func("arg1")

        assert mock_func.call_count == 1  # No retries for 400 error

        # Test with max retries exceeded
        mock_func.reset_mock()
        resp = MagicMock()
        resp.status = 503  # Service unavailable - retryable
        mock_func.side_effect = HttpError(resp=resp, content=b"Service unavailable")

        with pytest.raises(HttpError):
            decorated_func("arg1")

        assert mock_func.call_count == 4  # Original call + 3 retries

        # Test with non-HttpError exception
        mock_func.reset_mock()
        mock_func.side_effect = ValueError("Bad value")

        with pytest.raises(ValueError):
            decorated_func("arg1")

        assert mock_func.call_count == 1  # No retries for non-HttpError