import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agent.risk_classifier import classify_risk
from app.schemas import ActionProposal


def test_add_comment_scores_low_and_auto_approves():
    proposal = ActionProposal(
        action_type="add_comment",
        fields={"body": "Deployment complete, no issues observed."},
        target_issue="AG-1",
        justification="user asked to add a status comment",
        confidence=0.95,
    )

    result = classify_risk(proposal)

    assert result.forced is False
    assert result.decision == "auto_approve"
    assert result.risk_score < 40
    assert result.category == "general"


def test_compliance_labeled_transition_to_done_forces_approval():
    # AG-1 is labeled "compliance" (see fixture setup).
    proposal = ActionProposal(
        action_type="transition_issue",
        fields={"transition_name": "Done"},
        target_issue="AG-1",
        justification="user asked to close the ticket",
        confidence=0.9,
    )

    result = classify_risk(proposal)

    assert result.forced is True
    assert result.decision == "needs_approval"
    assert result.risk_score == 100
    assert result.category == "compliance"


def test_delete_action_forces_approval_with_delete_category():
    proposal = ActionProposal(
        action_type="transition_issue",
        fields={"transition_name": "delete"},
        target_issue="AG-1",
        justification="user asked to delete the ticket",
        confidence=0.9,
    )

    result = classify_risk(proposal)

    assert result.forced is True
    assert result.category == "delete"


def test_bulk_action_forces_approval_with_bulk_category():
    proposal = ActionProposal(
        action_type="add_comment",
        fields={"body": "bulk update", "bulk": True},
        target_issue="AG-1",
        justification="user asked to comment on many issues",
        confidence=0.9,
    )

    result = classify_risk(proposal)

    assert result.forced is True
    assert result.category == "bulk"
