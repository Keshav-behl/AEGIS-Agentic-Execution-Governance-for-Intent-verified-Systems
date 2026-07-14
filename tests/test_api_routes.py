import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient

from app import config as config_module
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(config_module, "DATABASE_PATH", str(tmp_path / "test.db"))


def test_low_risk_request_auto_executes():
    resp = client.post(
        "/aegis/request",
        json={"text": "add a comment on AG-1 saying the AEGIS Phase 7 pipeline test ran successfully"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "auto_executed"
    assert body["detail"]["status"] == "success"

    status_resp = client.get(f"/aegis/status/{body['request_id']}")
    assert status_resp.json()["status"] == "executed"


def test_high_risk_request_posts_to_slack_and_stays_pending():
    resp = client.post(
        "/aegis/request",
        json={"text": "move AG-1 to done"},
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
