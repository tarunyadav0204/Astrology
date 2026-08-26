import asyncio

from chat.instant_chat_pipeline import _build_instant_context, generate_instant_chat_response
from instant_chat_v2.marriage_timeline import (
    build_phase_action,
    build_selection_response,
)
from utils.query_context import normalize_query_context


REFERENCE_BIRTH_DATA = {
    "name": "Tarun",
    "date": "1980-04-02",
    "time": "14:55:00",
    "latitude": 29.2396596,
    "longitude": 75.8174505,
    "timezone": "UTC+5:30",
    "place": "Hisar, Haryana, India",
}


def _selection_intent(stage, selection):
    return {
        "query_context": {
            "follow_up_type": "marriage_timeline_selection",
            "marriage_timeline_stage": stage,
            "marriage_timeline_selection": selection,
            "marriage_timeline_disclosure": "period_selected",
        }
    }


def _option(action, label):
    return next(row for row in action["options"] if row["label"] == label)


def _selected(option):
    return option["query_context"]["marriage_timeline_selection"]


def test_initial_marriage_history_action_offers_ranked_broad_phases_without_exact_dates():
    intent = {
        "category": "marriage",
        "mode": "LIFESPAN_EVENT_TIMING",
        "answer_mode": "event_prediction",
        "time_relation": "past",
        "evidence_plan": {
            "question_parts": [
                {"intent_families": ["event_timing"], "timeframe": {"kind": "open_past"}}
            ],
            "evidence_needs": [
                {"kind": "historical_dasha_event_windows"},
                {"kind": "historical_transit_event_windows"},
            ],
        },
    }
    context = _build_instant_context(
        REFERENCE_BIRTH_DATA,
        "When did I get married?",
        intent,
        [],
        answer_mode_override="event_prediction",
    )

    action = build_phase_action(context["normalized_evidence"]["event_timing_verdict"])

    assert action["type"] == "timeline_selection"
    assert action["selection_stage"] == "phase"
    assert len(action["options"]) == 3
    assert all(row["query_context"]["marriage_timeline_stage"] == "phase" for row in action["options"])
    assert action["disclosure_state"] == {
        "exact_date_known": False,
        "highest_disclosure": "none",
    }
    assert "2005-11-18" not in str(action)


def test_reference_chart_progressively_reaches_18_november_2005():
    phase = {
        "mahadasha": "Jupiter",
        "antardasha": "Venus",
        "start": "2003-09-16",
        "end": "2006-05-16",
    }
    pd_response = build_selection_response(
        birth_data=REFERENCE_BIRTH_DATA,
        intent=_selection_intent("phase", phase),
    )
    mercury_pd = _selected(_option(pd_response["next_action"], "Jupiter–Venus–Mercury"))
    assert mercury_pd["start"] <= "2005-11-18" <= mercury_pd["end"]

    sookshma_response = build_selection_response(
        birth_data=REFERENCE_BIRTH_DATA,
        intent=_selection_intent("pd", mercury_pd),
    )
    mercury_sookshma = _selected(_option(sookshma_response["next_action"], "Sookshma Mercury"))
    assert mercury_sookshma["start"] <= "2005-11-18" <= mercury_sookshma["end"]

    prana_response = build_selection_response(
        birth_data=REFERENCE_BIRTH_DATA,
        intent=_selection_intent("sookshma", mercury_sookshma),
    )
    jupiter_prana = _selected(_option(prana_response["next_action"], "Prana Jupiter"))
    assert jupiter_prana["start"] <= "2005-11-18" <= jupiter_prana["end"]

    date_response = build_selection_response(
        birth_data=REFERENCE_BIRTH_DATA,
        intent=_selection_intent("prana", jupiter_prana),
    )
    selected_date = _selected(_option(date_response["next_action"], "18 November 2005"))

    verification = build_selection_response(
        birth_data=REFERENCE_BIRTH_DATA,
        intent=_selection_intent("date", selected_date),
    )
    assert verification["next_action"] is None
    assert "user-selected date verification" in verification["body"]
    assert "not a date the chart independently discovered" in verification["body"]
    assert "Jupiter–Venus–Mercury–Mercury–Jupiter" in verification["body"]
    assert "KP 2–7–11" in verification["body"]


def test_query_context_preserves_structured_marriage_timeline_selection():
    selected = {
        "mahadasha": "Jupiter",
        "antardasha": "Venus",
        "start": "2003-09-16",
        "end": "2006-05-16",
    }
    normalized = normalize_query_context(
        {
            "follow_up_type": "marriage_timeline_selection",
            "marriage_timeline_stage": "phase",
            "marriage_timeline_selection": selected,
            "marriage_timeline_disclosure": "period_selected",
        }
    )

    assert normalized["marriage_timeline_stage"] == "phase"
    assert normalized["marriage_timeline_selection"] == selected
    assert normalized["marriage_timeline_disclosure"] == "period_selected"


def test_structured_selection_uses_deterministic_no_charge_instant_response():
    phase = {
        "mahadasha": "Jupiter",
        "antardasha": "Venus",
        "start": "2003-09-16",
        "end": "2006-05-16",
    }

    result = asyncio.run(
        generate_instant_chat_response(
            object(),
            question="Selected: Jupiter–Venus",
            birth_data=REFERENCE_BIRTH_DATA,
            intent=_selection_intent("phase", phase),
            history=[],
            language="english",
        )
    )

    assert result["success"] is True
    assert result["skip_instant_credit_charge"] is True
    assert result["chat_llm_model"] == "__marriage_timeline__"
    assert result["next_action"]["selection_stage"] == "pd"
    assert _option(result["next_action"], "Jupiter–Venus–Mercury")
