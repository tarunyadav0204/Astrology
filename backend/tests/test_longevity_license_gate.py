import asyncio

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from auth import User
from longevity.routes import LongevityRequest, calculate_longevity


def test_longevity_route_requires_astrologer_entitlement(monkeypatch):
    checked = {}

    def reject_unlicensed(user, entitlement):
        checked["user"] = user.userid
        checked["entitlement"] = entitlement
        raise HTTPException(status_code=403, detail={"code": "ASTROLOGER_LICENSE_REQUIRED"})

    monkeypatch.setattr("longevity.routes.require_entitlement", reject_unlicensed)
    request = LongevityRequest(
        birth_data={"name": "Gate test"},
        chart_data={"ascendant": 0, "planets": {}},
    )
    user = User(userid=42, name="Tester", phone="000", role="user")

    with pytest.raises(HTTPException) as raised:
        asyncio.run(calculate_longevity(request, user))

    assert raised.value.status_code == 403
    assert raised.value.detail["code"] == "ASTROLOGER_LICENSE_REQUIRED"
    assert checked == {"user": 42, "entitlement": "astrologer_tools"}


def test_longevity_request_rejects_unknown_ashtakavarga_profile():
    with pytest.raises(ValidationError):
        LongevityRequest(
            birth_data={"name": "Profile test"},
            ashtakavarga_profile="unpublished_blend",
        )


def test_longevity_route_passes_selected_ashtakavarga_profile(monkeypatch):
    captured = {}

    class RecordingCalculator:
        def __init__(self, birth_data, chart_data, subject, ashtakavarga_profile):
            captured.update({
                "birth_data": birth_data,
                "chart_data": chart_data,
                "subject": subject,
                "ashtakavarga_profile": ashtakavarga_profile,
            })

        def calculate(self, horizon_years):
            captured["horizon_years"] = horizon_years
            return {"profile": captured["ashtakavarga_profile"]}

    monkeypatch.setattr("longevity.routes.require_entitlement", lambda *_args: None)
    monkeypatch.setattr("longevity.routes.LongevityCalculator", RecordingCalculator)
    chart = {"ascendant": 0, "planets": {}}
    request = LongevityRequest(
        birth_data={"name": "Profile route test"},
        chart_data=chart,
        subject="mother",
        horizon_years=8,
        ashtakavarga_profile="parasharas_light_7",
    )
    user = User(userid=42, name="Tester", phone="000", role="user")

    response = asyncio.run(calculate_longevity(request, user))

    assert response == {"success": True, "result": {"profile": "parasharas_light_7"}}
    assert captured["chart_data"] == chart
    assert captured["subject"] == "mother"
    assert captured["horizon_years"] == 8
    assert captured["ashtakavarga_profile"] == "parasharas_light_7"
