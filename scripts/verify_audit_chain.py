import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config
from app.audit.audit_log import verify_chain


def main():
    conn = sqlite3.connect(config.DATABASE_PATH)
    rows = conn.execute(
        "SELECT id, timestamp, prev_hash, result, hash FROM audit_log ORDER BY id ASC"
    ).fetchall()

    print(f"Audit log: {len(rows)} entr{'y' if len(rows) == 1 else 'ies'}\n")
    for row_id, timestamp, prev_hash, result, entry_hash in rows:
        print(f"  #{row_id}  result={result}  prev_hash={prev_hash[:12]}...  hash={entry_hash[:12]}...")

    print()
    ok = verify_chain()
    print("Chain verifies: TRUE" if ok else "Chain verifies: FALSE")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
