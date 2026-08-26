from chat.instant_chat_pipeline import (
    _build_instant_composer_context,
    _build_instant_context,
    _build_retrospective_budget_context,
    _mode_selection_from_intent,
    _rank_historical_marriage_periods,
)
from instant_chat_v2.graph_live import apply_live_graph_policy
from instant_chat_v2.orchestrator import build_instant_v2_packet
from instant_chat_v2.planner import build_query_plan


def test_historical_marriage_ranking_filters_confirmation_before_phase_diversity():
    house_lordships = {"Saturn": [7, 8], "Venus": [4, 11], "Jupiter": [6, 9]}
    repeated_phase = [
        {
            "start": f"2020-0{month}-01",
            "end": f"2020-0{month}-28",
            "mahadasha": "Saturn",
            "antardasha": "Venus",
            "pratyantardasha": planet,
            "relevance_score": 100 - month,
            "activated_focus_houses": [2, 5, 7, 11],
            "transit_trigger_score": 14,
            "peak_activation_windows": [{"start": f"2020-0{month}-10", "activated_focus_houses": [7, 11]}],
        }
        for month, planet in ((1, "Saturn"), (2, "Venus"), (3, "Jupiter"))
    ]
    distinct_2005_phase = {
        "start": "2005-06-02",
        "end": "2005-11-02",
        "mahadasha": "Jupiter",
        "antardasha": "Venus",
        "pratyantardasha": "Saturn",
        "relevance_score": 67,
        "activated_focus_houses": [2, 5, 7, 11],
        "transit_trigger_score": 5,
        "peak_activation_windows": [{"start": "2005-10-04", "activated_focus_houses": [5, 11]}],
    }
    unconfirmed = {
        "start": "2011-11-04",
        "end": "2012-04-24",
        "mahadasha": "Saturn",
        "antardasha": "Saturn",
        "pratyantardasha": "Saturn",
        "relevance_score": 999,
        "activated_focus_houses": [2, 7, 11],
        "transit_trigger_score": 0,
        "peak_activation_windows": [],
    }

    ranked = _rank_historical_marriage_periods(
        [unconfirmed, *repeated_phase, distinct_2005_phase],
        house_lordships,
        limit=3,
    )

    assert all(row["transit_trigger_score"] > 0 for row in ranked)
    assert len({(row["mahadasha"], row["antardasha"]) for row in ranked}) == 2
    assert any(row["start"].startswith("2005-") for row in ranked)


