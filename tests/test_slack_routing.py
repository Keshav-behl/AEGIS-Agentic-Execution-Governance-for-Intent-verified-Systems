import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from app import config as config_module
from app.approval import slack_client


@pytest.fixture(autouse=True)
def routing_config(monkeypatch):
    monkeypatch.setattr(config_module, "SLACK_APPROVAL_CHANNEL", "#aegis")
    monkeypatch.setattr(config_module, "SLACK_ROUTING_CHANNELS", {"compliance": "#aegis-compliance"})


def test_configured_category_routes_to_its_channel():
    assert slack_client._channel_for_category("compliance") == "#aegis-compliance"


def test_unconfigured_category_falls_back_to_default_channel():
    assert slack_client._channel_for_category("bulk") == "#aegis"
    assert slack_client._channel_for_category("general") == "#aegis"


def test_empty_routing_map_always_falls_back(monkeypatch):
    monkeypatch.setattr(config_module, "SLACK_ROUTING_CHANNELS", {})

    assert slack_client._channel_for_category("compliance") == "#aegis"
