
# File: quackcore/tests_http/test_integration.py
"""
Integration tests for the HTTP adapter.
"""

import pytest
import time
from fastapi.testclient import TestClient

from quackcore.adapters.http.app import create_app
from quackcore.adapters.http.config import HttpAdapterConfig


@pytest.fixture
def integration_client():
    """Create client for integration testing."""
    config = HttpAdapterConfig(
        auth_token="integration-test-token",
        max_workers=1,
        job_ttl_seconds=30
    )
    app = create_app(config)
    return TestClient(app)


@pytest.fixture
def integration_headers():
    """Auth headers for integration tests."""
    return {"Authorization": "Bearer integration-test-token"}


def test_full_job_workflow(integration_client, integration_headers):
    """Test complete job workflow from creation to completion."""
    # Create job
    create_response = integration_client.post("/jobs", json={
        "op": "quackmedia.slice_video",
        "params": {
            "input_path": "/test/input.mp4",
            "output_path": "/test/output.mp4",
            "start": "00:00:10",
            "end": "00:00:20"
        }
    }, headers=integration_headers)

    assert create_response.status_code == 200
    job_data = create_response.json()
    job_id = job_data["job_id"]

    # Poll for completion
    max_attempts = 20
    for attempt in range(max_attempts):
        status_response = integration_client.get(
            f"/jobs/{job_id}",
            headers=integration_headers
        )
        assert status_response.status_code == 200

        status_data = status_response.json()
        if status_data["status"] in ["done", "error"]:
            break

        time.sleep(0.1)

    # Verify completion
    assert status_data["status"] == "done"
    assert status_data["result"]["success"] is True
    assert "input_path" in status_data["result"]["params"]


def test_sync_vs_async_consistency(integration_client, integration_headers):
    """Test that sync and async endpoints return consistent results."""
    params = {
        "input_path": "/test.mp4",
        "output_path": "/out.mp4",
        "start": "00:00:05",
        "end": "00:00:10"
    }

    # Test sync endpoint
    sync_response = integration_client.post(
        "/quackmedia/slice",
        json=params,
        headers=integration_headers
    )
    assert sync_response.status_code == 200
    sync_result = sync_response.json()

    # Test async endpoint
    async_response = integration_client.post("/jobs", json={
        "op": "quackmedia.slice_video",
        "params": params
    }, headers=integration_headers)

    job_id = async_response.json()["job_id"]

    # Wait for async completion
    for _ in range(20):
        status_response = integration_client.get(
            f"/jobs/{job_id}",
            headers=integration_headers
        )
        status_data = status_response.json()
        if status_data["status"] == "done":
            break
        time.sleep(0.1)

    async_result = status_data["result"]

    # Results should be consistent
    assert sync_result["success"] == async_result["success"]
    assert sync_result["operation"] == async_result["operation"]


def test_health_endpoints(integration_client):
    """Test health endpoints work without auth."""
    # Note: health endpoints should work without auth in this setup
    # since we're testing the overall health of the service

    live_response = integration_client.get("/health/live")
    assert live_response.status_code == 200
    assert live_response.json() == {"ok": True}

    ready_response = integration_client.get("/health/ready")
    assert ready_response.status_code == 200
    assert ready_response.json() == {"ok": True}


def test_cors_headers(integration_client):
    """Test CORS handling."""
    # This is a basic test - full CORS testing would require
    # configuring CORS origins and testing preflight requests
    response = integration_client.get("/health/live")
    assert response.status_code == 200


def test_openapi_docs(integration_client):
    """Test that OpenAPI documentation is available."""
    docs_response = integration_client.get("/docs")
    # Should redirect or return HTML
    assert docs_response.status_code in [200, 307]

    openapi_response = integration_client.get("/openapi.json")
    assert openapi_response.status_code == 200

    openapi_data = openapi_response.json()
    assert "openapi" in openapi_data
    assert "info" in openapi_data
    assert openapi_data["info"]["title"] == "QuackCore API"