from charts.house_insight_service import (
    SHADBALA_VARGA_KEYS,
    _build_natal_evidence_ledger,
    _birth_obj,
    _factor,
    _natal_chart_for_shadbala,
    build_house_insight,
)


SAMPLE_BIRTH = {
    "name": "Sample",
    "date": "1990-04-23",
    "time": "06:15:00",
    "timezone": "UTC+5:30",
    "latitude": 13.0833333333,
    "longitude": 80.2833333333,
    "place": "Chennai",
}


def test_natal_chart_for_shadbala_includes_required_vargas():
    natal = _natal_chart_for_shadbala(_birth_obj(SAMPLE_BIRTH))
    for key in SHADBALA_VARGA_KEYS:
        assert key in natal["divisions"]
        assert natal["divisions"][key]


def test_build_house_insight_includes_worksheets():
    insight = build_house_insight(SAMPLE_BIRTH, house_num=1, chart_id="lagna")
    assert insight["house_num"] == 1
    assert insight["body_parts"] == insight["sign_body_parts"]
    assert insight["house_body_parts"] == ["head"]
    assert insight["verdict"]
    assert insight["support_factors"] or insight["stress_factors"]
    assert insight["raw"]["classical_grade"]
    lord = insight["lord_worksheet"]
    assert lord["planet"] == insight["house_lord"]
    assert lord["house"]
    assert lord["shadbala_rupas"] is not None
    assert lord["required_rupas"] is not None
    assert "support" in insight["argala"]
    assert "obstruction" in insight["argala"]
    assert insight["sav_givers"]["givers"]
    assert insight["natural_karakas"]
    assert insight.get("related_varga") is None
    assert "windows" in insight["timing"]
    assert insight["natal_assessment"]["method_version"] == "distinct_testimonies_v1"
    assert insight["verdict"] == insight["natal_assessment"]["verdict"]
    assert insight["raw"]["support_count"] == insight["natal_assessment"]["support_count"]
    assert insight["raw"]["stress_count"] == insight["natal_assessment"]["pressure_count"]


def test_house_10_has_related_varga_and_karakas():
    insight = build_house_insight(SAMPLE_BIRTH, house_num=10, chart_id="lagna")
    assert insight["related_varga"]["name"]
    assert insight["related_varga"]["lord"]
    assert insight["natural_karakas"]


def test_house_factors_keep_combustion_and_neecha_bhanga_separate():
    # Mercury is debilitated, combust and classically cancelled in this D1.
    # Cancellation mitigates the debilitation once; it does not erase the
    # independent combustion pressure.
    birth = {
        "name": "Condition sample",
        "date": "1978-03-10",
        "time": "04:08:00",
        "timezone": "Asia/Kolkata",
        "latitude": 28.4595,
        "longitude": 77.0266,
        "place": "Gurgaon",
    }
    insight = build_house_insight(birth, house_num=3, chart_id="lagna")
    support = [row["label"] for row in insight["support_factors"]]
    pressure = [row["label"] for row in insight["stress_factors"]]

    assert support.count(
        "Mercury has Neecha Bhanga, mitigating its debilitation while it occupies this house."
    ) == 1
    assert "Mercury occupies this house in debilitated dignity." in pressure
    assert "Mercury is combust, so its contribution to this house is under pressure." in pressure


def test_divisional_house_uses_and_exposes_natal_d1_combustion():
    birth = {
        "name": "Condition sample",
        "date": "1978-03-10",
        "time": "04:08:00",
        "timezone": "Asia/Kolkata",
        "latitude": 28.4595,
        "longitude": 77.0266,
        "place": "Gurgaon",
    }
    # Mercury rules this D9 house. Its combustion must come from the physical
    # D1 longitude, not from the derived distance between D9 placements.
    insight = build_house_insight(birth, house_num=5, chart_id="navamsa")
    combustion = insight["planet_conditions"]["Mercury"]["combustion"]

    assert combustion["is_combust"] is True
    assert combustion["source_chart"] == "D1"
    assert combustion["angular_distance"] is not None
    assert combustion["threshold"] is not None
    assert insight["lord_worksheet"]["combust"] is True
    assert insight["lord_worksheet"]["combustion"]["source_chart"] == "D1"


def test_house_insight_handles_tithi_with_no_dagdha_rashi():
    # 1990-01-26 noon at Delhi resolves to paksha tithi 15. The selected
    # classical table assigns no Dagdha rashis to Purnima/Amavasya.
    birth = {
        "name": "No Dagdha sample",
        "date": "1990-01-26",
        "time": "12:00:00",
        "timezone": "Asia/Kolkata",
        "latitude": 28.6139,
        "longitude": 77.209,
        "place": "Delhi",
    }

    insight = build_house_insight(birth, house_num=1, chart_id="navamsa")

    assert insight["house_num"] == 1
    assert all("Dagdha" not in row["label"] for row in insight["support_factors"])
    assert all("Dagdha" not in row["label"] for row in insight["stress_factors"])


def test_natal_house_verdict_does_not_change_with_transit_date():
    first = build_house_insight(
        SAMPLE_BIRTH,
        house_num=1,
        chart_id="lagna",
        transit_date="2026-01-15",
    )
    second = build_house_insight(
        SAMPLE_BIRTH,
        house_num=1,
        chart_id="lagna",
        transit_date="2026-09-28",
    )

    assert first["verdict"] == second["verdict"]
    assert first["natal_assessment"] == second["natal_assessment"]


def test_natal_assessment_counts_each_distinct_testimony_once():
    support = [
        _factor("Strong Shadbala", "good", "shadbala"),
        _factor("Own sign", "good", "dignity"),
        _factor("Yogi wording one", "good", "special", evidence_key="lord:Jupiter:yogi"),
        _factor("Yogi wording two", "good", "special", evidence_key="lord:Jupiter:yogi"),
        _factor("Derived Uttama summary", "good", "strength", contributes=False),
    ]
    pressure = [
        _factor("Combust", "warn", "combustion"),
        _factor("Enemy nakshatra", "warn", "occupant_nakshatra"),
    ]

    assessment = _build_natal_evidence_ledger(support, pressure)

    assert assessment["support_count"] == 3
    assert assessment["pressure_count"] == 2
    assert {row["label"] for row in assessment["supporting_testimonies"]} == {
        "Strong Shadbala", "Own sign", "Yogi wording one",
    }
    assert assessment["verdict"]["label"] == "Supported but pressured"
