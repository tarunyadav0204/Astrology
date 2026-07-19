from reports.context.janam_kundli_context_builder import _catalog_all_yogas, _yoga_polarity


def test_health_beneficial_yogas_are_auspicious():
    assert _yoga_polarity("health_yogas", {"name": "Ayur Yoga", "type": "beneficial"}) == "auspicious"
    assert _yoga_polarity("health_yogas", {"name": "Chandra Sukha Yoga", "type": "beneficial"}) == "auspicious"
    assert _yoga_polarity(
        "health_yogas",
        {"name": "Vipareeta Raja Yoga (Health)", "type": "beneficial"},
    ) == "auspicious"


def test_health_aristha_yogas_are_challenging():
    assert _yoga_polarity(
        "health_yogas",
        {"name": "Lagna Lord Aristha Yoga", "type": "affliction"},
    ) == "challenging"
    assert _yoga_polarity("health_yogas", {"name": "Mangal Dosha"}) == "challenging"


def test_catalog_splits_mixed_health_bucket():
    catalog = _catalog_all_yogas({
        "health_yogas": [
            {
                "name": "Ayur Yoga",
                "type": "beneficial",
                "strength": "High",
                "description": "good longevity",
            },
            {
                "name": "Lagna Lord Aristha Yoga",
                "type": "affliction",
                "strength": "High",
                "description": "health challenges",
            },
            {
                "name": "Vipareeta Raja Yoga (Health)",
                "type": "beneficial",
                "strength": "Medium",
                "description": "reduces hospitalization",
            },
        ],
        "parivartana_yogas": {
            "dainya_yogas": [
                {
                    "name": "Dainya Yoga",
                    "strength": "Medium",
                    "description": "dusthana exchange",
                }
            ]
        },
    })
    by_name = {y["name"]: y["polarity"] for y in catalog}
    assert by_name["Ayur Yoga"] == "auspicious"
    assert by_name["Vipareeta Raja Yoga (Health)"] == "auspicious"
    assert by_name["Lagna Lord Aristha Yoga"] == "challenging"
    assert by_name["Dainya Yoga"] == "challenging"
