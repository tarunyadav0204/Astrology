from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from ai.intent_router import IntentRouter, apply_education_routing_guards  # noqa: E402
from calculators.chart_calculator import ChartCalculator  # noqa: E402
from chat.instant_chat_pipeline import (  # noqa: E402
    _compact_education_foundation,
    _fit_composer_brief,
    _instant_real_chart_facts,
    _requested_charts_from_intent,
)
from instant_chat_v2.education import education_profile  # noqa: E402
from instant_chat_v2.education_graph_policy import EducationGraphPolicyStore  # noqa: E402
from instant_chat_v2.education_graph_runtime import (  # noqa: E402
    compare_education_graph_policy,
    education_graph_runtime_key,
)
from instant_chat_v2.graph_live import apply_live_graph_policy  # noqa: E402
from instant_chat_v2.planner import build_query_plan  # noqa: E402


EXPECTED_KEYS = {
    "education", "education_timing", "learning_style", "subject_fit", "course_comparison",
    "higher_education", "higher_education_timing", "exam_capacity", "exam_timing",
    "admission_capacity", "admission_timing", "scholarship", "research", "research_timing",
    "foreign_study", "foreign_study_timing", "education_obstacles", "education_resume",
    "foreign_study_comparison", "education_vs_work", "education_vs_work_timing",
    "education_remedies",
}
TIMED_KEYS = {
    "education_timing", "higher_education_timing", "exam_timing", "admission_timing",
    "research_timing", "foreign_study_timing",
    "education_vs_work_timing",
}


