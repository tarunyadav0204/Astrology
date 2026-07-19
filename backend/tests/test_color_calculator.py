"""Unit tests for chart-based ColorCalculator."""

from calculators.color_calculator import ColorCalculator
from calculators.remedy_engine import RemedyEngine


def _minimal_chart(asc_sign: int, planet_signs: dict | None = None) -> dict:
    """Build a chart dict with ascendant + planet signs for dignity checks."""
    signs = planet_signs or {}
    planets = {}
    for name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
        sign = signs.get(name, (asc_sign + 3) % 12)  # default neutral-ish placement
        planets[name] = {"sign": sign, "longitude": sign * 30 + 10.0}
    return {
        "ascendant": {"sign": asc_sign, "longitude": asc_sign * 30 + 5.0},
        "planets": planets,
    }


def _phrase_set(blob: str) -> set[str]:
    return {p.strip().lower() for p in (blob or "").split(",") if p.strip()}


def test_cancer_saturn_md_puts_saturn_colors_in_avoid_not_favor():
    """Cancer lagna: Saturn is functional malefic — MD must not favor blue/grey/black."""
    chart = _minimal_chart(3)  # Cancer
    result = ColorCalculator(chart).calculate(current_md="Saturn", current_ad="Moon")

    saturn_colors = _phrase_set(RemedyEngine.COLORS["Saturn"])
    favor = _phrase_set(result["wear_colors"])
    avoid = _phrase_set(result["avoid_colors"])

    assert result["planet_scores"]["Saturn"]["score"] < 0
    assert saturn_colors & avoid
    assert not (saturn_colors & favor)
    assert "blue" in avoid


def test_cancer_mars_yogakaraka_colors_in_favor():
    """Cancer lagna: Mars is yogakaraka — red / deep orange should favor."""
    chart = _minimal_chart(3)
    result = ColorCalculator(chart).calculate(current_md="Moon", current_ad="Mars")

    assert result["planet_scores"]["Mars"]["yogakaraka"] is True
    assert result["planet_scores"]["Mars"]["score"] > 0
    favor = _phrase_set(result["wear_colors"])
    assert "red" in favor or "deep orange" in favor


def test_leo_mars_yogakaraka_favor():
    """Leo: Mars rules Scorpio (4) and Aries (9) → yogakaraka colors favor."""
    chart = _minimal_chart(4)  # Leo
    result = ColorCalculator(chart).calculate(current_md="Sun", current_ad="Mars")
    assert result["planet_scores"]["Mars"]["yogakaraka"] is True
    favor = _phrase_set(result["wear_colors"])
    assert favor & {"red", "deep orange"}


def test_no_color_phrase_in_both_favor_and_avoid():
    for asc in range(12):
        chart = _minimal_chart(asc)
        result = ColorCalculator(chart).calculate(current_md="Saturn", current_ad="Rahu")
        favor = _phrase_set(result["wear_colors"])
        avoid = _phrase_set(result["avoid_colors"])
        assert favor.isdisjoint(avoid), f"overlap for asc={asc}: {favor & avoid}"


def test_dasha_does_not_flip_malefic_into_favor():
    """Negative chart score stays negative even when planet is current MD."""
    chart = _minimal_chart(3)  # Cancer — Saturn malefic
    base = ColorCalculator(chart).calculate(current_md=None, current_ad=None)
    with_md = ColorCalculator(chart).calculate(current_md="Saturn", current_ad=None)
    assert base["planet_scores"]["Saturn"]["score"] < 0
    assert with_md["planet_scores"]["Saturn"]["score"] < base["planet_scores"]["Saturn"]["score"]
    favor = _phrase_set(with_md["wear_colors"])
    assert "blue" not in favor
