import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from app import config as config_module
from app.audit import pending_requests
from app.audit.audit_log import append_entry
from app.audit.reporting import compute_stats


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(config_module, "DATABASE_PATH", str(tmp_path / "test.db"))


def test_empty_log_has_zeroed_stats():
    stats = compute_stats()

    assert stats["total_actions"] == 0
    assert stats["auto_executed"] == 0
    assert stats["human_approved_executed"] == 0
    assert stats["avg_decision_seconds"] is None
    assert stats["category_breakdown"] == {}


def test_auto_executed_entry_counted_separately_from_human_approved():
    # An auto-approved action: never went through pending_requests.
    append_entry({"nonce": "auto-1"}, "success")

    # A human-approved action: went to Slack first, then resolved.
    pending_requests.record_pending("human-1", "compliance", "#aegis", "123.456")
    append_entry({"nonce": "human-1"}, "success")

    stats = compute_stats()

    assert stats["total_actions"] == 2
    assert stats["auto_executed"] == 1
    assert stats["human_approved_executed"] == 1
    assert stats["human_reviewed_total"] == 1
    assert stats["category_breakdown"] == {"compliance": 1}


def test_denied_and_rejected_and_failed_are_tallied():
    append_entry({"nonce": "n1"}, "denied")
    append_entry({"nonce": "n2"}, "rejected")
    append_entry({"nonce": "n3"}, "failure: something broke")

    stats = compute_stats()

    assert stats["denied"] == 1
    assert stats["rejected"] == 1
    assert stats["failed"] == 1


def test_still_pending_request_not_counted_as_resolved():
    pending_requests.record_pending("still-pending", "bulk", "#aegis", "1.1")

    stats = compute_stats()

    assert stats["human_reviewed_total"] == 1
    assert stats["human_reviewed_still_pending"] == 1
    assert stats["human_approved_executed"] == 0


def test_escalated_request_counted_separately():
    pending_requests.record_pending("escalated-1", "general", "#aegis", "1.1")
    pending_requests.mark_escalated("escalated-1")

    stats = compute_stats()

    assert stats["human_reviewed_escalated"] == 1
    assert stats["human_reviewed_still_pending"] == 0


def test_avg_decision_seconds_reflects_pending_to_resolution_gap():
    pending_requests.record_pending("timed-1", "general", "#aegis", "1.1")
    # Manually backdate created_at to simulate a real gap.
    conn = pending_requests._get_conn()
    with conn:
        conn.execute(
            "UPDATE pending_requests SET created_at = ? WHERE nonce = ?", (time.time() - 30, "timed-1")
        )
    append_entry({"nonce": "timed-1"}, "success")

    stats = compute_stats()

    assert stats["avg_decision_seconds"] is not None
    assert 25 <= stats["avg_decision_seconds"] <= 35
