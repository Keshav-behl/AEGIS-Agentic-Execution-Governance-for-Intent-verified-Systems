import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient

from app import config as config_module
from app.main import app

client = TestClient(app)

TEST_API_KEY = "test-api-key"
AUTH_HEADERS = {"X-AEGIS-API-Key": TEST_API_KEY}


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(config_module, "DATABASE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setattr(config_module, "AEGIS_API_KEYS", {TEST_API_KEY: "test-requester@example.com"})


def test_missing_api_key_rejected():
    resp = client.post("/aegis/request", json={"text": "add a comment on AG-1 saying hi"})
    assert resp.status_code == 422  # missing required header


def test_unknown_api_key_rejected():
    resp = client.post(
        "/aegis/request",
        json={"text": "add a comment on AG-1 saying hi"},
        headers={"X-AEGIS-API-Key": "not-a-real-key"},
    )
    assert resp.status_code == 401


def test_low_risk_request_auto_executes():
    resp = client.post(
        "/aegis/request",
        json={"text": "add a comment on AG-1 saying the AEGIS Phase 7 pipeline test ran successfully"},
        headers=AUTH_HEADERS,
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "auto_executed"
    assert body["detail"]["status"] == "success"

    status_resp = client.get(f"/aegis/status/{body['request_id']}")
    status_body = status_resp.json()
    assert status_body["status"] == "executed"
    assert status_body["detail"]["requester"] == "test-requester@example.com"


def test_high_risk_request_posts_to_slack_and_stays_pending():
    resp = client.post(
        "/aegis/request",
        json={"text": "move AG-1 to done"},
        headers=AUTH_HEADERS,
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "pending_approval"
    assert body["detail"]["risk_score"] >= 40

    status_resp = client.get(f"/aegis/status/{body['request_id']}")
    assert status_resp.json()["status"] == "pending_approval"


def test_status_of_unknown_request_id_is_pending():
    resp = client.get("/aegis/status/not-a-real-nonce")

    assert resp.status_code == 200
    assert resp.json()["status"] == "pending_approval"