def test_reference_chart_retains_calculated_2005_marriage_window_in_top_three():
    birth_data = {
        "name": "Tarun",
        "date": "1980-04-02",
        "time": "14:55:00",
        "latitude": 29.2396596,
        "longitude": 75.8174505,
        "timezone": "UTC+5:30",
        "place": "Hisar, Haryana, India",
    }
    intent = {
        "category": "marriage",
        "mode": "LIFESPAN_EVENT_TIMING",
        "answer_mode": "explanation_mechanism",
        # A repeated direct question may be tagged as a follow-up because the
        # session already discussed marriage. It is still a timing request,
        # not a request to explain the previous answer.
        "turn_relation": "follow_up",
        "evidence_plan": {
            "question_parts": [
                {
                    "part_id": "marriage-history",
                    "intent_families": ["event_timing"],
                    "timeframe": {"kind": "open_past"},
                }
            ],
            "evidence_needs": [
                {"kind": "historical_dasha_event_windows"},
                {"kind": "historical_transit_event_windows"},
                {"kind": "natal_topic_foundation"},
            ],
        },
        "query_context": {"as_of": "2026-08-26T12:00:00+05:30"},
    }
    mode_selection = _mode_selection_from_intent(intent, "When did I get married?")
    assert mode_selection["raw_answer_mode"] == "explanation_mechanism"
    assert mode_selection["answer_mode"] == "event_prediction"

    context = _build_instant_context(
        birth_data,
        "When did I get married?",
        intent,
        [],
        answer_mode_override=mode_selection["answer_mode"],
    )

    verdict = context["normalized_evidence"]["event_timing_verdict"]
    assert context["intent_summary"]["answer_mode"] == "event_prediction"
    assert context["intent_summary"]["time_relation"] == "past"
    assert context["normalized_evidence"]["timing_policy"]["time_direction"] == "retrospective"
    ranked = verdict["ranked_windows"]
    confirmed_date = "2005-11-18"
    matching = [
        row for row in ranked
        if str(row.get("start") or "") <= confirmed_date <= str(row.get("end") or "")
        and row.get("mahadasha") == "Jupiter"
        and row.get("antardasha") == "Venus"
    ]
    assert matching, ranked
    assert matching[0]["mahadasha"] == "Jupiter"
    assert matching[0]["antardasha"] == "Venus"
    assert matching[0]["pratyantardasha"] == "Saturn"
    assert matching[0]["activated_focus_houses"] == [2, 5, 7, 11]
    assert matching[0]["phase_granularity"] == "MD_AD"
    assert matching[0]["phase_start"] < "2005-01-01"
    assert matching[0]["phase_end"] > confirmed_date
    assert matching[0]["strongest_pd_window"] == {
        "start": "2005-06-02",
        "end": "2005-11-02",
        "pratyantardasha": "Saturn",
        "rank_score": matching[0]["historical_marriage_rank_score"],
    }
    assert any(
        str(peak.get("probable_peak_date") or "").startswith("2005-")
        for peak in matching[0]["probable_peak_windows"]
    )

    packet = build_instant_v2_packet(
        question="When did I get married?",
        intent=intent,
        answer_mode="event_prediction",
        target_subject={"key": "self"},
        language="english",
        instant_context=context,
    )
    packet = apply_live_graph_policy(packet, intent=intent, context=context)
    graph_policy = packet["answer_spec"]["knowledge_graph_policy"]
    assert packet["query_plan"]["time_scope"]["retrospective"] is True
    assert graph_policy["runtime_key"] == "marriage_history"
    assert graph_policy["missing_required_factors"] == []
    assert graph_policy.get("claim_permission") != "directional_only_no_timing"

    composer = _build_instant_composer_context(context, packet)
    composer_windows = composer["verdict"]["ranked_windows"]
    composer_2005 = next(
        row for row in composer_windows
        if row.get("mahadasha") == "Jupiter" and row.get("antardasha") == "Venus"
    )
    assert composer_2005["strongest_pd_window"] == {
        "start": "2005-06-02",
        "end": "2005-11-02",
        "pratyantardasha": "Saturn",
        "rank_score": matching[0]["historical_marriage_rank_score"],
    }
    assert composer_2005["probable_peak_windows"]
    required_windows = composer["answer_contract"]["event_rules"]["required_material_windows"]
    required_2005 = next(
        row for row in required_windows
        if row.get("mahadasha") == "Jupiter" and row.get("antardasha") == "Venus"
    )
    assert required_2005["strongest_pd_window"]["start"] == "2005-06-02"
    assert required_2005["strongest_pd_window"]["end"] == "2005-11-02"
    assert required_2005["probable_peak_windows"]

    budget_context = _build_retrospective_budget_context(composer)
    assert budget_context["context_profile"] == "instant_retrospective_budget_v1"
    assert len(str(budget_context)) < 6000
    budget_2005 = next(
        row for row in budget_context["verdict"]["ranked_windows"]
        if row.get("mahadasha") == "Jupiter" and row.get("antardasha") == "Venus"
    )
    assert budget_2005["strongest_pd_window"] == {
        "start": "2005-06-02",
        "end": "2005-11-02",
        "pratyantardasha": "Saturn",
    }
    assert budget_2005["probable_peak_windows"]


def test_user_supplied_marriage_date_is_typed_as_confirmed_fact_not_prediction():
    intent = {
        "category": "marriage",
        "answer_mode": "event_prediction",
        "time_relation": "past",
        "dialogue_state": {
            "known_facts": {
                "timing_type": "past_event",
                "confirmed_event_date": "2005-11-18",
                "event_date_source": "user_confirmed",
            }
        },
    }

    plan = build_query_plan(
        question="I got married on 18 November 2005",
        intent=intent,
        answer_mode="event_prediction",
        target_subject={"key": "self"},
        language="english",
        as_of="2026-08-26",
    )

    assert plan["confirmed_life_event"] == {
        "date": "2005-11-18",
        "source": "user_confirmed",
        "category": "marriage",
        "claim_rule": (
            "Treat this as a fact supplied by the user. It may be used to verify calculated factors "
            "on that date, but must never be described as a date recovered or proven by astrology."
        ),
    }


def test_historical_evidence_request_is_an_authoritative_retrospective_signal():
    intent = {
        "category": "marriage",
        "answer_mode": "event_prediction",
        "required_evidence": [
            "historical_dasha_event_windows",
            "historical_transit_event_windows",
            "natal_topic_foundation",
        ],
    }

    plan = build_query_plan(
        question="When did I get married?",
        intent=intent,
        answer_mode="event_prediction",
        target_subject={"key": "self"},
        language="english",
        as_of="2026-08-26",
    )

    assert plan["time_scope"]["retrospective"] is True
    assert plan["time_scope"]["relation"] == "past"
    assert "future_dasha_event_windows" not in plan["requested_evidence"]


def test_genuine_explanation_followup_is_not_overwritten_by_life_event_guard():
    selection = _mode_selection_from_intent(
        {
            "category": "marriage",
            "mode": "LIFESPAN_EVENT_TIMING",
            "answer_mode": "explanation_mechanism",
            "turn_relation": "follow_up",
            "evidence_plan": {
                "question_parts": [
                    {"intent_families": ["event_timing"], "timeframe": {"kind": "open_past"}}
                ]
            },
        },
        "Why did you select that period?",
    )

    assert selection["answer_mode"] == "explanation_mechanism"
