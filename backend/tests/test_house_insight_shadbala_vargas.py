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
