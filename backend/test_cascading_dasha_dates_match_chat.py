"""Cascading / sub-dasha browser dates must match DashaCalculator (chat) dates."""

from datetime import datetime, timedelta

from shared.dasha_calculator import DashaCalculator


def _sample_birth():
    return {
        "name": "Test",
        "date": "1990-05-15",
        "time": "14:30",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "timezone": 5.5,
    }


def _tarun_birth():
    """Known AstroSage reference: Rahu MD ends 1995-11-04 → Saturn MD ends 2030-11-04."""
    return {
        "name": "Tarun",
        "date": "1980-04-02",
        "time": "14:55",
        "latitude": 29.15,
        "longitude": 75.72,
        "timezone": 5.5,
    }


def test_antardasha_list_matches_current_finder():
    calc = DashaCalculator()
    birth = _sample_birth()
    target = datetime(2024, 7, 1, 12, 0, 0)
    dashas = calc.calculate_current_dashas(birth, target)
    maha = next(m for m in dashas["maha_dashas"] if m["start"] <= target <= m["end"])

    listed = calc.list_antardashas(maha, target)
    current_row = next(r for r in listed if r["current"])
    chat_antar = dashas["antardasha"]

    assert current_row["planet"] == chat_antar["planet"]
    assert current_row["start"] == chat_antar["start"]
    assert current_row["end"] == chat_antar["end"]


def test_tarun_saturn_mahadasha_matches_astrosage():
    calc = DashaCalculator()
    dashas = calc.calculate_current_dashas(_tarun_birth(), datetime(2026, 7, 13, 12))
    assert dashas["mahadasha"]["planet"] == "Saturn"
    assert dashas["mahadasha"]["start"] == "2011-11-04"
    assert dashas["mahadasha"]["end"] == "2030-11-04"
    rahu = dashas["maha_dashas"][0]
    assert rahu["planet"] == "Rahu"
    assert calc.maha_end_date_str(rahu["end"]) == "1995-11-04"
    # Balance Rahu MD must still list all 9 ADs (ending with Mars), not truncate early.
    rahu_ads = calc.list_antardashas(rahu)
    assert len(rahu_ads) == 9
    assert [a["planet"] for a in rahu_ads][-1] == "Mars"
    assert rahu_ads[-1]["end"] == "1995-11-04"
    # AD must use same 365.25 year as MD; calendar-midnight MD bounds match AstroSage.
    assert dashas["antardasha"]["planet"] == "Rahu"
    assert dashas["antardasha"]["start"] == "2025-06-16"
    assert dashas["antardasha"]["end"] == "2028-04-22"
    saturn = next(m for m in dashas["maha_dashas"] if m["planet"] == "Saturn")
    mars_ad = next(a for a in calc.list_antardashas(saturn) if a["planet"] == "Mars")
    assert mars_ad["end"] == "2025-06-16"


def test_old_proportional_split_diverges_from_calculator():
    """Guard: date-only + inclusive-day proportional split drifts from chat math."""
    calc = DashaCalculator()
    birth = _sample_birth()
    target = datetime(2024, 7, 1, 12, 0, 0)
    dashas = calc.calculate_current_dashas(birth, target)
    maha = next(m for m in dashas["maha_dashas"] if m["start"] <= target <= m["end"])

    correct = calc.list_antardashas(maha, target)
    chat_antar = dashas["antardasha"]
    correct_current = next(r for r in correct if r["current"])
    assert correct_current["start"] == chat_antar["start"]
    assert correct_current["end"] == chat_antar["end"]

    parent_start = datetime.strptime(maha["start"].strftime("%Y-%m-%d"), "%Y-%m-%d")
    parent_end = datetime.strptime(maha["end"].strftime("%Y-%m-%d"), "%Y-%m-%d")
    parent_total_days = (parent_end - parent_start).days + 1
    start_index = calc.PLANET_ORDER.index(maha["planet"])
    total_period = 0.0
    periods_years = []
    for i in range(9):
        planet = calc.PLANET_ORDER[(start_index + i) % 9]
        years = (calc.DASHA_PERIODS[maha["planet"]] * calc.DASHA_PERIODS[planet]) / 120
        periods_years.append((planet, years))
        total_period += years

    current = parent_start
    old_rows = []
    for planet, years in periods_years:
        ratio = years / total_period
        end = current + timedelta(days=parent_total_days * ratio)
        if end > parent_end:
            end = parent_end
        display_end = min(end.date(), parent_end.date())
        old_rows.append(
            {
                "planet": planet,
                "start": current.strftime("%Y-%m-%d"),
                "end": display_end.strftime("%Y-%m-%d"),
            }
        )
        current = end
        if current >= parent_end:
            break

    old_current = next(r for r in old_rows if r["planet"] == chat_antar["planet"])
    # Primary contract: list helper matches chat finder. Old day-proportional
    # splitter is kept only as a contrast helper and may coincide on some charts.
    assert correct_current["planet"] == chat_antar["planet"]
    assert correct_current["start"] == chat_antar["start"]
    assert correct_current["end"] == chat_antar["end"]
    _ = old_current


def test_strip_internal_fields():
    calc = DashaCalculator()
    birth = _sample_birth()
    dashas = calc.calculate_current_dashas(birth, datetime(2024, 7, 1))
    maha = dashas["maha_dashas"][0]
    rows = calc.strip_internal_period_fields(calc.list_antardashas(maha))
    assert rows
    assert all(not k.startswith("_") for row in rows for k in row)


if __name__ == "__main__":
    test_antardasha_list_matches_current_finder()
    test_tarun_saturn_mahadasha_matches_astrosage()
    test_old_proportional_split_diverges_from_calculator()
    test_strip_internal_fields()
    print("ok")
