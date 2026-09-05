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
