from daily.daily_contract import build_daily_output_contract


def _sample_payload():
    return build_daily_output_contract(
        target_date="2026-04-30",
        daily_prediction_spine={
            "ranked_triggers": [
                {"level": "PR", "planet": "Mercury", "strength": "strong"},
                {"level": "SK", "planet": "Moon", "strength": "moderate"},
            ],
            "daily_judgment": {
                "top_event_domains": [{"domain": "communication"}, {"domain": "career"}],
            },
        },
        daily_micro_intent={
            "name": "communication",
            "daily_focus": "message delivery and response quality",
            "best_for": ["sending important communication", "follow-ups"],
            "watch_for": ["misunderstanding", "late replies"],
        },
        daily_confidence={
            "verdict": "mixed",
            "confidence_band": "moderate",
            "event_likelihood": "moderate",
            "day_shape": "eventful_but_frictional",
            "supporting_factors": ["Strong PR trigger is active."],
            "contradicting_factors": ["Moon tara adds friction."],
            "practical_guidance": "Use the cleaner window and avoid pushing emotionally charged conversations.",
        },
        intraday={
            "favorable_windows": [
                {"label": "Abhijit Muhurta", "start": "2026-04-30T12:10:00", "end": "2026-04-30T12:58:00", "quality": "supportive", "source": "special_times"}
            ],
            "caution_windows": [
                {"label": "Rahu Kalam", "start": "2026-04-30T13:30:00", "end": "2026-04-30T15:00:00", "quality": "caution", "source": "special_times"}
            ],
            "transition_windows": [
                {"label": "Moon nakshatra changes from Ardra to Punarvasu", "time_label": "2:18 PM", "at": "2026-04-30T14:18:00"}
            ],
        },
    )


def test_daily_output_contract_has_canonical_fields():
    payload = _sample_payload()
    assert payload["method"] == "daily_output_contract_v1"
    assert payload["target_date"] == "2026-04-30"
    assert payload["verdict"] == "mixed"
    assert payload["confidence_band"] == "moderate"
    assert payload["direct_answer"]
    assert payload["best_windows"]
    assert payload["caution_windows"]
    assert payload["transition_note"]


def test_daily_output_contract_direct_answer_is_direct():
    payload = _sample_payload()
    answer = payload["direct_answer"].lower()
    assert "mixed day" in answer
    assert "communication" in answer


if __name__ == "__main__":
    test_daily_output_contract_has_canonical_fields()
    test_daily_output_contract_direct_answer_is_direct()
    print("daily output contract tests passed")
