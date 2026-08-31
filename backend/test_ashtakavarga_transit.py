from types import SimpleNamespace

from calculators.ashtakavarga_transit import AshtakavargaTransitCalculator


def _published_chart_fixture():
    """Parashara's Light Sample Report 5 natal positions."""
    birth = SimpleNamespace(
        name="Transit Contract",
        date="2000-11-11",
        time="09:01",
        latitude=28.6139,
        longitude=77.2090,
        place="Delhi",
        timezone=5.5,
    )
    positions = {
        "Sun": (6, 205 + 11 / 60),
        "Moon": (0, 15 + 32 / 60),
        "Mars": (5, 160 + 28 / 60),
        "Mercury": (6, 186 + 53 / 60),
        "Jupiter": (1, 44 + 31 / 60),
        "Venus": (8, 243 + 47 / 60),
        "Saturn": (1, 34 + 18 / 60),
    }
    chart = {
        "ascendant": 210 + 24 + 25 / 60,
        "planets": {
            planet: {"sign": sign, "longitude": longitude}
            for planet, (sign, longitude) in positions.items()
        },
    }
    return birth, chart


def test_classical_transit_uses_fixed_natal_bav_sav_and_prastara():
    birth, chart = _published_chart_fixture()
    calc = AshtakavargaTransitCalculator(birth, chart)
    result = calc.calculate_classical_transit_analysis("2026-08-31", window_days=2)
    natal_sav = calc.calculate_sarvashtakavarga()["sarvashtakavarga"]

    assert result["schema_version"] == "ashtakavarga.transit.v2"
    assert result["basis"] == "fixed_natal_bav_sav_prastara"
    assert result["natal_sav"] == natal_sav
    assert sum(result["natal_sav"].values()) == 337
    assert len(result["planet_transits"]) == 7
    assert "probability" not in result
    assert "transit_sav" not in result

    for row in result["planet_transits"]:
        sign = row["sign_id"]
        bav = calc.calculate_individual_ashtakavarga(row["planet"])["bindus"]
        prastara = calc.calculate_prastara_ashtakavarga(row["planet"])
        ruler = row["kakshya"]["kakshya_ruler"]
        assert row["natal_bav_bindus"] == bav[sign]
        assert row["natal_sav_bindus"] == natal_sav[str(sign)]
        assert row["kakshya"]["bindu"] == prastara["matrix"][ruler][str(sign)]
        assert row["kakshya"]["active"] is bool(row["kakshya"]["bindu"])


def test_transit_calendar_is_ordered_and_contains_auditable_boundary_evidence():
    birth, chart = _published_chart_fixture()
    calc = AshtakavargaTransitCalculator(birth, chart)
    result = calc.calculate_classical_transit_analysis("2026-08-31", window_days=2)
    events = result["calendar_window"]["events"]

    assert events
    assert [row["timestamp_utc"] for row in events] == sorted(row["timestamp_utc"] for row in events)
    assert {row["type"] for row in events}.issubset(
        {"rashi_ingress", "nakshatra_ingress", "kakshya_ingress", "direction_station"}
    )
    for row in events:
        assert row["planet"] in {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        assert 1 <= row["kakshya_number"] <= 8
        assert row["kakshya_bindu"] in {0, 1}
        assert isinstance(row["natal_bav_bindus"], int)
        assert isinstance(row["natal_sav_bindus"], int)
        assert set(row["sensitive_timing"]) >= {"nakshatra_match", "rashi_match", "double_match"}


def test_transit_contract_propagates_selected_reduction_profile_to_sensitive_places():
    birth, chart = _published_chart_fixture()
    calc = AshtakavargaTransitCalculator(
        birth,
        chart,
        reduction_profile="parasharas_light_7",
    )
    result = calc.calculate_classical_transit_analysis("2026-08-31", window_days=1)

    assert result["convention"]["reduction_profile"] == "parasharas_light_7"
    assert result["convention"]["count_ascendant_as_occupant"] is True
    assert all(
        row["kakshya"]["interval"] == "[start, end)"
        for row in result["planet_transits"]
    )
