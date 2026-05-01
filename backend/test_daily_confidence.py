from daily.daily_confidence import build_daily_confidence


def test_eventful_but_frictional_day_shape():
    payload = build_daily_confidence(
        daily_prediction_spine={
            "ranked_triggers": [
                {"strength": "massive"},
                {"strength": "strong"},
                {"strength": "strong"},
            ],
            "daily_judgment": {
                "top_activated_houses": [{"house": 3}, {"house": 10}, {"house": 6}],
                "top_event_domains": [{"domain": "communication"}, {"domain": "career"}],
                "massive_result_factors": [{"planet": "Mercury"}],
                "moon_tara_quality": {"quality": "caution"},
            },
            "school_judgments": {
                "kp": {"verdict": "supports_materialization"},
                "ashtakavarga": {
                    "verdict": "mixed_or_workable",
                    "conflicts": [{"conflict": "high_sav_low_planet_bav"}],
                },
            },
        },
        fast_planets={"summary": {"overall_band": "active"}},
        intraday={
            "favorable_windows": [{"label": "Good"}],
            "caution_windows": [{"label": "Bad"}, {"label": "Worse"}, {"label": "Shift"}],
            "transition_windows": [{"label": "Moon shift"}],
        },
        daily_micro_intent={
            "name": "communication",
            "daily_focus": "message delivery",
            "houses": [3, 7, 11],
        },
    )
    assert payload["day_shape"] == "eventful_but_frictional"
    assert payload["event_likelihood"] == "high"


def test_smooth_but_low_manifestation_day_shape():
    payload = build_daily_confidence(
        daily_prediction_spine={
            "ranked_triggers": [],
            "daily_judgment": {
                "top_activated_houses": [{"house": 4}, {"house": 11}],
                "top_event_domains": [{"domain": "peace"}],
                "massive_result_factors": [],
                "moon_tara_quality": {"quality": "supportive"},
            },
            "school_judgments": {
                "kp": {"verdict": "weak_or_indirect_kp_trigger"},
                "ashtakavarga": {
                    "verdict": "supportive",
                    "conflicts": [],
                },
            },
        },
        fast_planets={"summary": {"overall_band": "background"}},
        intraday={
            "favorable_windows": [{"label": "Good"}, {"label": "Better"}],
            "caution_windows": [],
            "transition_windows": [],
        },
        daily_micro_intent={
            "name": "general_day",
            "daily_focus": "overall momentum",
            "houses": [1, 4, 7, 10, 11],
        },
    )
    assert payload["day_shape"] == "smooth_but_low_manifestation"
    assert payload["verdict"] in {"favorable", "mixed"}


def test_school_refinements_influence_confidence():
    payload = build_daily_confidence(
        daily_prediction_spine={
            "ranked_triggers": [{"strength": "strong"}],
            "daily_judgment": {
                "top_activated_houses": [{"house": 3}, {"house": 10}],
                "top_event_domains": [{"domain": "communication"}],
                "massive_result_factors": [],
                "moon_tara_quality": {"quality": "neutral"},
            },
            "school_judgments": {
                "kp": {"verdict": "strong_materialization_support"},
                "ashtakavarga": {
                    "verdict": "supportive_for_intent",
                    "conflicts": [],
                },
            },
        },
        fast_planets={"summary": {"overall_band": "active"}},
        intraday={"favorable_windows": [{"label": "Good"}], "caution_windows": [], "transition_windows": []},
        daily_micro_intent={"name": "communication", "daily_focus": "message delivery", "houses": [3, 7, 11]},
    )
    assert payload["verdict"] == "favorable"
    assert payload["event_likelihood"] in {"moderate", "high"}


if __name__ == "__main__":
    test_eventful_but_frictional_day_shape()
    test_smooth_but_low_manifestation_day_shape()
    test_school_refinements_influence_confidence()
    print("daily confidence tests passed")
