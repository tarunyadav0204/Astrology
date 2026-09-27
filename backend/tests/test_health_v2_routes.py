import asyncio

import pytest
from fastapi import HTTPException

from auth import User
from health_v2.routes import NatalBlueprintRequest, TimingHeatmapRequest, natal_blueprint, timing_heatmap


def test_health_v2_route_requires_astrologer_entitlement(monkeypatch):
    checked = {}

    def reject(user, entitlement):
        checked.update(user=user.userid, entitlement=entitlement)
        raise HTTPException(status_code=403, detail={"code": "ASTROLOGER_LICENSE_REQUIRED"})

    monkeypatch.setattr("health_v2.routes.require_entitlement", reject)
    request = NatalBlueprintRequest(birth_data={"name": "Gate test"}, chart_data={"planets": {}, "houses": []})
    user = User(userid=42, name="Tester", phone="000", role="user")

    with pytest.raises(HTTPException) as raised:
        asyncio.run(natal_blueprint(request, user))

    assert raised.value.status_code == 403
    assert checked == {"user": 42, "entitlement": "astrologer_tools"}


def test_health_v2_route_returns_isolated_preview(monkeypatch):
    chart = {
        "ascendant": 5.0,
        "houses": [{"house": house, "sign": house - 1} for house in range(1, 13)],
        "planets": {
            "Sun": {"house": 5, "sign": 4}, "Moon": {"house": 4, "sign": 3},
            "Mars": {"house": 1, "sign": 0}, "Mercury": {"house": 6, "sign": 5},
            "Jupiter": {"house": 9, "sign": 8}, "Venus": {"house": 7, "sign": 6},
            "Saturn": {"house": 10, "sign": 9}, "Rahu": {"house": 11, "sign": 10},
            "Ketu": {"house": 5, "sign": 4},
        },
        "graha_drishti_by_house": {},
    }
    monkeypatch.setattr("health_v2.routes.require_entitlement", lambda *_args: None)
    request = NatalBlueprintRequest(birth_data={"name": "Preview"}, chart_data=chart)
    user = User(userid=42, name="Tester", phone="000", role="user")

    response = asyncio.run(natal_blueprint(request, user))

    assert response["success"] is True
    assert response["result"]["status"] == "preview"
    assert response["result"]["legacy_health_unchanged"] is True


def test_health_v2_route_passes_female_chart_context_to_the_health_engine(monkeypatch):
    chart = {
        "ascendant": 5.0,
        "houses": [{"house": house, "sign": house - 1} for house in range(1, 13)],
        "planets": {
            "Sun": {"house": 5, "sign": 4}, "Moon": {"house": 4, "sign": 3},
            "Mars": {"house": 1, "sign": 0}, "Mercury": {"house": 6, "sign": 5},
            "Jupiter": {"house": 9, "sign": 8}, "Venus": {"house": 7, "sign": 6},
            "Saturn": {"house": 10, "sign": 9}, "Rahu": {"house": 11, "sign": 10},
            "Ketu": {"house": 5, "sign": 4},
        },
        "graha_drishti_by_house": {},
    }
    monkeypatch.setattr("health_v2.routes.require_entitlement", lambda *_args: None)
    request = NatalBlueprintRequest(
        birth_data={"name": "Female chart", "gender": "Female"},
        chart_data=chart,
    )
    user = User(userid=42, name="Tester", phone="000", role="user")

    response = asyncio.run(natal_blueprint(request, user))

    menstrual = response["result"]["female_health"]["menstrual_cycle"]
    assert menstrual["analyzed"] is True
    assert menstrual["status"] in {"heightened_attention", "some_sensitivity", "no_distinct_pattern"}


def test_health_v2_route_calculates_charak_medical_vargas_when_longitudes_exist(monkeypatch):
    chart = {
        "ascendant": 5.0,
        "houses": [{"house": house, "sign": house - 1} for house in range(1, 13)],
        "planets": {
            planet: {"house": index + 1, "sign": index, "longitude": index * 30.0 + 5.0}
            for index, planet in enumerate(("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"))
        },
        "graha_drishti_by_house": {},
    }
    calls = []

    def fake_division(source, division):
        calls.append(division)
        return {"divisional_chart": source}

    monkeypatch.setattr("health_v2.routes.require_entitlement", lambda *_args: None)
    monkeypatch.setattr("health_v2.routes.calculate_divisional_chart", fake_division)
    request = NatalBlueprintRequest(birth_data={"name": "Varga test"}, chart_data=chart)
    user = User(userid=42, name="Tester", phone="000", role="user")

    response = asyncio.run(natal_blueprint(request, user))

    assert calls == [3, 9, 12]
    confirmation = response["result"]["constitutional_protection"]["planet_conditions"]["Sun"]["divisional_confirmation"]
    assert set(confirmation) == {"D3", "D9", "D12"}


def test_health_timing_route_is_licensed_and_returns_heatmap(monkeypatch):
    chart = {
        "ascendant": 5.0,
        "houses": [{"house": house, "sign": house - 1} for house in range(1, 13)],
        "planets": {
            planet: {"house": index + 1, "sign": index, "longitude": index * 30.0 + 5.0}
            for index, planet in enumerate(("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"))
        },
        "graha_drishti_by_house": {},
    }
    checked = []
    monkeypatch.setattr("health_v2.routes.require_entitlement", lambda user, entitlement: checked.append(entitlement))
    monkeypatch.setattr("health_v2.routes.calculate_divisional_chart", lambda source, _division: {"divisional_chart": source})
    monkeypatch.setattr(
        "health_v2.routes.HealthTimingHeatmapEngine.calculate",
        lambda self, start_date, days: {"schema_version": "health.timing_heatmap.v1", "days": [], "start_date": str(start_date)},
    )
    request = TimingHeatmapRequest(
        birth_data={"name": "Timing"}, chart_data=chart, start_date="2026-09-01", days=30
    )
    user = User(userid=42, name="Tester", phone="000", role="user")
    response = asyncio.run(timing_heatmap(request, user))
    assert checked == ["astrologer_tools"]
    assert response["result"]["schema_version"] == "health.timing_heatmap.v1"
