from calculators.event_predictor_ai import EventPredictor
from calculators.event_timeline_context_prune import prune_for_event_timeline


class _Stub:
    pass


def test_event_timeline_prune_keeps_core_timing_spine():
    context = {
        "unified_dasha_timeline": {"vimshottari_periods": [1]},
        "requested_dasha_summary": {"vimshottari_sequence": [2]},
        "period_dasha_activations": {"dasha_activations": [3]},
        "transit_activations": [{"x": 1}],
        "kp_analysis": {"drop": True},
    }
    out = prune_for_event_timeline(context)
    assert "unified_dasha_timeline" in out
    assert "requested_dasha_summary" in out
    assert "period_dasha_activations" in out
    assert "transit_activations" in out
    assert "kp_analysis" not in out


def test_attach_timeline_summary_builds_ranked_month_windows():
    predictor = EventPredictor(_Stub(), _Stub(), _Stub(), _Stub())
    payload = {
        "monthly_predictions": [
            {
                "month_id": 5,
                "events": [
                    {
                        "type": "Career Rise",
                        "prediction": "A visible career rise becomes likely.",
                        "trigger_logic": "Double transit and strong D10 support.",
                        "activation_reasoning": "10th house activation.",
                        "start_date": "2026-05-10",
                        "end_date": "2026-05-25",
                        "intensity": "High",
                        "possible_manifestations": [{"scenario": "x", "reasoning": "y"}],
                    }
                ],
            },
            {
                "month_id": 6,
                "events": [
                    {
                        "type": "Marriage Window",
                        "prediction": "A marriage or engagement window opens.",
                        "trigger_logic": "Nakshatra return and relationship activation.",
                        "activation_reasoning": "7th house and Venus activation.",
                        "start_date": "2026-06-05",
                        "end_date": "2026-06-18",
                        "intensity": "High",
                        "possible_manifestations": [{"scenario": "x", "reasoning": "y"}],
                    }
                ],
            },
        ]
    }
    out = predictor._attach_timeline_summary(2026, payload)
    assert "timeline_summary" in out
    assert out["timeline_summary"]["best_months"]
    assert out["timeline_summary"]["candidate_windows"]
    assert out["monthly_predictions"][0]["month_summary"]["headline"]
