# filepath: /Users/pranavvaddepalli/Desktop/HooHacks/backend/tests/test_api.py
from fastapi.testclient import TestClient

from main import app


def test_health_ok():
    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


def test_generate_returns_job_id():
    with TestClient(app) as client:
        resp = client.post(
            "/generate",
            json={"topic": "Photosynthesis", "output_type": "image"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "job_id" in data
        assert isinstance(data["job_id"], str)
        assert data["job_id"] != ""