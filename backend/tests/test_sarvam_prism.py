import asyncio
import sys
from pathlib import Path

import pytest


BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from ai import sarvam_prism


class _Response:
    def raise_for_status(self):
        return None

    def json(self):
        return {
            "answers": {
                "answer_mode": {"choice": "event_prediction", "confidence": 0.98},
                "target_subject": {"choice": "self", "confidence": 0.96},
            }
        }


class _Client:
    captured = None

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def post(self, url, *, headers, json):
        type(self).captured = {"url": url, "headers": headers, "json": json}
        return _Response()


def test_is_prism_enabled_is_opt_in(monkeypatch):
    from utils import admin_settings
    monkeypatch.setattr(admin_settings, "get_setting", lambda _key: None)
    assert sarvam_prism.is_prism_enabled() is False
    monkeypatch.setattr(admin_settings, "get_setting", lambda key: "true" if key == "sarvam_prism_enabled" else None)
    assert sarvam_prism.is_prism_enabled() is True


def test_decide_posts_typed_decision_request(monkeypatch):
    from utils import admin_settings
    monkeypatch.setattr(admin_settings, "get_setting", lambda key: "test-key" if key == "sarvam_api_key" else None)
    monkeypatch.setattr(sarvam_prism.httpx, "AsyncClient", _Client)

    result = asyncio.run(
        sarvam_prism.decide(
            state={"question": "When will I marry?"},
            questions={"answer_mode": {"type": "choice", "criteria": {"event_prediction": "When?"}}},
        )
    )

    assert result["answers"]["answer_mode"]["choice"] == "event_prediction"
    assert _Client.captured["url"] == "https://api.sarvam.ai/v2/systemone"
    assert _Client.captured["headers"]["api-subscription-key"] == "test-key"
    assert _Client.captured["json"]["model"] == "sarvam-prism"


def test_decide_requires_api_key(monkeypatch):
    from utils import admin_settings
    monkeypatch.setattr(admin_settings, "get_setting", lambda _key: None)
    with pytest.raises(RuntimeError, match="Admin Settings"):
        asyncio.run(sarvam_prism.decide(state={}, questions={}))
