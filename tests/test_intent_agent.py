import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agent.intent_agent import propose_action

CASES = [
    (
        "create a bug ticket for the login page timeout and assign it to backend",
        "create_issue",
        None,
    ),
    (
        "add a comment on AG-1 saying deployment is complete",
        "add_comment",
        "AG-1",
    ),
    (
        "move AG-1 to done",
        "transition_issue",
        "AG-1",
    ),
    (
        "show me all open bugs assigned to me",
        "search",
        None,
    ),
    (
        "create a task to update the onboarding docs",
        "create_issue",
        None,
    ),
    (
        "comment on AG-2 that we're waiting on vendor response",
        "add_comment",
        "AG-2",
    ),
    (
        "transition AG-3 to in progress",
        "transition_issue",
        "AG-3",
    ),
    (
        "find all issues created this week",
        "search",
        None,
    ),
    (
        "create a story for adding dark mode support",
        "create_issue",
        None,
    ),
    (
        "close AG-4",
        "transition_issue",
        "AG-4",
    ),
]


@pytest.mark.parametrize("text,expected_action_type,expected_target", CASES)
def test_propose_action(text, expected_action_type, expected_target):
    proposal = propose_action(text)

    assert proposal.action_type == expected_action_type
    assert 0.0 <= proposal.confidence <= 1.0
    assert proposal.fields

    if expected_target is not None:
        assert proposal.target_issue == expected_target
