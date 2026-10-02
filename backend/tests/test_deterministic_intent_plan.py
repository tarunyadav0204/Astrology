from ai.intent_router import (
    _build_live_semantic_router_prompt,
    _build_semantic_only_planner_prompt,
    compare_deterministic_calculation_plan,
    compile_deterministic_calculation_plan,
)
from instant_chat_v2.career import CAREER_PROFILES
from instant_chat_v2.children import CHILDREN_PROFILES, BOUNDARY_CHILDREN_SUBTYPES
from instant_chat_v2.education import EDUCATION_PROFILES, TIMING_EDUCATION_SUBTYPES
from instant_chat_v2.foreign import FOREIGN_PROFILES, BOUNDARY_SUBTYPES as BOUNDARY_FOREIGN_SUBTYPES, TIMING_SUBTYPES as TIMING_FOREIGN_SUBTYPES
from instant_chat_v2.home import HOME_PROFILES, BOUNDARY_HOME_SUBTYPES, TIMING_HOME_SUBTYPES
from instant_chat_v2.nakshatra import NAKSHATRA_PROFILES


def test_semantic_prompt_removes_llm_owned_calculation_plan():
    prompt = """Header
Evidence planner:
- Build evidence.
Calibration:
- Preserve semantic distinctions.
Return exactly this JSON shape:
{
  "category": "career",
  "needs_transits": true or false,
  "divisional_charts": ["D1"],
  "transit_request": null,
  "evidence_plan": {"evidence_needs": []}
}
"""
    lean = _build_semantic_only_planner_prompt(prompt)

    assert "Evidence planner:" not in lean
    assert "Preserve semantic distinctions" in lean
    assert '"evidence_plan"' not in lean
    assert '"needs_transits"' not in lean
    assert '"semantic_timeframe"' in lean
    assert "Backend code deterministically selects charts" in lean


def test_live_semantic_v2_contract_has_no_llm_owned_calculation_fields():
    prompt = _build_live_semantic_router_prompt(
        user_question="मुझे नौकरी कब मिलेगी?",
        latest_user_reply="मुझे नौकरी कब मिलेगी?",
        history_text="",
        app_language="english",
        current_date="2026-10-01",
        dialogue_state_text="{}",
    )

    assert len(prompt) < 18000
    assert '"needs_transits"' not in prompt
    assert '"divisional_charts"' not in prompt
    assert '"transit_request"' not in prompt
    assert '"evidence_plan"' not in prompt
    assert "You alone interpret the user's language" in prompt
    assert "मुझे नौकरी कब मिलेगी?" in prompt


def test_compiler_builds_static_career_fit_plan():
    result = compile_deterministic_calculation_plan(
        {
            "status": "READY",
            "mode": "ANALYZE_TOPIC_POTENTIAL",
            "answer_mode": "potential_capacity",
            "category": "career",
            "career_subtype": "career_fit",
            "target_subject_key": "self",
            "semantic_timeframe": {"kind": "none"},
        },
        question="What are my main career strengths?",
        current_year=2026,
    )

    assert result["planning_source"] == "deterministic_v1"
    assert result["needs_transits"] is False
    assert "D10" in result["divisional_charts"]
    assert result["evidence_plan"]["question_parts"][0]["life_domain"] == "career"
    assert result["evidence_plan"]["question_parts"][0]["event_profile"] == "career_fit"
    assert [need["kind"] for need in result["evidence_plan"]["evidence_needs"]] == [
        "natal_topic_foundation",
    ]
    assert result["evidence_plan"]["evidence_needs"][0]["params"] == {
        "event_profile": "career_fit",
        "required_charts": ["D1", "D10", "Karkamsa"],
    }


