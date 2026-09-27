from __future__ import annotations

from datetime import datetime

from calculators.annual_nakshatra_calculator import AnnualNakshatraCalculator


# Drik Panchang's published Revati periods for New Delhi, 2026.  These are
# geocentric Moon crossings shown in IST; location changes the displayed time
# zone, not the UTC instant of the Nakshatra boundary.
DRIK_REVATI_2026_DELHI = (
    ("2026-01-24 14:16", "2026-01-25 13:35"),
    ("2026-02-20 20:07", "2026-02-21 19:07"),
    ("2026-03-20 04:05", "2026-03-21 02:27"),
    ("2026-04-16 13:59", "2026-04-17 12:02"),
    ("2026-05-14 00:17", "2026-05-14 22:34"),
    ("2026-06-10 09:21", "2026-06-11 08:16"),
    ("2026-07-07 16:24", "2026-07-08 16:00"),
    ("2026-08-03 22:00", "2026-08-04 21:54"),
    ("2026-08-31 03:44", "2026-09-01 03:23"),
    ("2026-09-27 11:08", "2026-09-28 10:16"),
    ("2026-10-24 20:32", "2026-10-25 19:22"),
    ("2026-11-21 06:50", "2026-11-22 05:54"),
    ("2026-12-18 16:10", "2026-12-19 15:58"),
)


def _minute_delta(actual: datetime, expected: str) -> float:
    return abs((actual - datetime.strptime(expected, "%Y-%m-%d %H:%M")).total_seconds()) / 60.0


def test_revati_2026_matches_drik_panchang_to_displayed_minute() -> None:
    periods = AnnualNakshatraCalculator().calculate_annual_nakshatra_periods(
        "Revati", 2026, 28.6139, 77.2090,
    )["periods"]

    assert len(periods) == len(DRIK_REVATI_2026_DELHI)
    for period, (expected_start, expected_end) in zip(periods, DRIK_REVATI_2026_DELHI):
        # Drik publishes whole minutes; allow the normal half-minute rounding
        # interval plus one displayed-minute difference at a few boundaries.
        assert _minute_delta(period["start_datetime"], expected_start) <= 1.5
        assert _minute_delta(period["end_datetime"], expected_end) <= 1.5


def test_screenshot_revati_boundaries_are_exact_to_displayed_minute() -> None:
    periods = AnnualNakshatraCalculator().calculate_annual_nakshatra_periods(
        "Revati", 2026, 28.6139, 77.2090,
    )["periods"]
    september = periods[9]
    october = periods[10]

    assert september["start_time"] == "11:08 AM"
    assert september["end_time"] == "10:16 AM"
    assert october["start_time"] == "08:32 PM"
    assert october["end_time"] == "07:22 PM"


def test_year_calendar_continuous_path_matches_screenshot() -> None:
    rows = AnnualNakshatraCalculator().calculate_annual_nakshatra_periods_all_continuous(
        2026, 28.6139, 77.2090,
    )
    revati = {
        row["start_datetime"].month: row
        for row in rows
        if row["nakshatra"] == "Revati" and row["start_datetime"].month in (9, 10)
    }

    assert revati[9]["start_time"] == "11:08 AM"
    assert revati[9]["end_time"] == "10:16 AM"
    assert revati[10]["start_time"] == "08:32 PM"
    assert revati[10]["end_time"] == "07:22 PM"
