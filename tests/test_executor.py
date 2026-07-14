import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from app import config as config_module
from app.protocol import executor, signing
from app.schemas import ActionProposal


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(config_module, "DATABASE_PATH", str(tmp_path / "test.db"))


def _audit_results():
    conn = sqlite3.connect(config_module.DATABASE_PATH)
    rows = conn.execute("SELECT result FROM audit_log ORDER BY id ASC").fetchall()
    conn.close()
    return [row[0] for row in rows]


def test_execute_add_comment_success():
    proposal = ActionProposal(
        action_type="add_comment",
        fields={"body": "AEGIS Phase 6 executor test comment."},
        target_issue="AG-1",
        justification="automated test",
        confidence=0.9,
    )
    token = signing.issue_token(proposal, risk_score=10)

    result = executor.execute(token)

    assert result["status"] == "success"
    assert _audit_results() == ["success"]


def test_execute_invalid_token_rejected():
    result = executor.execute("not-a-real-token")

    assert result["status"] == "rejected"
    assert _audit_results() == ["rejected"]


def test_execute_jira_failure_logs_failure():
    proposal = ActionProposal(
        action_type="transition_issue",
        fields={"transition_name": "Definitely Not A Real Transition"},
        target_issue="AG-1",
        justification="automated test",
        confidence=0.9,
    )
    token = signing.issue_token(proposal, risk_score=10)

    result = executor.execute(token)

    assert result["status"] == "failure"
    results = _audit_results()
    assert len(results) == 1
    assert results[0].startswith("failure")
