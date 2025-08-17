# File: quackcore/tests_http/test_util.py
"""
Tests for utility functions.
"""

import pytest
from unittest.mock import AsyncMock, patch
import json

from quackcore.adapters.http.util import new_id, stable_hash, post_callback


def test_new_id():
    """Test UUID generation."""
    id1 = new_id()
    id2 = new_id()

    assert len(id1) == 36  # UUID4 format
    assert len(id2) == 36
    assert id1 != id2  # Should be unique


def test_stable_hash():
    """Test stable hashing."""
    payload1 = {"key": "value", "number": 42}
    payload2 = {"number": 42, "key": "value"}  # Different order
    payload3 = {"key": "different", "number": 42}

    hash1 = stable_hash(payload1)
    hash2 = stable_hash(payload2)
    hash3 = stable_hash(payload3)

    # Same content should produce same hash regardless of order
    assert hash1 == hash2
    # Different content should produce different hash
    assert hash1 != hash3

    # Should be hex string
    assert len(hash1) == 64
    assert all(c in "0123456789abcdef" for c in hash1)


@pytest.mark.asyncio
async def test_post_callback_success():
    """Test successful callback posting."""
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = AsyncMock()
        mock_response.raise_for_status.return_value = None

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.post.return_value = mock_response
        mock_client.return_value = mock_context

        body = {"job_id": "123", "status": "done"}
        await post_callback("http://example.com/callback", body)

        # Verify client was called correctly
        mock_client.assert_called_once_with(timeout=10)


@pytest.mark.asyncio
async def test_post_callback_with_signature():
    """Test callback posting with signature."""
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = AsyncMock()
        mock_response.raise_for_status.return_value = None

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.post.return_value = mock_response
        mock_client.return_value = mock_context

        body = {"job_id": "123", "status": "done"}
        signature = "sha256=abcdef123456"

        await post_callback("http://example.com/callback", body, signature)

        # Check that post was called with signature header
        call_args = mock_context.__aenter__.return_value.post.call_args
        headers = call_args.kwargs["headers"]
        assert headers["X-Quack-Signature"] == signature


@pytest.mark.asyncio
async def test_post_callback_failure():
    """Test callback posting failure handling."""
    with patch('httpx.AsyncClient') as mock_client:
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.post.side_effect = Exception("Network error")
        mock_client.return_value = mock_context

        body = {"job_id": "123", "status": "done"}

        # Should not raise, just log error
        await post_callback("http://example.com/callback", body)