def test_compiler_collapses_generic_duplicate_facets_for_static_subtype():
    result = compile_deterministic_calculation_plan(
        {
            "status": "READY",
            "mode": "ANALYZE_TOPIC_POTENTIAL",
            "answer_mode": "potential_capacity",
            "category": "career_fit",
            "career_subtype": "career_fit",
            "semantic_timeframe": {"kind": "open_future"},
            "question_parts": [
                {"part_id": "p1", "life_domain": "career", "event_profile": "career_fit", "subject": "self", "timeframe": {"kind": "open_future"}},
                {"part_id": "p2", "life_domain": "career", "event_profile": "general_event", "subject": "self", "timeframe": {"kind": "open_future"}},
            ],
        },
        question="ignored by semantic compilation",
        current_year=2026,
    )

    parts = result["evidence_plan"]["question_parts"]
    assert len(parts) == 1
    assert parts[0]["event_profile"] == "career_fit"
    assert parts[0]["timeframe"] == {"kind": "none"}


def test_compiler_builds_promotion_timing_plan():
    result = compile_deterministic_calculation_plan(
        {
            "status": "READY",
            "mode": "LIFESPAN_EVENT_TIMING",
            "answer_mode": "event_prediction",
            "category": "career",
            "career_subtype": "promotion",
            "target_subject_key": "self",
            "semantic_timeframe": {"kind": "open_future"},
        },
        question="When will I be promoted?",
        current_year=2026,
    )

    assert result["needs_transits"] is True
    assert "D10" in result["divisional_charts"]
    assert result["evidence_plan"]["question_parts"][0]["event_profile"] == "promotion"
    assert [need["kind"] for need in result["evidence_plan"]["evidence_needs"]] == [
        "natal_topic_foundation", "future_dasha_event_windows", "transit_event_windows",
    ]
    assert result["transit_request"]["startYear"] == 2026


def test_compiler_builds_exact_day_transit_request():
    result = compile_deterministic_calculation_plan(
        {
            "status": "READY",
            "mode": "PREDICT_DAILY",
            "answer_mode": "timing_window",
            "category": "exams",
            "target_subject_key": "self",
            "daily_intent_confirmed": True,
            "extracted_context": {
                "specific_date": "2026-10-02",
                "specific_date_basis": "relative_user_day",
            },
            "semantic_timeframe": {"kind": "specific_date", "date": "2026-10-02"},
        },
        question="How will my exam go tomorrow?",
        current_year=2026,
    )

    assert result["needs_transits"] is True
    assert result["transit_request"] == {
        "startYear": 2026,
        "endYear": 2026,
        "yearMonthMap": {"2026": ["October"]},
    }
    assert "D24" in result["divisional_charts"]


def test_compiler_reads_exact_day_from_semantic_timeframe_without_text_parsing():
    result = compile_deterministic_calculation_plan(
        {
            "status": "READY",
            "mode": "PREDICT_DAILY",
            "answer_mode": "event_prediction",
            "category": "career",
            "career_subtype": "client_relationship",
            "target_subject_key": "self",
            "semantic_timeframe": {"kind": "specific_date", "start": "2026-10-02"},
            "question_parts": [
                {"part_id": "p1", "intent_families": ["event_timing"], "life_domain": "career", "event_profile": "general_event", "subject": "self", "timeframe": {"kind": "specific_date", "start": "2026-10-02"}},
            ],
            "extracted_context": {},
        },
        question="ignored by semantic compilation",
        current_year=2026,
    )

    assert result["transit_request"] == {
        "startYear": 2026,
        "endYear": 2026,
        "yearMonthMap": {"2026": ["October"]},
    }
    assert [need["kind"] for need in result["evidence_plan"]["evidence_needs"]] == [
        "natal_topic_foundation",
        "transit_event_windows",
    ]
    assert result["evidence_plan"]["evidence_needs"][1]["params"] == {
        "date": "2026-10-02"
    }


