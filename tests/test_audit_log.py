import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from app.audit import audit_log


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(audit_log.config, "DATABASE_PATH", str(tmp_path / "test.db"))


def test_clean_chain_verifies_true():
    audit_log.append_entry({"action": "add_comment"}, "success")
    audit_log.append_entry({"action": "transition_issue"}, "success")
    audit_log.append_entry({"action": "search"}, "denied")

    assert audit_log.verify_chain() is True


def test_tampered_row_breaks_chain_and_identifies_it(capsys):
    audit_log.append_entry({"action": "add_comment"}, "success")
    audit_log.append_entry({"action": "transition_issue"}, "success")

    conn = sqlite3.connect(audit_log.config.DATABASE_PATH)
    conn.execute("UPDATE audit_log SET payload_json = ? WHERE id = 1", ('{"action":"tampered"}',))
    conn.commit()
    conn.close()

    assert audit_log.verify_chain() is False
    assert "row 1" in capsys.readouterr().out
