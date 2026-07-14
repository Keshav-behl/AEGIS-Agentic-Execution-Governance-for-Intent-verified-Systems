from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.agent.intent_agent import propose_action
from app.agent.risk_classifier import classify_risk
from app.api.dashboard import render_dashboard
from app.approval.slack_client import post_approval_request
from app.audit.audit_log import find_by_nonce
from app.audit.pending_requests import record_pending
from app.audit.reporting import compute_stats
from app.auth import identify_requester
from app.protocol import signing
from app.protocol.executor import execute

router = APIRouter()


class AegisRequest(BaseModel):
    text: str


@router.post("/aegis/request")
def create_request(body: AegisRequest, x_aegis_api_key: str = Header(...)):
    requester = identify_requester(x_aegis_api_key)
    if requester is None:
        raise HTTPException(status_code=401, detail="Missing or unrecognized X-AEGIS-API-Key")

    proposal = propose_action(body.text)
    risk = classify_risk(proposal)
    token = signing.issue_token(proposal, risk.risk_score, requester=requester)
    request_id = signing.peek(token)["nonce"]

    if risk.decision == "auto_approve":
        result = execute(token)
        status = "auto_executed" if result["status"] == "success" else "auto_execution_failed"
        return {"status": status, "request_id": request_id, "detail": result}

    slack_resp = post_approval_request(proposal, risk, token, requester=requester)
    record_pending(request_id, risk.category, slack_resp.get("channel"), slack_resp.get("ts"))
    return {
        "status": "pending_approval",
        "request_id": request_id,
        "detail": {
            "risk_score": risk.risk_score,
            "rationale": risk.rationale,
            "action_type": proposal.action_type,
            "target_issue": proposal.target_issue,
        },
    }


@router.get("/aegis/status/{request_id}")
def get_status(request_id: str):
    entry = find_by_nonce(request_id)
    if entry is None:
        return {"status": "pending_approval", "request_id": request_id}

    result = entry["result"]
    if result == "success":
        status = "executed"
    elif result in ("denied", "rejected"):
        status = result
    else:
        status = "failed"

    return {"status": status, "request_id": request_id, "detail": entry["payload"]}


@router.get("/aegis/report")
def get_report():
    return compute_stats()


@router.get("/aegis/dashboard", response_class=HTMLResponse)
def get_dashboard():
    return render_dashboard(compute_stats())