# This is the public manual-test contract.  Every question must have an
# explicit semantic route before Education can be called complete.
QUESTION_MATRIX = [
    ("What does my chart show about my overall education?", "overall", "topic_reading", "education"),
    ("What are my strongest educational abilities?", "overall", "potential_capacity", "education"),
    ("When is my next supportive period for education?", "overall", "event_prediction", "education_timing"),
    ("What kind of learning style suits me best?", "learning_style", "potential_capacity", "learning_style"),
    ("Why do I understand some subjects quickly but struggle to retain others?", "learning_style", "topic_reading", "learning_style"),
    ("Do I learn better through reading, discussion, practice or structured instruction?", "learning_style", "potential_capacity", "learning_style"),
    ("Which subjects am I naturally suited for?", "subject_fit", "potential_capacity", "subject_fit"),
    ("Does my chart support studying data science?", "subject_fit", "potential_capacity", "subject_fit"),
    ("Would psychology be a suitable field for me?", "subject_fit", "potential_capacity", "subject_fit"),
    ("Am I better suited to engineering, medicine, law or business?", "course_comparison", "comparison_choice", "course_comparison"),
    ("Should I choose an MBA or an MS in Data Science?", "course_comparison", "comparison_choice", "course_comparison"),
    ("Which suits me better: computer science or mechanical engineering?", "course_comparison", "comparison_choice", "course_comparison"),
    ("Should I pursue law, psychology or management?", "course_comparison", "comparison_choice", "course_comparison"),
    ("Does my chart support postgraduate education?", "higher_education", "potential_capacity", "higher_education"),
    ("Is pursuing a master’s degree suitable for me?", "higher_education", "potential_capacity", "higher_education"),
    ("Does my chart support completing a PhD?", "research", "potential_capacity", "research"),
    ("When is a supportive period to begin my master’s degree?", "higher_education", "event_prediction", "higher_education_timing"),
    ("Which months in the next year support starting higher education?", "higher_education", "event_prediction", "higher_education_timing"),
    ("Does my chart support success in competitive examinations?", "exam_capacity", "potential_capacity", "exam_capacity"),
    ("What are my strengths and weaknesses when preparing for exams?", "exam_capacity", "potential_capacity", "exam_capacity"),
    ("Why do I underperform in exams despite studying?", "education_obstacles", "problem_diagnosis", "education_obstacles"),
    ("Does my chart support clearing the UPSC examination?", "exam_capacity", "potential_capacity", "exam_capacity"),
    ("Am I likely to clear my professional certification exam this year?", "exam_capacity", "event_prediction", "exam_timing"),
    ("When is my next supportive exam-success period?", "exam_capacity", "event_prediction", "exam_timing"),
    ("Which months in the next year are best for taking an important exam?", "exam_capacity", "event_prediction", "exam_timing"),
    ("Does my chart support admission to a competitive university?", "admission_capacity", "potential_capacity", "admission_capacity"),
    ("What does my chart show about getting into my preferred college?", "admission_capacity", "potential_capacity", "admission_capacity"),
    ("Will I receive admission to an MBA programme this year?", "admission_capacity", "event_prediction", "admission_timing"),
    ("When is my next supportive admission period?", "admission_capacity", "event_prediction", "admission_timing"),
    ("Which months are strongest for submitting university applications?", "admission_capacity", "event_prediction", "admission_timing"),
    ("Does my chart support receiving a scholarship?", "scholarship", "potential_capacity", "scholarship"),
    ("Is educational funding or institutional support indicated for me?", "scholarship", "potential_capacity", "scholarship"),
    ("What could strengthen my chances of receiving a scholarship?", "scholarship", "potential_capacity", "scholarship"),
    ("Does my chart support a career in academic research?", "research", "potential_capacity", "research"),
    ("Am I temperamentally suited for long-term research?", "research", "potential_capacity", "research"),
    ("What kind of research subjects suit my chart?", "research", "potential_capacity", "research"),
    ("Does my chart support doctoral research in artificial intelligence?", "research", "potential_capacity", "research"),
    ("Why do I struggle to complete research projects?", "education_obstacles", "problem_diagnosis", "education_obstacles"),
    ("When is my next supportive period for beginning research?", "research", "event_prediction", "research_timing"),
    ("Which period is favourable for completing or publishing my research?", "research", "event_prediction", "research_timing"),
    ("Does my chart support studying abroad?", "foreign_study", "potential_capacity", "foreign_study"),
    ("Is foreign education stronger for me than studying in India?", "foreign_study", "comparison_choice", "foreign_study_comparison"),
    ("What does my chart show about completing a degree overseas?", "foreign_study", "potential_capacity", "foreign_study"),
    ("When could I get an opportunity to study abroad?", "foreign_study", "event_prediction", "foreign_study_timing"),
    ("Which months in the next year support foreign university admission?", "foreign_study", "event_prediction", "foreign_study_timing"),
    ("What is the main astrological reason for interruptions in my education?", "education_obstacles", "problem_diagnosis", "education_obstacles"),
    ("Why do I lose concentration while studying?", "education_obstacles", "problem_diagnosis", "education_obstacles"),
    ("Why do I keep changing my course or educational direction?", "education_obstacles", "problem_diagnosis", "education_obstacles"),
    ("Does my chart show difficulty with consistency, memory or examination pressure?", "education_obstacles", "problem_diagnosis", "education_obstacles"),
    ("Can I successfully resume my education after a long break?", "education_resume", "potential_capacity", "education_resume"),
    ("Does my chart support returning to college at this stage of life?", "education_resume", "potential_capacity", "education_resume"),
    ("Should I continue studying or start working now?", "education_vs_work", "decision_support", "education_vs_work"),
    ("Should I pursue an MBA or focus on growing my career?", "education_vs_work", "decision_support", "education_vs_work"),
    ("Is this a better year for higher education or professional experience?", "education_vs_work", "event_prediction", "education_vs_work_timing"),
    ("Would a PhD serve me better than continuing in my current job?", "education_vs_work", "decision_support", "education_vs_work"),
    ("Which calculated remedy is most relevant for my lack of concentration?", "education_remedies", "remedy_action", "education_remedies"),
    ("What astrological remedy is most relevant for recurring exam anxiety?", "education_remedies", "remedy_action", "education_remedies"),
    ("Which calculated remedy could support consistency in my studies?", "education_remedies", "remedy_action", "education_remedies"),
    ("What remedy does my chart indicate for repeated educational obstacles?", "education_remedies", "remedy_action", "education_remedies"),
    ("What is my long-term educational potential?", "overall", "potential_capacity", "education"),
    ("Do I have the capacity to clear competitive exams?", "exam_capacity", "potential_capacity", "exam_capacity"),
    ("When will I clear a competitive exam?", "exam_capacity", "event_prediction", "exam_timing"),
    ("Does my chart support foreign education?", "foreign_study", "potential_capacity", "foreign_study"),
    ("Does my chart support a scholarship?", "scholarship", "potential_capacity", "scholarship"),
    ("Should I study MBA or Data Science?", "course_comparison", "comparison_choice", "course_comparison"),
]


