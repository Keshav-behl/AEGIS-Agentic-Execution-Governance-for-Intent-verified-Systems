import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from app.protocol import signing
from app.schemas import ActionProposal


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(signing.config, "DATABASE_PATH", str(tmp_path / "test.db"))


def _sample_proposal():
    return ActionProposal(
        action_type="add_comment",
        fields={"body": "test comment"},
        target_issue="AG-1",
        justification="test",
        confidence=0.9,
    )


def test_valid_token_round_trips():
    proposal = _sample_proposal()
    token = signing.issue_token(proposal, risk_score=10)

    verified = signing.verify_token(token)

    assert verified.action_type == proposal.action_type
    assert verified.target_issue == proposal.target_issue
    assert verified.fields == proposal.fields


def test_tampered_signature_rejected():
    token = signing.issue_token(_sample_proposal(), risk_score=10)
    encoded_payload, signature = token.rsplit(".", 1)
    flipped_char = "1" if signature[0] == "0" else "0"
    tampered = f"{encoded_payload}.{flipped_char}{signature[1:]}"

    with pytest.raises(signing.TokenError):
        signing.verify_token(tampered)


def test_tampered_payload_rejected():
    token = signing.issue_token(_sample_proposal(), risk_score=10)
    encoded_payload, signature = token.rsplit(".", 1)
    flipped_char = "1" if encoded_payload[0] == "0" else "0"
    tampered = f"{flipped_char}{encoded_payload[1:]}.{signature}"

    with pytest.raises(signing.TokenError):
        signing.verify_token(tampered)


def test_expired_token_rejected(monkeypatch):
    monkeypatch.setattr(signing.config, "TOKEN_EXPIRY_SECONDS", -1)
    token = signing.issue_token(_sample_proposal(), risk_score=10)

    with pytest.raises(signing.TokenError):
        signing.verify_token(token)


def test_replayed_token_rejected():
    token = signing.issue_token(_sample_proposal(), risk_score=10)

    signing.verify_token(token)  # first use succeeds
    with pytest.raises(signing.TokenError):
        signing.verify_token(token)  # replay rejected
