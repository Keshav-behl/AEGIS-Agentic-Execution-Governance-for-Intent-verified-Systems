import time

from app import config
from app.approval.slack_client import escalate_unresolved
from app.audit.audit_log import find_by_nonce
from app.audit.pending_requests import all_pending_requests, mark_escalated


def sweep_sla() -> int:
    now = time.time()
    escalated_count = 0

    for row in all_pending_requests():
        if row["escalated"]:
            continue

        age = now - row["created_at"]
        if age < config.APPROVAL_SLA_SECONDS:
            continue

        if find_by_nonce(row["nonce"]) is not None:
            continue  # already resolved before the SLA hit, nothing to escalate

        if row["slack_channel"] and row["slack_ts"]:
            escalate_unresolved(row["slack_channel"], row["slack_ts"], row["category"], age)

        mark_escalated(row["nonce"])
        escalated_count += 1

    return escalated_count