def _context(*, timing: bool = False, houses: list[int] | None = None) -> dict:
    context = {
        "intent_summary": {"category": "education", "answer_mode": "potential_capacity"},
        "normalized_evidence": {"education_foundation": {
            "houses_available": houses if houses is not None else list(range(1, 13)),
            "availability": {
                "d1": True, "d24": True, "d9": True, "d10": True,
                "learning_significators": True, "lord_nakshatra_chain": True,
                "dignity_strength": True, "education_yogas": True,
                "kp_fructification": True, "option_evidence": True,
                "remedy_blueprint": True,
            },
            "route_synthesis": {"verdict": "qualified"},
        }},
    }
    if timing:
        context["current_dashas"] = {"levels": {"MD": {"planet": "Jupiter"}}}
        context["current_transits"] = {"planets": {"Jupiter": {"house": 9}}}
    return context


def _required_houses(runtime_key: str) -> list[int]:
    return [
        int(value.rsplit("H", 1)[1])
        for value in EducationGraphPolicyStore().require(runtime_key).required_factors
        if value.startswith("education:H")
    ]


def test_education_ontology_compiles_and_validates() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_education_ontology.py")],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Education, Exams and Research ontology PoC valid: 22 competency questions" in result.stdout


def test_bundle_covers_all_routes_with_expandable_factor_children() -> None:
    store = EducationGraphPolicyStore()
    assert set(store.runtime_keys()) == EXPECTED_KEYS
    for key in EXPECTED_KEYS:
        question = store.require(key).graph_tree["children"][0]
        stages = next(node for node in question["children"] if node["label"] == "Decision stages")
        assert stages["children"], key
        for stage in stages["children"]:
            factors = next(node for node in stage["children"] if node["label"] == "Required astrology factors")
            assert factors["children"], f"{key}/{stage['label']}"


def test_static_routes_exclude_timing_and_timed_routes_require_complete_chain() -> None:
    store = EducationGraphPolicyStore()
    for key in EXPECTED_KEYS - TIMED_KEYS:
        exclusions = set(store.require(key).default_exclusions)
        assert {"education:DashaActivation", "education:TransitConfirmation"}.issubset(exclusions), key
    for key in TIMED_KEYS:
        policy = store.require(key)
        assert {"education:KPFructification", "education:DashaActivation", "education:TransitConfirmation"}.issubset(policy.required_factors)
        assert "education:StrictHorizon" in policy.guardrails


def test_all_semantic_subtypes_resolve_without_falling_back_to_overall() -> None:
    cases = {
        "learning_style": "learning_style", "subject_fit": "subject_fit",
        "course_comparison": "course_comparison", "higher_education": "higher_education",
        "exam_capacity": "exam_capacity", "admission_capacity": "admission_capacity",
        "scholarship": "scholarship", "research": "research", "foreign_study": "foreign_study",
        "foreign_study_comparison": "foreign_study_comparison",
        "education_obstacles": "education_obstacles", "education_resume": "education_resume",
        "education_vs_work": "education_vs_work", "education_remedies": "education_remedies",
    }
    modes = {"course_comparison": "comparison_choice", "education_vs_work": "decision_support", "education_remedies": "remedy_action", "education_obstacles": "problem_diagnosis"}
    for subtype, expected in cases.items():
        assert education_graph_runtime_key("education", {
            "education_subtype": subtype, "answer_mode": modes.get(subtype, "potential_capacity"),
        }) == expected


def test_timing_modes_upgrade_only_the_matching_education_event() -> None:
    cases = {
        "overall": "education_timing", "higher_education": "higher_education_timing",
        "exam_capacity": "exam_timing", "admission_capacity": "admission_timing",
        "research": "research_timing", "foreign_study": "foreign_study_timing",
        "education_vs_work": "education_vs_work_timing",
    }
    for subtype, expected in cases.items():
        assert education_graph_runtime_key("education", {
            "education_subtype": subtype, "answer_mode": "event_prediction",
        }) == expected


def test_static_long_term_wording_does_not_trigger_timing() -> None:
    assert education_graph_runtime_key("education", {
        "education_subtype": "higher_education", "answer_mode": "potential_capacity",
        "time_scope": {"requested": "long-term", "relation": "future"},
    }) == "higher_education"


