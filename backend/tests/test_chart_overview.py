from charts.chart_overview_service import build_chart_overview
from tests.test_house_insight_shadbala_vargas import SAMPLE_BIRTH


def test_chart_overview_has_houses_pillars_and_marks():
    overview = build_chart_overview(SAMPLE_BIRTH, chart_id="lagna")
    assert overview["chart_id"] == "lagna"
    assert overview["summary"]
    assert len(overview["houses"]) == 12
    assert overview["houses"][0]["house"] == 1
    assert overview["houses"][0]["verdict"]
    assert overview["pillars"]
    roles = {row["role"] for row in overview["pillars"]}
    assert "Lagna lord" in roles
    assert "Moon" in roles
    assert overview["now"]["mahadasha"]
    labels = {row["label"] for row in overview["special_marks"]}
    assert {"Yogi", "Avayogi", "Dagdha", "Badhaka"} <= labels
    assert any(row.get("marks") is not None for row in overview["houses"])


def test_chart_overview_marks_d1_d9_vargottama():
    from charts.chart_overview_service import SKIP_PLANETS
    from charts.house_insight_service import _birth_obj, _natal_chart_for_shadbala

    natal = _natal_chart_for_shadbala(_birth_obj(SAMPLE_BIRTH))
    d9 = (natal.get("divisions") or {}).get("D9") or {}
    expected = {
        planet
        for planet, data in (natal.get("planets") or {}).items()
        if planet not in SKIP_PLANETS
        and isinstance(data, dict)
        and data.get("sign") is not None
        and (d9.get(planet) or {}).get("sign") is not None
        and int(data["sign"]) == int(d9[planet]["sign"])
    }
    overview = build_chart_overview(SAMPLE_BIRTH, chart_id="lagna")
    marked = {
        row["value"].split(" · ")[0]
        for row in overview["special_marks"]
        if row["label"] == "Vargottama"
    }
    assert marked == expected
    if expected:
        assert any("VG" in (row.get("marks") or []) for row in overview["houses"])