def test_compiler_matches_legacy_marriage_timing_contract():
    result = compile_deterministic_calculation_plan(
        {
            "status": "READY",
            "mode": "LIFESPAN_EVENT_TIMING",
            "answer_mode": "event_prediction",
            "category": "marriage",
            "marriage_subtype": "general",
            "target_subject_key": "self",
            "semantic_timeframe": {"kind": "open_future"},
            "question_parts": [{
                "part_id": "p1",
                "life_domain": "marriage",
                "event_profile": "general_event",
                "subject": "self",
                "timeframe": {"kind": "none"},
            }],
        },
        question="When will I get married?",
        current_year=2026,
    )

    assert result["divisional_charts"] == ["D1", "D9"]
    part = result["evidence_plan"]["question_parts"][0]
    assert part["event_profile"] == "marriage"
    assert part["timeframe"] == {"kind": "open_future"}
    assert [need["kind"] for need in result["evidence_plan"]["evidence_needs"]] == [
        "natal_topic_foundation", "future_dasha_event_windows", "transit_event_windows",
    ]
    assert all(
        need["system"] == "parashari"
        for need in result["evidence_plan"]["evidence_needs"]
    )
    assert "required_charts" not in result["evidence_plan"]["evidence_needs"][1]["params"]


def test_compiler_preserves_promise_and_timing_as_distinct_compatible_parts():
    result = compile_deterministic_calculation_plan(
        {
            "status": "READY",
            "mode": "LIFESPAN_EVENT_TIMING",
            "answer_mode": "event_prediction",
            "category": "marriage",
            "marriage_subtype": "general",
            "target_subject_key": "self",
            "semantic_timeframe": {"kind": "open_future"},
            "question_parts": [
                {"part_id": "promise", "intent_families": ["topic_outlook"], "life_domain": "marriage", "event_profile": "marriage", "subject": "self", "timeframe": {"kind": "open_future"}},
                {"part_id": "timing", "intent_families": ["event_timing"], "life_domain": "marriage", "event_profile": "marriage", "subject": "self", "timeframe": {"kind": "open_future"}},
            ],
        },
        question="ignored by semantic compilation",
        current_year=2026,
    )

    assert [
        part["intent_families"] for part in result["evidence_plan"]["question_parts"]
    ] == [["topic_outlook"], ["event_timing"]]


def test_compiler_uses_structured_visa_profile_for_generic_part():
    result = compile_deterministic_calculation_plan(
        {
            "status": "READY",
            "mode": "LIFESPAN_EVENT_TIMING",
            "answer_mode": "event_prediction",
            "category": "visa",
            "foreign_subtype": "visa_timing",
            "target_subject_key": "self",
            "semantic_timeframe": {"kind": "open_future"},
            "question_parts": [
                {"part_id": "p1", "intent_families": ["event_timing"], "life_domain": "general", "event_profile": "general_event", "subject": "self", "timeframe": {"kind": "open_future"}},
            ],
        },
        question="ignored by semantic compilation",
        current_year=2026,
    )

    part = result["evidence_plan"]["question_parts"][0]
    assert part["life_domain"] == "relocation"
    assert part["event_profile"] == "visa"
    assert result["evidence_plan"]["evidence_needs"][0]["params"]["event_profile"] == "visa"


def _compile_profile(*, category, subtype_field, subtype, timing=False, answer_mode=None):
    return compile_deterministic_calculation_plan(
        {
            "status": "READY",
            "route_action": "answer",
            "mode": "LIFESPAN_EVENT_TIMING" if timing else "ANALYZE_TOPIC_POTENTIAL",
            "answer_mode": answer_mode or ("event_prediction" if timing else "topic_reading"),
            "category": category,
            subtype_field: subtype,
            "target_subject_key": "self",
            "semantic_timeframe": {"kind": "open_future" if timing else "none"},
        },
        question=f"contract case for {subtype}",
        current_year=2026,
    )


def test_compiler_covers_every_declared_career_profile():
    for subtype, profile in CAREER_PROFILES.items():
        result = _compile_profile(
            category="career", subtype_field="career_subtype", subtype=subtype,
            timing=bool(profile.get("timing_default")),
        )
        assert result["career_subtype"] == subtype
        assert result["divisional_charts"] == profile["divisionals"]
        assert result["evidence_plan"]["question_parts"]


