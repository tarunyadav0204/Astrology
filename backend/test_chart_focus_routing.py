import os
import sys

_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)


def test_extract_chart_focus_detects_d10():
    from ai.intent_router import extract_chart_focus_from_question

    focus = extract_chart_focus_from_question("Analyze my D10 chart deeply")

    assert focus is not None
    assert focus["kind"] == "chart_specific"
    assert focus["primary"] == "D10"
    assert focus["explicit"] is True


def test_extract_chart_focus_detects_lagna_as_d1_scope():
    from ai.intent_router import extract_chart_focus_from_question

    focus = extract_chart_focus_from_question("Please analyze my lagna")

    assert focus is not None
    assert focus["primary"] == "D1"
    assert focus["label"] == "Lagna"


def test_apply_chart_focus_guards_adds_requested_chart_and_metadata():
    from ai.intent_router import apply_chart_focus_guards

    result = {
        "category": "general",
        "divisional_charts": ["D1", "D9"],
        "extracted_context": {},
    }

    apply_chart_focus_guards(result, "Interpret my navamsha chart")

    assert result["chart_focus"]["primary"] == "D9"
    assert "D9" in result["divisional_charts"]
    assert result["extracted_context"]["chart_focus"]["label"] == "D9"


def test_chart_focus_branch_plan_narrows_d10_run():
    from ai.parallel_chat.orchestrator import _chart_focus_branch_plan

    enabled, reason = _chart_focus_branch_plan(
        {"chart_focus": {"kind": "chart_specific", "primary": "D10", "label": "D10"}}
    )

    assert enabled == ["parashari", "jaimini", "nakshatra"]
    assert reason == "chart_focus:D10"


def test_chart_focus_branch_plan_defaults_to_full_parallel_set():
    from ai.parallel_chat.orchestrator import _chart_focus_branch_plan

    enabled, reason = _chart_focus_branch_plan({"category": "career"})

    assert enabled == [
        "parashari",
        "jaimini",
        "nadi",
        "nakshatra",
        "kp",
        "ashtakavarga",
        "sudarshan",
    ]
    assert reason is None
