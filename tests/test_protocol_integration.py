import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from app.audit import audit_log
from app.protocol import signing
from app.schemas import ActionProposal


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(signing.config, "DATABASE_PATH", db_path)


def test_full_signed_flow_produces_verifying_chain():
    proposal = ActionProposal(
        action_type="add_comment",
        fields={"body": "Deployment complete."},
        target_issue="AG-1",
        justification="user asked to add a status comment",
        confidence=0.95,
    )

    token = signing.issue_token(proposal, risk_score=15)
    verified_proposal = signing.verify_token(token)  # simulates the executor's fail-closed verify step

    result = "executed"  # simulates the real Jira call the Phase 6 executor will make
    audit_log.append_entry(
        {"action_proposal": verified_proposal.model_dump(), "risk_score": 15},
        result,
    )

    assert audit_log.verify_chain() is True