def test_every_published_question_has_an_explicit_static_timing_or_boundary_route() -> None:
    for question, subtype, mode, expected_runtime_key in QUESTION_MATRIX:
        actual = education_graph_runtime_key("education", {
            "education_subtype": subtype, "answer_mode": mode,
        })
        assert actual == expected_runtime_key, question
        policy = EducationGraphPolicyStore().require(expected_runtime_key)
        comparison = compare_education_graph_policy(
            category="education",
            query_plan={"education_subtype": subtype, "answer_mode": mode},
            observed_answer_mode=mode,
            context=_context(
                timing=expected_runtime_key in TIMED_KEYS,
                houses=_required_houses(expected_runtime_key),
            ),
        )
        assert comparison and comparison["mode_match"] is True, (question, policy.answer_mode)


def test_settlement_after_study_is_not_answered_by_education_graph() -> None:
    assert education_graph_runtime_key("foreign", {
        "education_subtype": None, "answer_mode": "event_prediction",
    }) is None


def test_composer_compaction_preserves_route_specific_education_facts() -> None:
    context = {
        "query_plan": {"category": "education", "answer_mode": "potential_capacity"},
        "verdict": {"direction": "synthesize_from_calculated_education_foundation"},
        "answer_contract": {},
        "evidence": {"education_foundation": {
            "education_subtype": "subject_fit", "focus_houses": [5, 9, 10],
            "education_target": "Data Science",
            "route_synthesis": {
                "verdict": "supported", "target": "Data Science",
                "trait_results": [{
                    "trait": "analytical_quantitative",
                    "carriers": [{
                        "planet": "Mercury", "score": 3,
                        "support": ["D24: Mercury rules focus house 5"],
                    }],
                }],
            },
            "availability": {"d1": True, "d24": True},
        }},
    }
    compact = _fit_composer_brief(context, target_chars=400)
    route = compact["evidence"]["education_foundation"]["route_synthesis"]
    carrier = route["trait_results"][0]["carriers"][0]
    assert carrier["planet"] == "Mercury"
    assert carrier["support"] == ["D24: Mercury rules focus house 5"]


def test_higher_education_is_ninth_house_led_and_excludes_fourth_house() -> None:
    for subtype in ("higher_education", "higher_education_timing"):
        profile = education_profile("education", subtype)
        assert profile["houses"] == [9, 5, 11]
        policy = EducationGraphPolicyStore().require(subtype)
        assert "education:H9" in policy.required_factors
        assert "education:H5" in policy.required_factors
        assert "education:H11" in policy.required_factors
        assert "education:H4" not in policy.required_factors
        assert "education:H4" in policy.default_exclusions


def test_fourth_house_is_not_a_universal_education_factor() -> None:
    for subtype in (
        "subject_fit", "course_comparison", "higher_education", "higher_education_timing",
        "exam_capacity", "exam_timing", "foreign_study", "foreign_study_timing",
        "education_vs_work",
    ):
        assert 4 not in education_profile("education", subtype)["houses"], subtype


def test_router_guard_preserves_target_options_and_requests_correct_charts() -> None:
    intent = {
        "category": "education", "education_subtype": "course_comparison",
        "education_target": "masters", "education_options": ["MBA", "MS Data Science"],
    }
    apply_education_routing_guards(intent)
    assert intent["education_options"] == ["MBA", "MS Data Science"]
    assert intent["divisional_charts"] == ["D1", "D24", "D9"]
    assert _requested_charts_from_intent(intent, answer_mode="comparison_choice") == ["D1", "D24", "D9"]


def test_instant_finalizer_applies_education_guard_and_rejects_unknown_traits() -> None:
    raw = {
        "status": "READY", "mode": "ANALYZE_TOPIC_POTENTIAL",
        "category": "education", "education_subtype": "course_comparison",
        "answer_mode": "comparison_choice", "needs_transits": False,
        "education_target_traits": ["analytical_quantitative", "invented_trait"],
        "education_options": [
            {"label": "MBA", "traits": ["commercial_management", "leadership"]},
            {"label": "MS Data Science", "traits": ["technical_engineering", "research_depth"]},
        ],
    }
    result = IntentRouter()._finalize_instant_router_result(
        raw, current_year=2026, normalized_query_context=None,
    )
    assert result["education_target_traits"] == ["analytical_quantitative"]
    assert result["education_options"][0]["traits"] == ["commercial_management"]
    assert result["divisional_charts"] == ["D1", "D24", "D9"]

    research = IntentRouter()._finalize_instant_router_result({
        "status": "READY", "mode": "ANALYZE_TOPIC_POTENTIAL",
        "category": "research", "education_subtype": "research",
        "answer_mode": "potential_capacity", "needs_transits": False,
    }, current_year=2026, normalized_query_context=None)
    assert research["divisional_charts"] == ["D1", "D24", "D9", "D10"]


