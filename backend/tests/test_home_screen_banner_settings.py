from __future__ import annotations

import json
import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from utils import admin_settings


def test_home_screen_banner_accepts_studio_cta(monkeypatch):
    monkeypatch.setattr(
        admin_settings,
        "get_setting",
        lambda key: json.dumps({"enabled": True, "cta_action": "studio"})
        if key == "home_screen_banner_json"
        else None,
    )

    banner = admin_settings.get_home_screen_banner()

    assert banner["enabled"] is True
    assert banner["cta_action"] == "studio"


def test_home_screen_banner_rejects_unknown_cta(monkeypatch):
    monkeypatch.setattr(
        admin_settings,
        "get_setting",
        lambda key: json.dumps({"cta_action": "unknown_destination"})
        if key == "home_screen_banner_json"
        else None,
    )

    assert admin_settings.get_home_screen_banner()["cta_action"] == "dismiss"
