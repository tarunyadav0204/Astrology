"""Tests for canonical graha drishti (avoid importing calculators package __init__)."""

import importlib.util
from pathlib import Path

import pytest

_BACKEND = Path(__file__).resolve().parent.parent
_VEDIC_PATH = _BACKEND / "calculators" / "vedic_graha_drishti.py"


def _load_vedic():
    spec = importlib.util.spec_from_file_location("vedic_graha_drishti", _VEDIC_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def vedic():
    return _load_vedic()


def _minimal_chart():
    """Whole-sign: Asc Cancer (3). House 1 sign=3, H2=4, ..."""
    asc_sign = 3
    houses = []
    for i in range(12):
        house_sign = (asc_sign + i) % 12
        houses.append({"sign": house_sign, "longitude": house_sign * 30.0})
    planets = {
        "Sun": {"sign": 3, "longitude": 95.0},
        "Moon": {"sign": 5, "longitude": 125.0},
        "Mars": {"sign": 8, "longitude": 245.0},
        "Mercury": {"sign": 4, "longitude": 110.0},
        "Jupiter": {"sign": 9, "longitude": 275.0},
        "Venus": {"sign": 7, "longitude": 215.0},
        "Saturn": {"sign": 10, "longitude": 305.0},
        "Rahu": {"sign": 0, "longitude": 15.0},
        "Ketu": {"sign": 6, "longitude": 195.0},
    }
    return {"houses": houses, "planets": planets, "ascendant": asc_sign * 30.0 + 5.0}


def test_planets_aspecting_excludes_occupants(vedic):
    chart = _minimal_chart()
    t = chart["houses"][0]["sign"]
    names = vedic.planets_aspecting_house_sign(chart["planets"], t)
    assert "Sun" not in names


def test_mars_special_aspects(vedic):
    chart = _minimal_chart()
    target = 11
    names = vedic.planets_aspecting_house_sign(chart["planets"], target)
    assert "Mars" in names


def test_attach_adds_keys(vedic):
    chart = _minimal_chart()
    vedic.attach_graha_drishti_to_chart(chart)
    assert "graha_drishti_by_house" in chart
    assert "1" in chart["graha_drishti_by_house"]
    assert isinstance(chart["houses"][0].get("graha_drishti"), list)


def test_compute_has_aspect_labels(vedic):
    chart = _minimal_chart()
    by_h = vedic.compute_graha_drishti_by_house(chart)
    assert 1 in by_h
    for row in by_h[1]:
        assert "planet" in row
        assert "aspect_labels" in row
        assert isinstance(row["aspect_labels"], str)


def test_rahu_fifth_aspect(vedic):
    houses = [{"sign": i, "longitude": i * 30.0} for i in range(12)]
    planets = {"Rahu": {"sign": 0}}
    chart = {"houses": houses, "planets": planets}
    names = vedic.planets_aspecting_house_sign(planets, 4)
    assert "Rahu" in names
