import json

from app import config
from app.jira.client import get_issue
from app.llm.nvidia_client import chat
from app.schemas import ActionProposal, RiskAssessment

RISK_SYSTEM_PROMPT = """You are the risk classifier for AEGIS, a trust-verified automation layer for Jira.

Score the proposed Jira action from 0 (trivial, fully reversible, no sensitive data) to 100 (severe, hard to reverse, highly sensitive), based on:
- blast radius: how many people or systems are affected
- reversibility: how easily the action can be undone
- data sensitivity: whether it touches sensitive/compliance-relevant information

Return ONLY a JSON object: {"risk_score": <int 0-100>, "rationale": "<one sentence>"}"""

DONE_LIKE_TRANSITIONS = {"done", "closed"}
FORCE_APPROVAL_LABELS = {"compliance", "pci"}


def _hard_rule_reason(proposal: ActionProposal) -> str | None:
    if "delete" in proposal.action_type.lower():
        return "hard rule: delete action"
    if any("delete" in str(value).lower() for value in proposal.fields.values()):
        return "hard rule: delete action"

    if proposal.fields.get("bulk") or (proposal.target_issue and "," in proposal.target_issue):
        return "hard rule: bulk action"

    if proposal.action_type == "transition_issue" and proposal.target_issue:
        transition_name = str(proposal.fields.get("transition_name", "")).lower()
        if transition_name in DONE_LIKE_TRANSITIONS:
            issue = get_issue(proposal.target_issue)
            labels = {label.lower() for label in issue["fields"].get("labels", [])}
            matched = labels & FORCE_APPROVAL_LABELS
            if matched:
                return f"hard rule: transition to '{transition_name}' on issue labeled {sorted(matched)}"

    return None


def classify_risk(proposal: ActionProposal) -> RiskAssessment:
    forced_reason = _hard_rule_reason(proposal)
    if forced_reason:
        return RiskAssessment(
            risk_score=100,
            rationale=forced_reason,
            decision="needs_approval",
            forced=True,
        )

    messages = [
        {"role": "system", "content": RISK_SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(proposal.model_dump())},
    ]
    raw = chat(messages, model=config.NVIDIA_RISK_MODEL, api_key=config.NVIDIA_RISK_API_KEY, json_mode=True)
    result = json.loads(raw)
    risk_score = int(result["risk_score"])
    decision = "needs_approval" if risk_score >= config.RISK_APPROVAL_THRESHOLD else "auto_approve"

    return RiskAssessment(
        risk_score=risk_score,
        rationale=result.get("rationale", ""),
        decision=decision,
        forced=False,
    )
