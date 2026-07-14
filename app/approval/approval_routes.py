import hashlib
import hmac
import json
import time

from fastapi import APIRouter, Header, HTTPException, Request

from app import config
from app.approval.slack_client import update_message
from app.audit.audit_log import append_entry
from app.protocol import signing
from app.protocol.executor import execute

router = APIRouter()


def _verify_slack_signature(raw_body: bytes, timestamp: str, signature: str) -> None:
    if abs(time.time() - int(timestamp)) > 60 * 5:
        raise HTTPException(status_code=400, detail="Stale Slack request")

    basestring = f"v0:{timestamp}:{raw_body.decode()}"
    computed = "v0=" + hmac.new(
        config.SLACK_SIGNING_SECRET.encode(), basestring.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed, signature):
        raise HTTPException(status_code=401, detail="Invalid Slack signature")


@router.post("/slack/interactions")
async def slack_interactions(
    request: Request,
    x_slack_signature: str = Header(...),
    x_slack_request_timestamp: str = Header(...),
):
    raw_body = await request.body()
    _verify_slack_signature(raw_body, x_slack_request_timestamp, x_slack_signature)

    form = await request.form()
    payload = json.loads(form["payload"])
    action = payload["actions"][0]
    action_id = action["action_id"]
    token = action["value"]

    user = payload.get("user", {}).get("username") or payload.get("user", {}).get("id", "someone")
    response_url = payload.get("response_url")
    kept_blocks = [
        block for block in payload.get("message", {}).get("blocks", []) if block.get("type") != "actions"
    ]

    def _replace_with_outcome(outcome_text: str) -> None:
        if not response_url:
            return
        kept_blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": outcome_text}]})
        update_message(response_url, text=outcome_text, blocks=kept_blocks)

    if action_id == "aegis_approve":
        result = execute(token)
        if result["status"] == "success":
            outcome = f":white_check_mark: *Approved* by @{user} — executed successfully."
        else:
            outcome = f":warning: *Approved* by @{user}, but {result['status']}: {result['error']}"
        _replace_with_outcome(outcome)
        return {"status": "ok", "result": result}

    if action_id == "aegis_deny":
        try:
            nonce = signing.peek(token)["nonce"]
        except signing.TokenError:
            nonce = None
        try:
            proposal = signing.verify_token(token)
            record = {"action_proposal": proposal.model_dump(), "nonce": nonce}
        except signing.TokenError as error:
            record = {"token_error": str(error), "nonce": nonce}
        append_entry(record, "denied")
        _replace_with_outcome(f":no_entry: *Denied* by @{user}.")
        return {"status": "ok", "result": "denied"}

    raise HTTPException(status_code=400, detail=f"Unknown action_id: {action_id}")
