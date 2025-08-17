# quackcore/tests/test_http/test_routes_quackmedia.py
"""
Tests for QuackMedia routes.
"""

import pytest


def test_slice_video_no_auth(test_client):
    """Test slice endpoint fails without auth."""
    response = test_client.post("/quackmedia/slice", json={
        "input_path": "/test.mp4",
        "output_path": "/out.mp4",
        "start": "00:00:05",
        "end": "00:00:15"
    })
    assert response.status_code == 401


def test_slice_video_success(test_client, auth_headers):
    """Test successful video slicing."""
    response = test_client.post("/quackmedia/slice", json={
        "input_path": "/test.mp4",
        "output_path": "/out.mp4",
        "start": "00:00:05",
        "end": "00:00:15",
        "overwrite": True
    }, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["operation"] == "quackmedia.slice_video"


def test_transcribe_audio_success(test_client, auth_headers):
    """Test successful audio transcription."""
    response = test_client.post("/quackmedia/transcribe", json={
        "input_path": "/test.mp3",
        "model_name": "small",
        "device": "auto",
        "vad": True
    }, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["operation"] == "quackmedia.transcribe_audio"


def test_extract_frames_success(test_client, auth_headers):
    """Test successful frame extraction."""
    response = test_client.post("/quackmedia/frames", json={
        "input_path": "/test.mp4",
        "output_dir": "/frames",
        "fps": 2.0,
        "pattern": "frame_%06d.png",
        "overwrite": True
    }, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["operation"] == "quackmedia.extract_frames"


def test_invalid_operation_params(test_client, auth_headers):
    """Test handling of invalid parameters."""
    response = test_client.post("/quackmedia/slice", json={
        "invalid_param": "value"
    }, headers=auth_headers)

    # Should handle gracefully (mock function accepts any kwargs)
    assert response.status_code == 200


@pytest.mark.parametrize("endpoint,operation", [
    ("/quackmedia/slice", "quackmedia.slice_video"),
    ("/quackmedia/transcribe", "quackmedia.transcribe_audio"),
    ("/quackmedia/frames", "quackmedia.extract_frames"),
])
def test_all_quackmedia_endpoints(test_client, auth_headers, endpoint, operation):
    """Test all QuackMedia endpoints return consistent structure."""
    response = test_client.post(endpoint, json={
        "test_param": "test_value"
    }, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["operation"] == operation
    assert "params" in data
    assert data["params"]["test_param"] == "test_value"