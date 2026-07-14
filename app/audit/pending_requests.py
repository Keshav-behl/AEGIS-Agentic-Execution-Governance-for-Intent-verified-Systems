import sqlite3
import time

from app import config


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pending_requests (
            nonce TEXT PRIMARY KEY,
            created_at REAL NOT NULL,
            category TEXT NOT NULL,
            slack_channel TEXT,
            slack_ts TEXT,
            escalated INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    return conn


def record_pending(nonce: str, category: str, slack_channel: str | None, slack_ts: str | None) -> None:
    conn = _get_conn()
    with conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO pending_requests
                (nonce, created_at, category, slack_channel, slack_ts, escalated)
            VALUES (?, ?, ?, ?, ?, 0)
            """,
            (nonce, time.time(), category, slack_channel, slack_ts),
        )


def all_pending_requests() -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT nonce, created_at, category, slack_channel, slack_ts, escalated FROM pending_requests"
    ).fetchall()
    return [
        {
            "nonce": r[0],
            "created_at": r[1],
            "category": r[2],
            "slack_channel": r[3],
            "slack_ts": r[4],
            "escalated": bool(r[5]),
        }
        for r in rows
    ]


def mark_escalated(nonce: str) -> None:
    conn = _get_conn()
    with conn:
        conn.execute("UPDATE pending_requests SET escalated = 1 WHERE nonce = ?", (nonce,))
