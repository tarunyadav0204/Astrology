from charts.house_insight_service import (
    SHADBALA_VARGA_KEYS,
    _birth_obj,
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
