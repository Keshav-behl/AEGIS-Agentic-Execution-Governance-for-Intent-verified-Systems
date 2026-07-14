import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from app import config as config_module
from app.approval.sla import sweep_sla
from app.approval.slack_client import _client as slack_web_client
from app.audit import pending_requests
from app.audit.audit_log import append_entry


def _post_real_message(text: str) -> tuple[str, str]:
    resp = slack_web_client.chat_postMessage(channel=config_module.SLACK_APPROVAL_CHANNEL, text=text)
    return resp["channel"], resp["ts"]


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(config_module, "DATABASE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setattr(config_module, "APPROVAL_SLA_SECONDS", 5)


def _backdate(nonce: str, seconds_ago: float) -> None:
    conn = pending_requests._get_conn()
    with conn:
        conn.execute(
            "UPDATE pending_requests SET created_at = ? WHERE nonce = ?",
            (time.time() - seconds_ago, nonce),
        )


def _row(nonce: str) -> dict:
    return next(row for row in pending_requests.all_pending_requests() if row["nonce"] == nonce)


def test_fresh_pending_request_not_escalated():
    pending_requests.record_pending("fresh-1", "general", config_module.SLACK_APPROVAL_CHANNEL, None)

    escalated = sweep_sla()

    assert escalated == 0
    assert _row("fresh-1")["escalated"] is False


def test_unresolved_past_sla_gets_escalated():
    channel, ts = _post_real_message("AEGIS SLA test — this request should get escalated shortly.")
    pending_requests.record_pending("stale-1", "compliance", channel, ts)
    _backdate("stale-1", seconds_ago=10)

    escalated = sweep_sla()

    assert escalated == 1
    assert _row("stale-1")["escalated"] is True


def test_resolved_before_sla_not_escalated():
    pending_requests.record_pending("resolved-1", "general", config_module.SLACK_APPROVAL_CHANNEL, None)
    _backdate("resolved-1", seconds_ago=10)
    append_entry({"nonce": "resolved-1"}, "success")

    escalated = sweep_sla()

    assert escalated == 0
    assert _row("resolved-1")["escalated"] is False


def test_already_escalated_not_escalated_again():
    pending_requests.record_pending("double-1", "general", config_module.SLACK_APPROVAL_CHANNEL, None)
    _backdate("double-1", seconds_ago=10)

    first_pass = sweep_sla()
    second_pass = sweep_sla()

    assert first_pass == 1
    assert second_pass == 0


def test_missing_slack_ts_skips_notification_but_still_marks_escalated():
    # slack_channel/slack_ts can be None if post_approval_request ever fails
    # to return them - escalation should still mark the row so it isn't
    # rechecked forever, it just can't post a threaded reply.
    pending_requests.record_pending("no-ts-1", "general", None, None)
    _backdate("no-ts-1", seconds_ago=10)

    escalated = sweep_sla()

    assert escalated == 1
    assert _row("no-ts-1")["escalated"] is True
