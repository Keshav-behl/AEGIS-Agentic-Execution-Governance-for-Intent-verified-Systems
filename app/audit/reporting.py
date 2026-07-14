import json

from app.audit.audit_log import _get_conn as _audit_conn
from app.audit.pending_requests import all_pending_requests


def compute_stats() -> dict:
    audit_rows = _audit_conn().execute(
        "SELECT timestamp, payload_json, result FROM audit_log ORDER BY id ASC"
    ).fetchall()
    pending_rows = all_pending_requests()
    pending_by_nonce = {row["nonce"]: row for row in pending_rows}

    counts = {"success": 0, "denied": 0, "rejected": 0, "failed": 0}
    auto_executed = 0
    human_approved_executed = 0
    decision_seconds = []
    resolved_nonces = set()

    for timestamp, payload_json, result in audit_rows:
        if result == "success":
            counts["success"] += 1
        elif result == "denied":
            counts["denied"] += 1
        elif result == "rejected":
            counts["rejected"] += 1
        else:
            counts["failed"] += 1

        nonce = json.loads(payload_json).get("nonce")
        pending = pending_by_nonce.get(nonce) if nonce else None
        if pending:
            resolved_nonces.add(nonce)
            decision_seconds.append(timestamp - pending["created_at"])
            if result == "success":
                human_approved_executed += 1
        elif result == "success":
            auto_executed += 1

    category_breakdown: dict[str, int] = {}
    for row in pending_rows:
        category_breakdown[row["category"]] = category_breakdown.get(row["category"], 0) + 1

    still_pending = sum(1 for row in pending_rows if row["nonce"] not in resolved_nonces and not row["escalated"])
    escalated = sum(1 for row in pending_rows if row["escalated"])

    return {
        "total_actions": len(audit_rows),
        "auto_executed": auto_executed,
        "human_approved_executed": human_approved_executed,
        "denied": counts["denied"],
        "rejected": counts["rejected"],
        "failed": counts["failed"],
        "human_reviewed_total": len(pending_rows),
        "human_reviewed_still_pending": still_pending,
        "human_reviewed_escalated": escalated,
        "avg_decision_seconds": (sum(decision_seconds) / len(decision_seconds)) if decision_seconds else None,
        "category_breakdown": category_breakdown,
    }
