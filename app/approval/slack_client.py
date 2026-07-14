import json

import httpx
from slack_sdk import WebClient

from app import config
from app.schemas import ActionProposal, RiskAssessment

_client = WebClient(token=config.SLACK_BOT_TOKEN)


def update_message(response_url: str, text: str, blocks: list) -> None:
    resp = httpx.post(
        response_url,
        json={"replace_original": True, "text": text, "blocks": blocks},
        timeout=10.0,
    )
    resp.raise_for_status()


def _channel_for_category(category: str) -> str:
    return config.SLACK_ROUTING_CHANNELS.get(category, config.SLACK_APPROVAL_CHANNEL)


def post_approval_request(
    proposal: ActionProposal, risk: RiskAssessment, token: str, requester: str | None = None
) -> dict:
    summary_lines = [
        "*AEGIS approval needed*",
        f"*Requested by:* {requester or 'unknown (no API key)'}",
        f"*Action:* `{proposal.action_type}`" + (f" on `{proposal.target_issue}`" if proposal.target_issue else ""),
        f"*Category:* {risk.category}",
        f"*Risk score:* {risk.risk_score}/100" + (" _(forced by hard rule)_" if risk.forced else ""),
        f"*Rationale:* {risk.rationale}",
        f"*Justification:* {proposal.justification}",
        f"*Fields:*\n```{json.dumps(proposal.fields, indent=2)}```",
    ]

    blocks = [
        {"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(summary_lines)}},
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Approve"},
                    "style": "primary",
                    "action_id": "aegis_approve",
                    "value": token,
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Deny"},
                    "style": "danger",
                    "action_id": "aegis_deny",
                    "value": token,
                },
            ],
        },
    ]

    return _client.chat_postMessage(
        channel=_channel_for_category(risk.category),
        text=f"AEGIS approval needed: {proposal.action_type} (risk {risk.risk_score}/100)",
        blocks=blocks,
    )
