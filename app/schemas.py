from typing import Literal

from pydantic import BaseModel


class ActionProposal(BaseModel):
    action_type: Literal["create_issue", "transition_issue", "add_comment", "search"]
    fields: dict
    target_issue: str | None = None
    justification: str
    confidence: float


class RiskAssessment(BaseModel):
    risk_score: int
    rationale: str
    decision: Literal["auto_approve", "needs_approval"]
    forced: bool = False
    category: Literal["delete", "bulk", "compliance", "general"] = "general"