def test_research_and_education_vs_work_add_d10() -> None:
    for subtype in ("subject_fit", "research", "education_vs_work"):
        charts = _requested_charts_from_intent(
            {"category": "education", "education_subtype": subtype}, answer_mode="potential_capacity",
        )
        assert ("D10" in charts) is (subtype in {"research", "education_vs_work"})


def test_research_requires_d9_but_other_static_routes_do_not() -> None:
    store = EducationGraphPolicyStore()
    assert "education:D9" in store.require("research").required_factors
    assert "education:D9" in store.require("research_timing").required_factors
    assert "education:D9" not in store.require("subject_fit").required_factors


def test_complete_foundation_matches_static_and_timed_routes() -> None:
    static = compare_education_graph_policy(
        category="education", query_plan={"education_subtype": "exam_capacity", "answer_mode": "potential_capacity"},
        observed_answer_mode="potential_capacity", context=_context(houses=_required_houses("exam_capacity")),
    )
    assert static and static["match"] is True
    timed = compare_education_graph_policy(
        category="exams", query_plan={"education_subtype": "exam_timing", "answer_mode": "event_prediction"},
        observed_answer_mode="event_prediction", context=_context(timing=True, houses=_required_houses("exam_timing")),
    )
    assert timed and timed["match"] is True


def test_every_authored_route_is_reachable_and_complete_with_its_required_evidence() -> None:
    modes = {
        "education": "topic_reading", "education_timing": "event_prediction",
        "learning_style": "potential_capacity", "subject_fit": "potential_capacity",
        "course_comparison": "comparison_choice", "higher_education": "potential_capacity",
        "higher_education_timing": "event_prediction", "exam_capacity": "potential_capacity",
        "exam_timing": "event_prediction", "admission_capacity": "potential_capacity",
        "admission_timing": "event_prediction", "scholarship": "potential_capacity",
        "research": "potential_capacity", "research_timing": "event_prediction",
        "foreign_study": "potential_capacity", "foreign_study_timing": "event_prediction",
        "foreign_study_comparison": "comparison_choice",
        "education_obstacles": "problem_diagnosis", "education_resume": "potential_capacity",
        "education_vs_work": "decision_support", "education_vs_work_timing": "event_prediction",
        "education_remedies": "remedy_action",
    }
    for runtime_key, mode in modes.items():
        subtype = "overall" if runtime_key == "education" else runtime_key
        comparison = compare_education_graph_policy(
            category="education",
            query_plan={"education_subtype": subtype, "answer_mode": mode},
            observed_answer_mode=mode,
            context=_context(timing=runtime_key in TIMED_KEYS, houses=_required_houses(runtime_key)),
        )
        assert comparison and comparison["runtime_key"] == runtime_key
        assert comparison["match"] is True, (runtime_key, comparison["mismatches"])


def test_live_graph_is_authoritative_for_each_education_category() -> None:
    for category, subtype in (("education", "subject_fit"), ("learning", "learning_style"), ("exams", "exam_capacity"), ("research", "research")):
        packet = {
            "query_plan": {"category": category, "education_subtype": subtype, "answer_mode": "potential_capacity"},
            "verdict": {}, "answer_spec": {}, "verification": {},
        }
        resolved = apply_live_graph_policy(
            packet, intent=packet["query_plan"], context=_context(houses=_required_houses(subtype)),
        )
        policy = resolved["answer_spec"]["knowledge_graph_policy"]
        assert policy["live"] is True
        assert policy["domain"] == "education"
        assert policy["runtime_key"] == subtype


def test_planner_carries_all_education_semantics_without_text_matching() -> None:
    intent = {
        "category": "education", "answer_mode": "comparison_choice",
        "education_subtype": "course_comparison", "education_target": "postgraduate course",
        "education_target_traits": ["analytical_quantitative"],
        "education_options": ["MBA", "MSc"],
    }
    plan = build_query_plan(
        question="Which should I choose?", intent=intent, language="english",
        answer_mode="comparison_choice", target_subject={"key": "self", "label": "self"},
    )
    assert plan["education_subtype"] == "course_comparison"
    assert plan["education_target"] == "postgraduate course"
    assert plan["education_options"] == ["MBA", "MSc"]


