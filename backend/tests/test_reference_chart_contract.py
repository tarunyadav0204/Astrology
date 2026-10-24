"""Regression checks for reference-Lagna chart recasting."""

from charts.routes import _recast_reference_chart


def test_reference_lagna_recasts_houses_without_moving_natal_planets():
    natal = {
        "ascendant": 12.0,
        "planets": {
            "Sun": {"longitude": 134.0, "sign": 4, "house": 5},
            "Moon": {"longitude": 47.0, "sign": 1, "house": 2},
        },
    }

    recast = _recast_reference_chart(natal, {
        "key": "chandra_lagna",
        "name": "Chandra Lagna",
        "sign": 1,
        "longitude": 47.0,
        "precision": "exact_longitude",
    })

    assert recast["ascendant"] == 47.0
    assert recast["houses"][0]["sign"] == 1
    assert recast["planets"]["Moon"]["house"] == 1
    assert recast["planets"]["Sun"]["house"] == 4
    # A reference chart changes house counting only; it is never a varga map.
    assert recast["planets"]["Sun"]["longitude"] == natal["planets"]["Sun"]["longitude"]
    assert natal["planets"]["Sun"]["house"] == 5


def test_sign_only_reference_uses_marked_plotting_anchor():
    recast = _recast_reference_chart({"planets": {"Moon": {"sign": 7}}}, {
        "key": "indu_lagna",
        "name": "Indu Lagna",
        "sign": 7,
        "precision": "sign_only",
        "longitude_is_plotting_anchor": True,
    })

    assert recast["ascendant"] == 225.0
    assert recast["reference_lagna"]["longitude_is_plotting_anchor"] is True
