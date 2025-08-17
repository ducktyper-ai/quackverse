# quackcore/tests_http/test_jobs.py
"""
Tests for job management functionality.
"""

import time
import pytest
from unittest.mock import patch, MagicMock

from quackcore.adapters.http.jobs import (
    set_cfg, enqueue, get_status, resolve_callable, _create_mock_function
)
from quackcore.adapters.http.config import HttpAdapterConfig


@pytest.fixture
def job_config():
    """Create job test configuration."""
    return HttpAdapterConfig(
        max_workers=2,
        job_ttl_seconds=60,
        request_timeout_seconds=30
    )


def test_set_cfg(job_config):
    """Test configuration setting."""
    set_cfg(job_config)
    # Should not raise


def test_resolve_callable_unknown_op():
    """Test resolving unknown operation."""
    with pytest.raises(ValueError, match="Unsupported operation"):
        resolve_callable("unknown.operation")


def test_resolve_callable_mock():
    """Test resolving operation that falls back to mock."""
    # This should work since quackmedia doesn't exist yet
    fn = resolve_callable("quackmedia.slice_video")
    assert callable(fn)

    # Test mock function
    result = fn(input_path="/test", output_path="/out")
    assert result["success"] is True
    assert result["operation"] == "quackmedia.slice_video"


def test_create_mock_function():
    """Test mock function creation."""
    mock_fn = _create_mock_function("test.operation")

    result = mock_fn(param1="value1", param2="value2")

    assert result["success"] is True
    assert result["operation"] == "test.operation"
    assert result["params"]["param1"] == "value1"
    assert result["params"]["param2"] == "value2"


def test_enqueue_not_initialized():
    """Test enqueuing when system not initialized."""
    # Reset global state
    from quackcore.adapters.http import jobs
    jobs._executor = None
    jobs._cfg = None

    with pytest.raises(RuntimeError, match="Job system not initialized"):
        enqueue("test.op", {})


def test_enqueue_and_get_status(job_config):
    """Test job enqueuing and status retrieval."""
    set_cfg(job_config)

    # Enqueue a job
    job_id = enqueue("quackmedia.slice_video", {"input_path": "/test"})

    assert job_id is not None
    assert len(job_id) == 36  # UUID4 length

    # Get initial status (should exist immediately after enqueue)
    status = get_status(job_id)
    assert status is not None
    assert status["job_id"] == job_id
    assert status["status"] in ["queued", "running", "done"]

    # Wait a bit for job to complete
    time.sleep(0.2)

    final_status = get_status(job_id)
    assert final_status is not None
    assert final_status["status"] in ["running", "done"]


def test_enqueue_with_idempotency(job_config):
    """Test job idempotency."""
    set_cfg(job_config)

    params = {"input_path": "/test"}
    key = "test-key-123"

    # Enqueue first job
    job_id1 = enqueue("quackmedia.slice_video", params, idempotency_key=key)

    # Enqueue same job again immediately (before first one finishes)
    job_id2 = enqueue("quackmedia.slice_video", params, idempotency_key=key)

    # Should return same job ID
    assert job_id1 == job_id2


def test_get_status_not_found():
    """Test getting status for non-existent job."""
    status = get_status("non-existent-job-id")
    assert status is None