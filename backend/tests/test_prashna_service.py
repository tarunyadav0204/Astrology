import asyncio
from unittest.mock import patch

import httpx
import pytest
from fastapi import FastAPI

from auth import User, get_current_user
from prashna.routes import credit_service, router
from prashna.service import _question_clock, _validate_analysis_contract, analyze_prashna


def fake_chart(_clock):
    def p(longitude, speed, house):
        return {"longitude": longitude, "tropical_longitude": longitude + 23, "speed": speed,
                "retrograde": speed < 0, "sign": int(longitude // 30), "sign_name": "sign",
                "degree": longitude % 30, "house": house, "house_strength": 10}
    planets = {"Sun": p(130, 1, 5), "Moon": p(10, 13, 1), "Mars": p(75, .5, 3),
               "Mercury": p(35, 1.2, 2), "Jupiter": p(15, .08, 1), "Venus": p(65, 1.1, 3),
               "Saturn": p(15, .03, 1), "Rahu": p(305, -.05, 11), "Ketu": p(125, -.05, 5)}
    return {"ascendant": 0.0, "midheaven": 270.0, "planets": planets,
            "houses": [{"house": i + 1, "cusp": i * 30, "cusp_sign": i,
                        "begin_junction": (i * 30 - 15) % 360, "end_junction": (i * 30 + 15) % 360}
                       for i in range(12)],
            "calculation": {"profile_id": "hayanaratna_textual_precession_quadrant_v1",
                "ayanamsha": "Hayanaratna 1.9 textual precession", "ayanamsha_degrees": 22.9,
                "house_system": "Hayanaratna quadrant cusps and junctions (Sripati geometry)",
                "ephemeris": ["Swiss Ephemeris"]}}


def request(**overrides):
    data = dict(question_id="career_job_offer", date="2026-09-19", time="14:30:23",
                latitude=28.4595, longitude=77.0266,
                timezone="Asia/Kolkata", place="Gurgaon")
    data.update(overrides)
    return data


async def post_to_prashna(path, payload, *, balance=100, spend=True):
    app = FastAPI(); app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: User(userid=7, name="Test", phone="1", role="user")
    with patch.object(credit_service, "get_credit_setting", return_value=3), \
         patch.object(credit_service, "get_effective_cost", return_value=3), \
         patch.object(credit_service, "get_user_credits", return_value=balance), \
         patch.object(credit_service, "spend_credits", return_value=spend):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            return await client.post(path, json=payload)


@patch("prashna.service.ClassicalPrashnaChartCalculator")
def test_analysis_uses_confirmed_moment_and_new_profile(calculator):
    calculator.return_value.calculate_chart.side_effect = fake_chart
    result = analyze_prashna(**request())
    assert result["question"]["status"] == "selected"
    assert result["question"]["question_id"] == "career_job_offer"
    assert result["clock"]["source"] == "guided_question_selection"
    assert result["verdict"]["result"] in {"favorable", "unfavorable", "mixed", "cannot_judge"}
    assert result["calculation"]["profile_id"] == "hayanaratna_textual_precession_quadrant_v1"
    assert result["classical"]["ruleset_version"] == "prashnatantra-tajika-2.0.0"
    assert "kp_overlay" not in result


@patch("prashna.service.ClassicalPrashnaChartCalculator")
def test_unknown_question_id_fails_before_chart_cast(calculator):
    with pytest.raises(ValueError, match="supported Prashna questions"):
        analyze_prashna(**request(question_id="made_up"))
    calculator.return_value.calculate_chart.assert_not_called()


@pytest.mark.parametrize("question_id,expected_topic,heading_text", [
    ("relationship_contact", "relationship", "renewed contact"),
    ("relationship_unblock", "relationship", "contact being reopened"),
    ("relationship_reconcile", "relationship", "reconciliation after the conflict"),
    ("relationship_return", "relationship", "return to the relationship"),
    ("relationship_marriage", "marriage", "marriage with this person"),
])
@patch("prashna.service.ClassicalPrashnaChartCalculator")
def test_relationship_questions_run_end_to_end(calculator, question_id, expected_topic, heading_text):
    calculator.return_value.calculate_chart.side_effect = fake_chart
    result = analyze_prashna(**request(question_id=question_id))
    assert result["classical"]["topic"] == expected_topic
    assert heading_text in result["presentation"]["heading"]


def test_clock_validation_and_dst_fail_closed():
    assert _question_clock(date="2026-09-19", time="14:30:23", latitude=28.6, longitude=77.2,
                           timezone="Asia/Kolkata").utc_datetime.isoformat() == "2026-09-19T09:00:23+00:00"
    for overrides in (dict(date="2026-02-30"), dict(time="25:00"), dict(latitude=float("nan")),
                      dict(timezone="fake"), dict(date="2026-03-08", time="02:30", timezone="America/New_York")):
        args = dict(date="2026-09-19", time="14:30:23", latitude=28.6, longitude=77.2, timezone="UTC")
        args.update(overrides)
        with pytest.raises(ValueError):
            _question_clock(**args)


def test_result_contract_rejects_old_yes_no_shape():
    with pytest.raises(RuntimeError, match="verdict.result"):
        _validate_analysis_contract({"verdict": {"answer": "yes"}, "presentation": {}, "question": {},
                                     "classical": {}, "calculation": {}})


def test_api_exposes_catalogue_and_accepts_question_id_directly():
    catalogue = asyncio.run(post_to_prashna("/prashna/analyze", {"question_id": "career_job_offer"}))
    assert catalogue.status_code == 422  # Clock and place inputs are still required.
    incomplete = asyncio.run(post_to_prashna("/prashna/analyze", {
        "date": "2026-09-19", "time": "14:30:23", "latitude": 28.4, "longitude": 77.0}))
    assert incomplete.status_code == 400
    with patch("prashna.service.ClassicalPrashnaChartCalculator") as calculator:
        calculator.return_value.calculate_chart.side_effect = fake_chart
        completed = asyncio.run(post_to_prashna("/prashna/analyze", request()))
    assert completed.status_code == 200
    assert completed.json()["clock"]["source"] == "guided_question_selection"
    assert completed.json()["billing"] == {
        "feature": "prashna", "credits_spent": 3, "credits_remaining": 97,
    }


def test_api_rejects_insufficient_credits_before_chart_calculation():
    with patch("prashna.service.ClassicalPrashnaChartCalculator") as calculator:
        response = asyncio.run(post_to_prashna("/prashna/analyze", request(), balance=2))
    assert response.status_code == 402
    assert "need 3 credits but have 2" in response.json()["detail"]
    calculator.return_value.calculate_chart.assert_not_called()


def test_api_rejects_old_kp_horary_number_field():
    # Pydantic currently ignores undeclared fields by default, so assert the public model itself has no KP field.
    from prashna.routes import AnalyzeRequest
    fields = AnalyzeRequest.model_fields
    assert "horary_number" not in fields


def test_legacy_category_request_gets_actionable_migration_error():
    payload = request(); payload.pop("question_id")
    payload.update(question="Will this relationship progress", category="relationship")
    response = asyncio.run(post_to_prashna("/prashna/analyze", payload))
    assert response.status_code == 409
    assert "older Prashna screen" in response.json()["detail"]
    assert "contact, unblock, reconciliation, return, or marriage" in response.json()["detail"]
