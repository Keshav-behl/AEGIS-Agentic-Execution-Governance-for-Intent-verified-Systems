import json
import os

from dotenv import load_dotenv

load_dotenv()

REQUIRED_VARS = [
    "NVIDIA_API_KEY",
    "NVIDIA_BASE_URL",
    "NVIDIA_CHAT_MODEL",
    "NVIDIA_RISK_API_KEY",
    "NVIDIA_RISK_MODEL",
    "JIRA_SITE_URL",
    "JIRA_EMAIL",
    "JIRA_API_TOKEN",
    "JIRA_PROJECT_KEY",
    "SLACK_BOT_TOKEN",
    "SLACK_SIGNING_SECRET",
    "SLACK_APPROVAL_CHANNEL",
    "AEGIS_SIGNING_SECRET",
    "RISK_APPROVAL_THRESHOLD",
    "TOKEN_EXPIRY_SECONDS",
    "DATABASE_PATH",
]


def _load_required_vars() -> dict:
    missing = [name for name in REQUIRED_VARS if not os.getenv(name)]
    if missing:
        raise RuntimeError(
            "Missing required environment variable(s): "
            + ", ".join(missing)
            + ". Copy .env.example to .env and fill in real values."
        )
    return {name: os.environ[name] for name in REQUIRED_VARS}


_vars = _load_required_vars()

NVIDIA_API_KEY = _vars["NVIDIA_API_KEY"]
NVIDIA_BASE_URL = _vars["NVIDIA_BASE_URL"]
NVIDIA_CHAT_MODEL = _vars["NVIDIA_CHAT_MODEL"]
NVIDIA_RISK_API_KEY = _vars["NVIDIA_RISK_API_KEY"]
NVIDIA_RISK_MODEL = _vars["NVIDIA_RISK_MODEL"]

JIRA_SITE_URL = _vars["JIRA_SITE_URL"]
JIRA_EMAIL = _vars["JIRA_EMAIL"]
JIRA_API_TOKEN = _vars["JIRA_API_TOKEN"]
JIRA_PROJECT_KEY = _vars["JIRA_PROJECT_KEY"]

SLACK_BOT_TOKEN = _vars["SLACK_BOT_TOKEN"]
SLACK_SIGNING_SECRET = _vars["SLACK_SIGNING_SECRET"]
SLACK_APPROVAL_CHANNEL = _vars["SLACK_APPROVAL_CHANNEL"]

AEGIS_SIGNING_SECRET = _vars["AEGIS_SIGNING_SECRET"]
RISK_APPROVAL_THRESHOLD = int(_vars["RISK_APPROVAL_THRESHOLD"])
TOKEN_EXPIRY_SECONDS = int(_vars["TOKEN_EXPIRY_SECONDS"])

DATABASE_PATH = _vars["DATABASE_PATH"]

# Optional: map API keys to requester identities, e.g. {"nvapi-...": "alice@company.com"}.
# Requests to /aegis/request must carry a known key in the X-AEGIS-API-Key header.
AEGIS_API_KEYS: dict[str, str] = json.loads(os.getenv("AEGIS_API_KEYS", "{}"))

# Optional: route approval requests to a different Slack channel by risk category
# (delete/bulk/compliance/general). Falls back to SLACK_APPROVAL_CHANNEL for any
# category with no entry, e.g. {"compliance": "#aegis-compliance"}.
SLACK_ROUTING_CHANNELS: dict[str, str] = json.loads(os.getenv("SLACK_ROUTING_CHANNELS", "{}"))

# How long a pending approval can go without a decision before it's escalated.
# Should be shorter than TOKEN_EXPIRY_SECONDS so the still-valid token has time
# left to be actioned after escalation.
APPROVAL_SLA_SECONDS = int(os.getenv("APPROVAL_SLA_SECONDS", "120"))

# Optional: where to post the wider escalation notice. Defaults to the same
# channel the original request was posted to (as a threaded reply there either way).
SLACK_ESCALATION_CHANNEL = os.getenv("SLACK_ESCALATION_CHANNEL") or None
