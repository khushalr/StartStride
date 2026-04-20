from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] in {"mock", "live"}
    assert "poll_interval_seconds" in payload


def test_vehicles_filtering_by_mode() -> None:
    response = client.get("/api/vehicles", params={"mode": "streetcar"})
    assert response.status_code == 200
    body = response.json()
    assert "vehicles" in body
    for vehicle in body["vehicles"]:
        assert vehicle["mode"] == "streetcar"