def test_compiler_covers_every_declared_education_profile():
    for subtype in EDUCATION_PROFILES:
        timing = subtype in TIMING_EDUCATION_SUBTYPES
        result = _compile_profile(
            category="education", subtype_field="education_subtype", subtype=subtype,
            timing=timing,
            answer_mode="remedy_action" if subtype == "education_remedies" else None,
        )
        assert result["education_subtype"] == subtype
        assert "D24" in result["divisional_charts"]
        assert result["needs_transits"] is timing


def test_compiler_covers_every_declared_children_profile():
    for subtype in CHILDREN_PROFILES:
        timing = subtype.endswith("_timing") or subtype in {"first_child", "subsequent_child"}
        result = _compile_profile(
            category="children", subtype_field="children_subtype", subtype=subtype,
            timing=timing,
        )
        assert result["children_subtype"] == subtype
        if subtype in BOUNDARY_CHILDREN_SUBTYPES:
            assert result["divisional_charts"] == []
        else:
            assert "D7" in result["divisional_charts"]


def test_compiler_covers_every_declared_home_profile():
    for subtype in HOME_PROFILES:
        timing = subtype in TIMING_HOME_SUBTYPES
        result = _compile_profile(
            category="property", subtype_field="home_subtype", subtype=subtype,
            timing=timing,
            answer_mode="remedy_action" if subtype == "property_remedy" else None,
        )
        if subtype == "foreign_handoff":
            assert result["category"] == "foreign"
            assert result["foreign_subtype"] == "foreign_residence"
            continue
        if subtype == "inheritance_handoff":
            assert result["category"] == "inheritance"
            assert result["divisional_charts"] == ["D1", "D2", "D8"]
            continue
        assert result["home_subtype"] == subtype
        if subtype in BOUNDARY_HOME_SUBTYPES:
            assert result["divisional_charts"] == []
        elif subtype.startswith("vehicle_"):
            assert result["divisional_charts"] == ["D1", "D4", "D16"]
        else:
            assert result["divisional_charts"] == ["D1", "D4"]


def test_compiler_covers_every_declared_foreign_profile():
    for subtype, profile in FOREIGN_PROFILES.items():
        timing = subtype in TIMING_FOREIGN_SUBTYPES
        result = _compile_profile(
            category="foreign", subtype_field="foreign_subtype", subtype=subtype,
            timing=timing,
            answer_mode="remedy_action" if subtype == "foreign_remedy" else None,
        )
        assert result["foreign_subtype"] == subtype
        assert result["divisional_charts"] == ([] if subtype in BOUNDARY_FOREIGN_SUBTYPES else profile["charts"])


def test_compiler_covers_every_declared_nakshatra_profile():
    for subtype, profile in NAKSHATRA_PROFILES.items():
        timing = subtype == "nakshatra_timing"
        result = _compile_profile(
            category="nakshatra", subtype_field="nakshatra_subtype", subtype=subtype,
            timing=timing,
            answer_mode=profile["answer_mode"],
        )
        assert result["nakshatra_subtype"] == subtype
        assert result["divisional_charts"] == profile["charts"]


def test_shadow_comparison_reports_contract_fields_without_question_text():
    legacy = {
        "mode": "ANALYZE_TOPIC_POTENTIAL",
        "context_type": "birth",
        "needs_transits": False,
        "divisional_charts": ["D1", "D10"],
        "evidence_plan": {
            "question_parts": [{
                "text": "private user wording",
                "intent_families": ["topic_outlook"],
                "life_domain": "career",
                "event_profile": "career_fit",
                "subject": "self",
                "timeframe": {"kind": "none"},
            }],
            "evidence_needs": [],
        },
    }
    deterministic = {
        **legacy,
        "divisional_charts": ["D1", "D10", "Karkamsa"],
        "evidence_plan": {
            **legacy["evidence_plan"],
            "question_parts": [{
                **legacy["evidence_plan"]["question_parts"][0],
                "text": "different private wording",
            }],
        },
    }

    assert compare_deterministic_calculation_plan(legacy, deterministic) == [
        "divisional_charts"
    ]