def test_safety_boundaries_are_authored_for_every_relevant_route() -> None:
    store = EducationGraphPolicyStore()
    assert "education:ForeignStudyNotSettlement" in store.require("foreign_study").guardrails
    assert "education:ScholarshipNotAward" in store.require("scholarship").guardrails
    assert "education:NoGuaranteedResult" in store.require("exam_timing").guardrails
    assert "education:NoIntelligenceLabel" in store.require("learning_style").guardrails
    assert "education:NoGenericRemedy" in store.require("education_remedies").guardrails
    for key in TIMED_KEYS:
        assert "education:NoNodeFifthNinth" in store.require(key).guardrails


def test_reference_chart_builds_real_d1_d24_and_individualized_field_signatures() -> None:
    birth = {
        "name": "Tarun", "date": "1980-04-02", "time": "14:55:00",
        "latitude": 29.2396596, "longitude": 75.8174505,
        "timezone": "UTC+5:30", "place": "Hisar, Haryana, India",
    }
    chart = ChartCalculator({}).calculate_chart(SimpleNamespace(**birth))
    facts = _instant_real_chart_facts(
        chart_data=chart, requested_charts=["D1", "D24", "D9"],
        requested_fact=None, karaka_evidence={}, d1_snapshot={},
    )
    foundation = _compact_education_foundation(
        chart, birth, {"chart_facts": facts}, category="education",
        answer_mode="potential_capacity", education_subtype="subject_fit",
    )
    assert foundation["availability"]["d1"] is True
    assert foundation["availability"]["d24"] is True
    assert foundation["route_synthesis"]["verdict"] in {"supported", "qualified", "pressured"}
    assert len(foundation["ranked_field_signatures"]) >= 5
    assert foundation["ranked_field_signatures"][0]["support"]
    assert foundation["subject_synthesis"]["ranked_field_traits"]
    assert all(row["lord_nakshatra"] for row in foundation["lord_nakshatra_chains"])

    comparison = _compact_education_foundation(
        chart, birth, {"chart_facts": facts}, category="education",
        answer_mode="comparison_choice", education_subtype="course_comparison",
        education_options=[
            {"label": "MBA", "traits": ["commercial_management"]},
            {"label": "MS Data Science", "traits": ["analytical_quantitative", "technical_engineering"]},
        ],
    )
    rows = comparison["option_synthesis"]["options"]
    assert [row["option"] for row in rows] == ["MBA", "MS Data Science"]
    assert rows[0]["demand_traits"] != rows[1]["demand_traits"]

    postgraduate = _compact_education_foundation(
        chart, birth, {"chart_facts": facts}, category="education",
        answer_mode="potential_capacity", education_subtype="higher_education",
    )
    assert postgraduate["focus_houses"] == [9, 5, 11]
    assert postgraduate["ranked_field_signatures"] == []
    synthesis = postgraduate["higher_education_synthesis"]
    assert synthesis["primary_house"] == 9
    assert synthesis["supporting_houses"] == [5, 11]
    assert synthesis["excluded_house"] == 4
    assert {row["house"] for row in synthesis["house_lord_conditions"]} == {5, 9, 11}
    for chart_payload in postgraduate["charts"].values():
        for planet in (chart_payload.get("planets") or {}).values():
            assert 4 not in (planet.get("lordships") or [])


