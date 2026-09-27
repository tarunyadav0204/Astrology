from __future__ import annotations

import asyncio

import httpx
from fastapi import FastAPI
from ai.education_ai_context_generator import EducationAIContextGenerator
from ai.health_ai_context_generator import HealthAIContextGenerator
from calculators.classical_functional_nature import calculate_functional_nature
from calculators.color_calculator import ColorCalculator
from calculators.divisional_chart_calculator import DivisionalChartCalculator
from calculators.planet_analyzer import PlanetAnalyzer
from calculators.planetary_dignities_calculator import (
    PlanetaryDignitiesCalculator,
    attach_canonical_position_states,
)
from chat.instant_chat_pipeline import _enrich_calculated_chart_for_prediction
from health_v2.constitutional_strength_engine import ConstitutionalStrengthEngine
from planetary_dignities import calculate_planetary_dignities, router as planetary_dignities_router
from vedic_predictions.engines.context_analyzer import ContextAnalyzer


PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")


def _cancer_chart() -> dict:
    longitudes = {
        "Sun": 10.0, "Moon": 100.0, "Mars": 70.0, "Mercury": 130.0,
        "Jupiter": 160.0, "Venus": 190.0, "Saturn": 220.0,
        "Rahu": 250.0, "Ketu": 70.0,
    }
    chart = {
        "ascendant": 95.0,
        "houses": [{"house": h, "sign": (3 + h - 1) % 12} for h in range(1, 13)],
        "planets": {},
    }
    for planet in PLANETS:
        longitude = longitudes[planet]
        sign = int(longitude / 30) % 12
        chart["planets"][planet] = {
            "longitude": longitude,
            "sign": sign,
            "degree": longitude % 30,
            "house": ((sign - 3) % 12) + 1,
            "retrograde": False,
        }
    return chart


def test_dignity_api_and_calculator_keep_legacy_fields_and_add_evidence():
    chart = _cancer_chart()
    direct = PlanetaryDignitiesCalculator(chart).calculate_planetary_dignities()
    response = asyncio.run(calculate_planetary_dignities({"chart_data": chart}))
    assert {"dignities", "positions", "ascendant_sign", "summary"} <= set(response)
    assert response["positions"]["schema_version"] == "canonical-positions/2.0.0"
    for planet, row in direct.items():
        assert {"dignity", "functional_nature", "strength_multiplier", "states"} <= set(row)
        assert row["functional_nature"] == response["dignities"][planet]["functional_nature"]
        assert "functional_nature_details" in row
        assert "natural_nature_details" in row

    app = FastAPI()
    app.include_router(planetary_dignities_router, prefix="/api")
    async def transport_request():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.post("/api/planetary-dignities", json={"chart_data": chart})

    transported = asyncio.run(transport_request())
    assert transported.status_code == 200
    assert transported.json()["dignities"]["Moon"]["natural_nature"] == "benefic"
    assert transported.json()["positions"]["planets"][1]["nakshatra"] == "Pushya"


def test_positions_contract_is_the_single_source_for_mobile_tables_and_chart_badges():
    displayed = _cancer_chart()
    # Display Mercury at 18° Virgo: degree-bounded Moolatrikona. Conditions
    # deliberately come from another chart to exercise the selected-chart vs
    # natal/transit distinction used by the mobile screen.
    displayed["planets"]["Mercury"].update({
        "longitude": 168.0, "sign": 5, "degree": 18.0, "house": 3,
    })
    condition = _cancer_chart()
    condition["planets"]["Sun"].update({"longitude": 160.0, "sign": 5, "degree": 10.0})
    condition["planets"]["Mercury"].update({
        "longitude": 168.0, "sign": 5, "degree": 18.0,
        "neecha_bhanga": True,
    })

    calculator = PlanetaryDignitiesCalculator(displayed)
    dignities = calculator.calculate_planetary_dignities()
    positions = calculator.calculate_position_tables(condition, dignities=dignities)
    mercury = next(row for row in positions["planets"] if row["name"] == "Mercury")

    assert mercury["dignity"]["key"] == "mt"
    assert mercury["nakshatra"] == "Hasta"
    assert mercury["pada"] == 3
    assert mercury["sign_lord"] == "Mercury"
    assert mercury["sign_lord_relationship"]["key"] == "self"
    assert mercury["nakshatra_lord"] == "Moon"
    assert mercury["nakshatra_lord_relationship"]["key"] == "enemy"
    assert mercury["combust"] is True
    assert mercury["combustion"]["angular_distance"] == 8.0
    assert mercury["neecha_bhanga"] is True
    assert mercury["degree_dms"]["text"] == "18°00'00.00\""
    assert mercury["rashi_house"] == 3
    # A planet occupying its own sign is reported as self; temporary and
    # compound friendship are not manufactured against the same planet.
    assert mercury["friendships"]["sign_lord"]["compound"]["key"] == "self"
    assert mercury["friendships"]["sign_lord"]["temporary"] is None
    assert mercury["dispositors"]["sign"]["planet"] == "Mercury"
    assert mercury["baladi_avastha"]["key"] == "kumara"
    assert mercury["boundary_proximity"]["rashi_degrees"] == 12.0
    assert mercury["navatara"]["key"] == "sadhaka"
    assert mercury["aspects"]["method"].startswith("Parashari")
    assert mercury["motion"]["key"] == "direct"
    assert len(positions["houses"]) == 12
    assert any(
        person["name"] == "Mercury"
        for row in positions["nakshatras"]
        if row["nakshatra"] == "Hasta"
        for person in row["people"]
    )

    attach_canonical_position_states(displayed)
    assert displayed["canonical_positions_version"] == "canonical-positions/2.0.0"
    assert displayed["planets"]["Mercury"]["dignity"] == "moolatrikona"
    assert displayed["planets"]["Mercury"]["nakshatra"] == "Hasta"
    assert isinstance(displayed["planets"]["Mercury"]["vargottama"], bool)


