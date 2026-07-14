import hashlib
import json
import sqlite3
import time

from app import config

GENESIS_HASH = "0" * 64


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            prev_hash TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            result TEXT NOT NULL,
            hash TEXT NOT NULL
        )
        """
    )
    return conn


def _compute_hash(prev_hash: str, payload_json: str, result: str) -> str:
    return hashlib.sha256((prev_hash + payload_json + result).encode()).hexdigest()


def _last_hash(conn: sqlite3.Connection) -> str:
    row = conn.execute("SELECT hash FROM audit_log ORDER BY id DESC LIMIT 1").fetchone()
    return row[0] if row else GENESIS_HASH


def append_entry(payload: dict, result: str) -> int:
    conn = _get_conn()
    with conn:
        prev_hash = _last_hash(conn)
        payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        entry_hash = _compute_hash(prev_hash, payload_json, result)
        cursor = conn.execute(
            "INSERT INTO audit_log (timestamp, prev_hash, payload_json, result, hash) VALUES (?, ?, ?, ?, ?)",
            (time.time(), prev_hash, payload_json, result, entry_hash),
        )
        return cursor.lastrowid


def find_by_nonce(nonce: str) -> dict | None:
    conn = _get_conn()
    rows = conn.execute("SELECT result, payload_json FROM audit_log ORDER BY id ASC").fetchall()
    for result, payload_json in rows:
        payload = json.loads(payload_json)
        if payload.get("nonce") == nonce:
            return {"result": result, "payload": payload}
    return None


def verify_chain() -> bool:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, prev_hash, payload_json, result, hash FROM audit_log ORDER BY id ASC"
    ).fetchall()

    expected_prev_hash = GENESIS_HASH
    for row_id, prev_hash, payload_json, result, stored_hash in rows:
        if prev_hash != expected_prev_hash:
            print(f"Chain broken at row {row_id}: prev_hash does not match preceding row's hash")
            return False

        recomputed_hash = _compute_hash(prev_hash, payload_json, result)
        if recomputed_hash != stored_hash:
            print(f"Chain broken at row {row_id}: stored hash does not match recomputed hash (payload tampered)")
            return False

        expected_prev_hash = stored_hash

    return True
