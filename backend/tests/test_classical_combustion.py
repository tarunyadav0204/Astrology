from calculators.classical_combustion import (
    CLASSICAL_COMBUSTION_LIMITS,
    angular_distance,
    attach_classical_combustion,
    calculate_chart_combustion,
    calculate_planet_combustion,
)
from calculators.planetary_dignities_calculator import PlanetaryDignitiesCalculator
from calculators.planet_analyzer import PlanetAnalyzer
from health_v2.constitutional_strength_engine import _combustion as health_combustion


def planet(longitude, *, retrograde=False):
    return {
        "longitude": float(longitude),
        "sign": int(float(longitude) / 30) % 12,
        "degree": float(longitude) % 30,
        "house": 1,
        "retrograde": retrograde,
    }


def test_shortest_distance_wraps_across_zero():
    assert angular_distance(359, 1) == 2
    assert angular_distance(10, 190) == 180


def test_every_direct_limit_and_boundary_is_applied():
    sun = planet(100)
    for name, limits in CLASSICAL_COMBUSTION_LIMITS.items():
        boundary = calculate_planet_combustion(name, planet(100 + limits["direct"]), sun)
        outside = calculate_planet_combustion(name, planet(100 + limits["direct"] + 0.001), sun)
        assert boundary["is_combust"] is True, name
        assert boundary["threshold"] == limits["direct"]
        assert outside["is_combust"] is False, name


def test_retrograde_limits_cover_all_variants_in_selected_table():
    sun = planet(100)
    expected = {"Mars": 8, "Mercury": 12, "Jupiter": 11, "Venus": 8, "Saturn": 16}
    for name, threshold in expected.items():
        row = calculate_planet_combustion(name, planet(100 + threshold, retrograde=True), sun)
        assert row["motion"] == "retrograde"
        assert row["threshold"] == threshold
        assert row["is_combust"] is True
    assert calculate_planet_combustion("Mars", planet(109, retrograde=True), sun)["is_combust"] is False
    assert calculate_planet_combustion("Mercury", planet(113, retrograde=True), sun)["is_combust"] is False
    assert calculate_planet_combustion("Venus", planet(109, retrograde=True), sun)["is_combust"] is False


def test_sun_nodes_and_mathematical_points_are_not_applicable():
    sun = planet(100)
    for name in ("Sun", "Rahu", "Ketu", "Gulika", "Mandi", "InduLagna"):
        row = calculate_planet_combustion(name, planet(100.1), sun)
        assert row["applicable"] is False
        assert row["is_combust"] is False
        assert row["threshold"] is None


def test_exact_solar_contact_remains_combust_and_never_becomes_cazimi():
    row = calculate_planet_combustion("Mercury", planet(100.1), planet(100))
    assert row["status"] == "combust"
    assert "cazimi" not in row.values()


def test_additive_chart_contract_preserves_legacy_status_fields():
    chart = {
        "ascendant": 0,
        "planets": {
            "Sun": planet(100),
            "Mercury": planet(111, retrograde=True),
            "Saturn": planet(115.5),
            "Rahu": planet(100),
        },
    }
    attach_classical_combustion(chart)
    assert chart["combustion"]["planets"]["Mercury"]["threshold"] == 12
    assert chart["planets"]["Mercury"]["combustion_status"] == "combust"
    assert chart["planets"]["Mercury"]["combust"] is True
    assert chart["planets"]["Saturn"]["combust"] is True
    assert chart["planets"]["Rahu"]["combust"] is False


def test_dignity_health_and_chart_consumers_share_identical_result():
    chart = {
        "ascendant": 0,
        "planets": {
            "Sun": planet(100),
            "Mars": planet(109, retrograde=True),
            "Mercury": planet(111, retrograde=True),
        },
    }
    canonical = calculate_chart_combustion(chart)["planets"]
    dignity = PlanetaryDignitiesCalculator(chart).calculate_planetary_dignities()
    for name in ("Mars", "Mercury"):
        health = health_combustion(chart, name)
        assert dignity[name]["combustion"] == canonical[name]
        assert dignity[name]["combustion_status"] == canonical[name]["status"]
        assert health["is_combust"] == canonical[name]["is_combust"]
        assert health["threshold"] == canonical[name]["threshold"]


def test_planet_analyzer_exposes_canonical_evidence_for_chat_and_reports():
    chart = {
        "ascendant": 0,
        "planets": {
            "Sun": planet(100),
            "Moon": planet(160),
            "Mars": planet(210),
            "Mercury": planet(111, retrograde=True),
            "Jupiter": planet(240),
            "Venus": planet(270),
            "Saturn": planet(300),
            "Rahu": planet(20),
            "Ketu": planet(200),
        },
    }
    row = PlanetAnalyzer(chart, compute_shadbala=False).analyze_planet("Mercury")[
        "combustion_status"
    ]
    assert row["is_combust"] is True
    assert row["is_cazimi"] is False
    assert row["angular_distance"] == 11
    assert row["threshold"] == 12
    assert row["motion"] == "retrograde"
    assert row["source"]["work"] == "Brihat Parashara Hora Shastra"
