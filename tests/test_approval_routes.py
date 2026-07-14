import hashlib
import hmac
import json
import sys
import time
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient

from app import config as config_module
from app.audit.audit_log import _get_conn as _audit_conn
from app.main import app
from app.protocol import signing
from app.schemas import ActionProposal

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(config_module, "DATABASE_PATH", str(tmp_path / "test.db"))


def _interaction_body(action_id: str, token: str) -> bytes:
    payload = {"actions": [{"action_id": action_id, "value": token}]}
    return urlencode({"payload": json.dumps(payload)}).encode()


def _sign_headers(raw_body: bytes, timestamp: str | None = None) -> dict:
    timestamp = timestamp or str(int(time.time()))
    basestring = f"v0:{timestamp}:{raw_body.decode()}"
    signature = "v0=" + hmac.new(
        config_module.SLACK_SIGNING_SECRET.encode(), basestring.encode(), hashlib.sha256
    ).hexdigest()
    return {
        "X-Slack-Request-Timestamp": timestamp,
        "X-Slack-Signature": signature,
        "Content-Type": "application/x-www-form-urlencoded",
    }


def _sample_token():
    proposal = ActionProposal(
        action_type="add_comment",
        fields={"body": "AEGIS Phase 5 approval-route test comment."},
        target_issue="AG-1",
        justification="automated test",
        confidence=0.9,
    )
    return signing.issue_token(proposal, risk_score=50)


def _audit_results():
    conn = _audit_conn()
    rows = conn.execute("SELECT result FROM audit_log ORDER BY id ASC").fetchall()
    conn.close()
    return [row[0] for row in rows]


def test_bad_signature_rejected():
    body = _interaction_body("aegis_deny", "irrelevant-token")
    headers = _sign_headers(body)
    headers["X-Slack-Signature"] = "v0=" + "0" * 64

    resp = client.post("/slack/interactions", content=body, headers=headers)

    assert resp.status_code == 401
    assert _audit_results() == []


def test_stale_timestamp_rejected():
    body = _interaction_body("aegis_deny", "irrelevant-token")
    stale_timestamp = str(int(time.time()) - 1000)
    headers = _sign_headers(body, timestamp=stale_timestamp)

    resp = client.post("/slack/interactions", content=body, headers=headers)

    assert resp.status_code == 400
    assert _audit_results() == []


def test_deny_logs_audit_entry_and_skips_execution():
    token = _sample_token()
    body = _interaction_body("aegis_deny", token)
    headers = _sign_headers(body)

    resp = client.post("/slack/interactions", content=body, headers=headers)

    assert resp.status_code == 200
    assert resp.json()["result"] == "denied"
    assert _audit_results() == ["denied"]


def test_approve_executes_real_jira_action():
    token = _sample_token()
    body = _interaction_body("aegis_approve", token)
    headers = _sign_headers(body)

    resp = client.post("/slack/interactions", content=body, headers=headers)

    assert resp.status_code == 200
    assert resp.json()["result"]["status"] == "success"
    assert _audit_results() == ["success"]
