import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from app import auth
from app import config as config_module


@pytest.fixture(autouse=True)
def test_keys(monkeypatch):
    monkeypatch.setattr(config_module, "AEGIS_API_KEYS", {"good-key": "alice@example.com"})


def test_known_key_resolves_to_requester():
    assert auth.identify_requester("good-key") == "alice@example.com"


def test_unknown_key_resolves_to_none():
    assert auth.identify_requester("bad-key") is None


def test_missing_key_resolves_to_none():
    assert auth.identify_requester(None) is None
    assert auth.identify_requester("") is None
