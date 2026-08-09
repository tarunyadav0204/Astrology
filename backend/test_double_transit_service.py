from datetime import datetime, timedelta, timezone

import pytest

from charts import double_transit_service as service


def _segment(sign, start, end):
    return {
        "sign": sign,
        "start": start,
        "end": end,
        "retrograde_at_midpoint": False,
    }


def _chart():
    names = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
    return {
        "ascendant": 12.0,
        "planets": {
            name: {"longitude": index * 30.0 + 15.0, "sign": index}
            for index, name in enumerate(names)
        },
    }


def test_strict_full_and_aspect_only_classification(monkeypatch):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2027, 1, 1, tzinfo=timezone.utc)

    def fake_segments(planet, _start, _end):
        # Aries ascendant: Jupiter occupies H1; Saturn occupies H7.
        return [_segment(0 if planet == "Jupiter" else 6, start, end)]

    monkeypatch.setattr(service, "_segments", fake_segments)
    result = service.calculate_double_transits(
        _chart(),
        start,
        end,
    )

    by_house = {row["house"]: row for row in result["windows"]}
    assert by_house[1]["status"] == "full"
    assert by_house[1]["jupiter"]["mode"] == "occupies"
    assert by_house[7]["status"] == "full"
    assert by_house[7]["saturn"]["mode"] == "occupies"
    assert by_house[9]["status"] == "aspect_only"
    assert result["method"]["fallbacks_used"] is False


def test_can_exclude_aspect_only(monkeypatch):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2027, 1, 1, tzinfo=timezone.utc)
    monkeypatch.setattr(
        service,
        "_segments",
        lambda planet, _start, _end: [_segment(0 if planet == "Jupiter" else 6, start, end)],
    )
    result = service.calculate_double_transits(
        _chart(),
        start,
        end,
        include_aspect_only=False,
    )
    assert {row["house"] for row in result["windows"]} == {1, 7}


def test_missing_ascendant_is_rejected_without_fallback():
    with pytest.raises(service.DoubleTransitInputError, match="ascendant"):
        service.calculate_double_transits(
            {"planets": _chart()["planets"]},
            datetime(2026, 1, 1),
            datetime(2027, 1, 1),
        )


def test_conflicting_natal_sign_is_rejected(monkeypatch):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2027, 1, 1, tzinfo=timezone.utc)
    monkeypatch.setattr(
        service,
        "_segments",
        lambda planet, _start, _end: [_segment(0 if planet == "Jupiter" else 6, start, end)],
    )
    with pytest.raises(service.DoubleTransitInputError, match="Conflicting natal sign"):
        chart = _chart()
        chart["planets"]["Sun"]["sign"] = 4
        service.calculate_double_transits(chart, start, end)


def test_incomplete_natal_planets_are_rejected_without_fallback():
    chart = _chart()
    del chart["planets"]["Saturn"]
    with pytest.raises(service.DoubleTransitInputError, match="Saturn"):
        service.calculate_double_transits(
            chart,
            datetime(2026, 1, 1),
            datetime(2027, 1, 1),
        )


def test_optimized_ingress_scan_matches_daily_swiss_file_reference():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2028, 1, 1, tzinfo=timezone.utc)

    def daily_reference(planet):
        cursor = segment_start = start
        old_sign = service._sign(start, planet)
        rows = []
        while cursor < end:
            nxt = min(cursor + timedelta(days=1), end)
            new_sign = service._sign(nxt, planet)
            if new_sign != old_sign:
                boundary = service._refine_boundary(cursor, nxt, planet, old_sign)
                rows.append((segment_start, boundary, old_sign))
                segment_start, old_sign = boundary, new_sign
            cursor = nxt
        rows.append((segment_start, end, old_sign))
        return rows

    for planet in ("Jupiter", "Saturn"):
        optimized = [
            (row["start"], row["end"], row["sign"])
            for row in service._segments(planet, start, end)
        ]
        assert optimized == daily_reference(planet)
