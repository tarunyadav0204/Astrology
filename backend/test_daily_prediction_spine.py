from daily_prediction_spine import build_daily_prediction_spine


def _birth():
    return {
        "name": "Test Native",
        "date": "1980-01-01",
        "time": "12:00",
        "place": "Delhi",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "timezone": 5.5,
    }


def _static_context():
    planets = {
        "Sun":  {"longitude": 256.0, "house": 9},
        "Moon": {"longitude": 42.0, "house": 2},
        "Mars": {"longitude": 118.0, "house": 5},
        "Mercury": {"longitude": 245.0, "house": 9},
        "Jupiter": {"longitude": 156.0, "house": 6},
        "Venus": {"longitude": 300.0, "house": 11},
        "Saturn": {"longitude": 170.0, "house": 6},
        "Rahu": {"longitude": 132.0, "house": 5},
        "Ketu": {"longitude": 312.0, "house": 11},
    }
    planetary_analysis = {
        planet: {"basic_info": {"nakshatra": "Rohini", "pada": 1}}
        for planet in planets
    }
    planetary_analysis["Moon"] = {"basic_info": {"nakshatra": "Rohini", "pada": 2}}
    av_sav = {str(i): 24 + (i % 8) for i in range(12)}
    av_bav = {
        planet: {"bindus": {str(i): 2 + ((i + idx) % 5) for i in range(12)}}
        for idx, planet in enumerate(("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"))
    }
    return {
        "d1_chart": {
            "ascendant": 10.0,
            "planets": planets,
        },
        "planetary_analysis": planetary_analysis,
        "chara_karakas": {
            "chara_karakas": {
                "Atmakaraka": {"planet": "Sun", "house": 9},
                "Amatyakaraka": {"planet": "Mercury", "house": 9},
                "Gnatikaraka": {"planet": "Saturn", "house": 6},
                "Darakaraka": {"planet": "Mars", "house": 5},
            }
        },
        "kp_analysis": {
            "cusp_lords": {
                "1": {"sign_lord": "Mars", "star_lord": "Ketu", "sub_lord": "Venus", "sub_sub_lord": "Sun"},
                "6": {"sign_lord": "Mercury", "star_lord": "Moon", "sub_lord": "Saturn", "sub_sub_lord": "Rahu"},
                "10": {"sign_lord": "Saturn", "star_lord": "Mars", "sub_lord": "Mercury", "sub_sub_lord": "Jupiter"},
                "11": {"sign_lord": "Jupiter", "star_lord": "Rahu", "sub_lord": "Sun", "sub_sub_lord": "Moon"},
            },
            "planet_significators": {
                "Sun": [1, 10],
                "Moon": [2, 11],
                "Mars": [5, 10],
                "Mercury": [6, 10],
                "Jupiter": [9, 11],
                "Venus": [7, 11],
                "Saturn": [6, 8],
            },
            "four_step_theory": {
                "Mercury": {"planet": {"name": "Mercury", "houses": [6, 10]}},
                "Saturn": {"planet": {"name": "Saturn", "houses": [6, 8]}},
            },
        },
        "ashtakavarga": {
            "d1_rashi": {
                "sarvashtakavarga": {
                    "sarvashtakavarga": av_sav,
                    "total_bindus": sum(av_sav.values()),
                },
                "bhinnashtakavarga": av_bav,
            }
        },
    }


def test_daily_prediction_spine_has_five_level_dasha_evidence():
    out = build_daily_prediction_spine(
        birth_data=_birth(),
        static_context=_static_context(),
        intent_result={
            "mode": "PREDICT_DAILY",
            "dasha_as_of": "2026-04-26",
        },
    )

    assert out is not None
    assert out["target_date"] == "2026-04-26"
    assert out["method"] == "daily_spine_v1"
    levels = {row["level"] for row in out["dasha_stack"]}
    assert {"MD", "AD", "PD", "SK", "PR"}.issubset(levels)
    assert out["ranked_triggers"]
    assert out["daily_judgment"]["method"] == "daily_judgment_v1"
    assert out["daily_judgment"]["top_activated_houses"]
    assert out["daily_judgment"]["top_event_domains"]
    assert "prediction_rule" in out["daily_judgment"]
    schools = out["school_judgments"]
    assert schools["method"] == "daily_school_judgments_v1"
    assert schools["parashari"]["top_triggers"]
    assert schools["nadi"]["method"] == "nadi_daily_v1"
    assert schools["jaimini"]["method"] == "jaimini_daily_v1"
    assert schools["kp"]["method"] == "kp_daily_v1"
    assert schools["ashtakavarga"]["method"] == "ashtakavarga_daily_v1"
    assert schools["ashtakavarga"]["available"] is True
    assert schools["ashtakavarga"]["dasha_transit_usability"]
    for row in out["dasha_stack"]:
        assert row["planet"]
        assert row["natal"]["house"]
        assert row["transit"]["available"] is True
        assert "trigger" in row
        assert row["trigger"]["strength"] in {"background", "moderate", "strong", "massive"}
        assert "conjunct_natal_planet_details" in row["trigger"]


def test_daily_prediction_spine_ignores_non_daily():
    out = build_daily_prediction_spine(
        birth_data=_birth(),
        static_context=_static_context(),
        intent_result={"mode": "ANALYZE_PERSONALITY"},
    )
    assert out is None
