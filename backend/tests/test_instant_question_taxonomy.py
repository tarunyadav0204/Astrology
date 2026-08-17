from instant_chat_v2.question_taxonomy import (
    CONVERSATION_STATES,
    LIFE_DOMAINS,
    QUESTION_OPERATIONS,
    ROUTER_CATEGORY_LABELS,
    covered_domain_labels,
)
from instant_chat_v2.methodology import get_methodology
from instant_chat_v2.question_acceptance_cases import QUESTION_ACCEPTANCE_CASES


def test_every_router_category_has_a_declared_domain_contract():
    assert ROUTER_CATEGORY_LABELS <= covered_domain_labels()


def test_question_operations_define_answer_shape_and_failure_guards():
    assert len(QUESTION_OPERATIONS) >= 16
    for name, contract in QUESTION_OPERATIONS.items():
        assert contract.get("answer_mode"), name
        assert len(contract.get("required_answer") or []) >= 2, name
        assert contract.get("forbidden"), name
        assert contract.get("examples"), name


def test_core_predictive_operations_include_real_user_multilingual_examples():
    keys = {
        "topic_outlook", "period_outlook", "event_likelihood_or_timing",
        "comparison_or_choice", "problem_diagnosis",
    }
    for key in keys:
        examples = " ".join(QUESTION_OPERATIONS[key]["examples"])
        assert any(ord(char) > 127 for char in examples) or any(
            token in examples.lower() for token in ("karun", "kaisa", "kab", "kyun")
        ), key


def test_every_domain_declares_at_least_one_calculation_chart():
    for name, contract in LIFE_DOMAINS.items():
        charts = contract.get("divisionals") or []
        assert charts, name
        assert "D1" in charts, name


def test_supported_router_domains_do_not_silently_fall_back_to_general():
    for label in sorted(ROUTER_CATEGORY_LABELS - {"general", "timing"}):
        method = get_methodology(label, "topic_reading")
        assert method["domain"] != "general", label
        assert len(method.get("operations") or []) >= 3, label


def test_conversation_state_contract_covers_ambiguity_correction_and_safety():
    assert {
        "clear_first_turn", "ambiguous_reference", "clarification_reply",
        "correction", "contextual_follow_up", "insufficient_chart_data",
        "high_stakes_or_blocked",
    } <= set(CONVERSATION_STATES)
    for name, contract in CONVERSATION_STATES.items():
        assert contract.get("required"), name
        assert contract.get("example"), name


def test_acceptance_bank_is_bound_to_declared_operations_and_domains():
    assert len(QUESTION_ACCEPTANCE_CASES) >= 40
    covered_operations = set()
    covered_domains = set()
    seen_ids = set()
    for case in QUESTION_ACCEPTANCE_CASES:
        assert case["case_id"] not in seen_ids
        seen_ids.add(case["case_id"])
        assert case["operation"] in QUESTION_OPERATIONS, case["case_id"]
        assert case["domain"] in LIFE_DOMAINS, case["case_id"]
        covered_operations.add(case["operation"])
        covered_domains.add(case["domain"])
    assert set(LIFE_DOMAINS) <= covered_domains
    assert {
        "chart_fact", "explanation", "person_profile", "topic_outlook",
        "period_outlook", "event_likelihood_or_timing", "comparison_or_choice",
        "problem_diagnosis", "action_guidance", "compatibility",
        "muhurat_or_election", "multi_part",
    } <= covered_operations