def test_reference_chart_produces_question_specific_adjudication_for_every_route() -> None:
    birth = {
        "name": "Tarun", "date": "1980-04-02", "time": "14:55:00",
        "latitude": 29.2396596, "longitude": 75.8174505,
        "timezone": "UTC+5:30", "place": "Hisar, Haryana, India",
    }
    chart = ChartCalculator({}).calculate_chart(SimpleNamespace(**birth))
    facts = _instant_real_chart_facts(
        chart_data=chart, requested_charts=["D1", "D24", "D9", "D10"],
        requested_fact=None, karaka_evidence={}, d1_snapshot={},
    )
    normalized = {
        "chart_facts": facts,
        "forward_event_dasha_scan": {"ranked_windows": [{
            "start": "2027-01-01", "end": "2027-03-31",
            "active_houses": list(range(1, 13)), "score": 5,
        }]},
        "remedy_blueprint": {
            "top_recommendation": {"id": "education_focus", "label": "calculated focus remedy"},
            "alternatives": [],
        },
    }
    modes = {
        "overall": "topic_reading", "education_timing": "event_prediction",
        "learning_style": "potential_capacity", "subject_fit": "potential_capacity",
        "course_comparison": "comparison_choice", "higher_education": "potential_capacity",
        "higher_education_timing": "event_prediction", "exam_capacity": "potential_capacity",
        "exam_timing": "event_prediction", "admission_capacity": "potential_capacity",
        "admission_timing": "event_prediction", "scholarship": "potential_capacity",
        "research": "potential_capacity", "research_timing": "event_prediction",
        "foreign_study": "potential_capacity", "foreign_study_comparison": "comparison_choice",
        "foreign_study_timing": "event_prediction", "education_obstacles": "problem_diagnosis",
        "education_resume": "potential_capacity", "education_vs_work": "decision_support",
        "education_vs_work_timing": "event_prediction", "education_remedies": "remedy_action",
    }
    for subtype, mode in modes.items():
        options = None
        traits = None
        target = None
        if subtype == "course_comparison":
            options = [
                {"label": "MBA", "traits": ["commercial_management"]},
                {"label": "MS Data Science", "traits": ["analytical_quantitative", "technical_engineering"]},
            ]
        elif subtype == "subject_fit":
            target, traits = "Data Science", ["analytical_quantitative", "technical_engineering"]
        elif subtype in {"research", "research_timing"}:
            target, traits = "AI research", ["research_depth", "technical_engineering"]
        foundation = _compact_education_foundation(
            chart, birth, normalized, category="education", answer_mode=mode,
            education_subtype=subtype, education_target=target,
            education_target_traits=traits, education_options=options,
        )
        route = foundation["route_synthesis"]
        assert route, subtype
        assert route.get("verdict") or route.get("direction") or route.get("static_direction"), subtype
        if subtype not in {"education_remedies"}:
            assert route.get("required_visible_facts", {}).get("D1"), subtype
            assert route.get("required_visible_facts", {}).get("D24"), subtype
        if subtype in TIMED_KEYS:
            assert route.get("promise_verdict"), subtype
            assert route.get("timing_verdict") == "supportive_windows_found", subtype
            assert foundation["timing_windows"], subtype

    learning = _compact_education_foundation(
        chart, birth, normalized, category="education", answer_mode="potential_capacity",
        education_subtype="learning_style",
    )
    assert len(learning["learning_style_synthesis"]["ranked_methods"]) >= 4
    assert learning["learning_style_synthesis"]["best_supported_methods"][0]["method"]

    obstacles = _compact_education_foundation(
        chart, birth, normalized, category="education", answer_mode="problem_diagnosis",
        education_subtype="education_obstacles",
    )
    assert obstacles["obstacle_synthesis"]["dominant_relative_vulnerability"]
    assert {row["mechanism"] for row in obstacles["obstacle_synthesis"]["mechanisms"]} >= {
        "concentration", "retention_and_recall", "consistency", "examination_pressure",
    }

    research = _compact_education_foundation(
        chart, birth, normalized, category="research", answer_mode="potential_capacity",
        education_subtype="research", education_target="academic research career",
        education_target_traits=["research_depth"],
    )
    assert research["research_synthesis"]["target_assessment"]["traits_complete"] is True
    assert research["research_synthesis"]["career_conversion"]["evidence_complete"] is True

    comparison = _compact_education_foundation(
        chart, birth, normalized, category="education", answer_mode="comparison_choice",
        education_subtype="foreign_study",
    )
    assert comparison["education_subtype"] == "foreign_study_comparison"
    assert comparison["foreign_study_synthesis"]["comparison"]["direction"] in {
        "foreign_stronger", "domestic_stronger", "mixed_or_close",
    }

    remedy = _compact_education_foundation(
        chart, birth, normalized, category="education", answer_mode="remedy_action",
        education_subtype="exam_capacity",
    )
    assert remedy["education_subtype"] == "education_remedies"
    assert remedy["remedy_synthesis"]["calculated"] is True
    assert remedy["availability"]["remedy_blueprint"] is True
