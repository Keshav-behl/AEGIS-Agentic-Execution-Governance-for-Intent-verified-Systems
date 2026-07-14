import json

from pydantic import ValidationError

from app.llm.nvidia_client import chat
from app.schemas import ActionProposal

SYSTEM_PROMPT = """You are the intent agent for AEGIS, a trust-verified automation layer for Jira.

Given a natural-language request, output ONLY a single JSON object (no markdown, no prose, no code fences) matching this schema:

{
  "action_type": "create_issue" | "transition_issue" | "add_comment" | "search",
  "fields": { ... },
  "target_issue": "<Jira issue key like AG-123, or null>",
  "justification": "<one sentence explaining your interpretation>",
  "confidence": <float between 0.0 and 1.0>
}

Rules for "fields" by action_type:
- create_issue: {"issue_type": "Task"|"Bug"|"Story", "summary": "...", "description": "...", "assignee": "<name or null>"}
- transition_issue: {"transition_name": "<e.g. Done, In Progress, Closed>"}
- add_comment: {"body": "..."}
- search: {"jql": "<a valid JQL query string>"}

target_issue MUST be a real issue key extracted from the request for transition_issue and add_comment.
target_issue MUST be null for create_issue and search.
If confidence is low, still make your best guess but lower the confidence score.
Return ONLY the JSON object, nothing else."""


def propose_action(user_text: str) -> ActionProposal:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
    ]
    raw = chat(messages, json_mode=True)

    try:
        return ActionProposal.model_validate(json.loads(raw))
    except (json.JSONDecodeError, ValidationError) as error:
        retry_messages = messages + [
            {"role": "assistant", "content": raw},
            {
                "role": "user",
                "content": f"That response was invalid: {error}. Return ONLY a corrected JSON object matching the schema.",
            },
        ]
        raw_retry = chat(retry_messages, json_mode=True)
        return ActionProposal.model_validate(json.loads(raw_retry))