def test_positions_professional_strength_is_backend_calculated_when_birth_data_is_supplied():
    chart = _cancer_chart()
    birth_data = {
        "name": "Contract test", "date": "1990-01-01", "time": "12:00:00",
        "latitude": 28.6139, "longitude": 77.209, "timezone": "Asia/Kolkata",
    }
    response = asyncio.run(calculate_planetary_dignities({
        "chart_data": chart, "birth_data": birth_data,
    }))
    sun = next(row for row in response["positions"]["planets"] if row["name"] == "Sun")
    assert response["positions"]["shadbala_status"] == {"status": "calculated"}
    assert sun["shadbala"]["total_rupas"] > 0
    assert sun["ishta_kashta"]["ishta_phala"] is not None
    assert 0 <= sun["varga_strength"]["vimshopaka_bala"]["score"] <= 20
    assert sun["varga_strength"]["vimshopaka_bala"]["scheme"] == "shodashavarga"
    assert sun["dispositors"]["sign"]["shadbala"]["required_percent"] > 0
    assert isinstance(sun["dispositors"]["sign"]["aspects_received"], list)


def test_planet_analyzer_chat_and_health_share_the_canonical_value():
    chart = _cancer_chart()
    expected = calculate_functional_nature(3, "Mars")
    analyzer = PlanetAnalyzer(chart, compute_shadbala=False)
    assert analyzer.analyze_planet("Mars")["dignity_analysis"]["functional_nature"] == expected["functional_nature"]

    enriched = _enrich_calculated_chart_for_prediction("D1", {**chart, "ascendant_sign": 3})
    assert enriched["planets"]["Mars"]["functional_nature"] == "functional_benefic"
    assert enriched["planets"]["Mars"]["functional_nature_details"] == expected

    health = ConstitutionalStrengthEngine(chart).calculate()
    role = health["planet_conditions"]["Mars"]["functional_role"]
    assert role["is_yogakaraka"] is True
    assert role["classical_functional_nature"] == expected


def test_ai_context_and_vedic_context_clients_use_corrected_compatibility_lists():
    chart = _cancer_chart()
    health = HealthAIContextGenerator.__new__(HealthAIContextGenerator)._analyze_functional_nature(chart, 3)
    education = EducationAIContextGenerator.__new__(EducationAIContextGenerator)._analyze_functional_nature(chart, 3)
    assert {row["planet"] for row in health["functional_benefics"]} == {"Moon", "Mars", "Jupiter"}
    assert {row["planet"] for row in education["functional_benefics"]} == {"Moon", "Mars", "Jupiter"}
    assert ContextAnalyzer()._get_functional_nature("Saturn", chart) == "neutral"
    assert ContextAnalyzer()._get_functional_nature("Venus", chart) == "malefic"


def test_color_and_divisional_clients_do_not_recreate_yogakaraka_shortcuts():
    chart = _cancer_chart()
    colors = ColorCalculator(chart).calculate(current_md="Saturn")
    assert colors["planet_scores"]["Mars"]["yogakaraka"] is True
    assert colors["planet_scores"]["Mars"]["functional_nature_details"]["functional_nature"] == "benefic"
    assert colors["planet_scores"]["Saturn"]["functional_nature"] == "neutral"

    division = DivisionalChartCalculator(chart).calculate_divisional_chart(9)["divisional_chart"]
    division_asc = int(float(division["ascendant"]) / 30.0) % 12
    for planet in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        assert division["planets"][planet]["functional_nature"] == calculate_functional_nature(
            division_asc, planet
        )["functional_nature"]
