"""
Regression checks for Hindu festival dating vs published 2026 Delhi (Drik-style) dates.

We use Purnimanta labels and Udaya Tithi, with classical windows for
Diwali (Pradosh), Maha Shivaratri / Janmashtami (Nishita), Ram Navami (Madhyahna),
and Vijayadashami (Aparahna).
"""
import pytest

from festivals.festival_calculator import FestivalCalculator

DELHI = {"lat": 28.6139, "lon": 77.2090, "tz": "Asia/Kolkata"}


@pytest.fixture(scope="module")
def calc():
    return FestivalCalculator()


@pytest.fixture(scope="module")
def festivals_2026(calc):
    return calc.find_festival_dates(
        2026, None, DELHI["lat"], DELHI["lon"], "purnimanta", DELHI["tz"]
    )


def _dates_for(festivals, festival_id):
    return [f["date"] for f in festivals if f["id"] == festival_id]


@pytest.mark.parametrize(
    "festival_id,expected",
    [
        ("vasant_panchami", "2026-01-23"),
        ("maha_shivratri", "2026-02-15"),
        ("holika_dahan", "2026-03-03"),
        ("holi", "2026-03-04"),
        ("gudi_padwa", "2026-03-19"),
        ("chaitra_navratri", "2026-03-19"),
        ("ram_navami", "2026-03-26"),
        ("akshaya_tritiya", "2026-04-19"),
        ("janmashtami", "2026-09-04"),
        ("ganesh_chaturthi", "2026-09-14"),
        ("radha_ashtami", "2026-09-19"),
        ("anant_chaturdashi", "2026-09-25"),
        ("navratri", "2026-10-11"),
        ("dussehra", "2026-10-20"),
        ("sarva_pitru_amavasya", "2026-10-10"),
        ("karva_chauth", "2026-10-29"),
        ("dhanteras", "2026-11-06"),
        ("diwali", "2026-11-08"),
        ("govardhan_puja", "2026-11-10"),
        ("bhai_dooj", "2026-11-11"),
        ("devutthana_ekadashi", "2026-11-20"),
    ],
)
def test_drik_aligned_2026_delhi_dates(festivals_2026, festival_id, expected):
    dates = _dates_for(festivals_2026, festival_id)
    assert dates == [expected], f"{festival_id}: got {dates}, expected [{expected}]"


def test_no_duplicate_paksha_false_positives(festivals_2026):
    """Major festivals must not fire once per paksha (old lunar_day-only bug)."""
    for festival_id in ("holi", "navratri", "karva_chauth", "diwali", "gudi_padwa"):
        dates = _dates_for(festivals_2026, festival_id)
        assert len(dates) == 1, f"{festival_id} duplicated: {dates}"


def test_pitra_paksha_covers_ashwin_krishna(festivals_2026):
    dates = _dates_for(festivals_2026, "pitra_paksha")
    assert dates[0] == "2026-09-27"
    assert dates[-1] == "2026-10-10"
    assert "2026-10-10" in _dates_for(festivals_2026, "sarva_pitru_amavasya")


def test_sharad_purnima_handles_short_tithi(festivals_2026):
    dates = _dates_for(festivals_2026, "sharad_purnima")
    assert dates == ["2026-10-25"]


def test_named_ekadashi_labels(calc):
    vrats = calc.get_monthly_vrats(2026, 5, DELHI["lat"], DELHI["lon"], "purnimanta", DELHI["tz"])
    names = {v["date"]: v["name"] for v in vrats if "Ekadashi" in v["name"]}
    assert any(name == "Nirjala Ekadashi" for name in names.values())


def test_month_aliases_vaishakha(calc):
    assert calc.normalize_month("vaishakha") == "vaisakha"
    assert calc.normalize_month("adhika_jyeshtha").startswith("adhika_")


def test_adhika_detected_in_mid_2026(calc):
    assert calc.is_adhika_month(2026, 5) or calc.is_adhika_month(2026, 6)
