import json
from pathlib import Path

from ai.relational_answer_evaluator import RelationalAnswerEvaluator


def test_relational_answer_evaluator_fixture():
    path = Path(__file__).parent / "testdata" / "relational_parallel_answer_samples.json"
    rows = json.loads(path.read_text(encoding="utf-8"))

    for row in rows:
        result = RelationalAnswerEvaluator.evaluate(
            text=row["answer"],
            profile={
                "relation_family": row["relation_family"],
                "event_topic": row["event_topic"],
            },
            question=row["question"],
        )
        assert result["passed"] is row["should_pass"], {"row": row, "result": result}


def test_relational_answer_evaluator_flags_non_romantic_spouse_framing():
    result = RelationalAnswerEvaluator.evaluate(
        text=(
            "**Direct Answer**: Your marriage compatibility is unstable.\n\n"
            "**Main Astrological Evidence**: Venus and spouse factors are weak.\n\n"
            "FAQ_META: {\"category\":\"general\",\"canonical_question\":\"Guru trust\"}"
        ),
        profile={"relation_family": "guru_disciple", "event_topic": "guru_trust_breach"},
        question="Is this a fake guru or spiritual fraud?",
    )

    assert result["passed"] is False
    assert "non_romantic_spouse_framing_clean" in result["failed_checks"]


def test_relational_answer_evaluator_requires_timing_clarity_for_timing_questions():
    result = RelationalAnswerEvaluator.evaluate(
        text=(
            "**Direct Answer**: Reconciliation is possible.\n\n"
            "**Main Astrological Evidence**: The 7th house and Moon are active.\n\n"
            "FAQ_META: {\"category\":\"marriage\",\"canonical_question\":\"Reconciliation timing\"}"
        ),
        profile={"relation_family": "spouse_romantic", "event_topic": "reconciliation_return"},
        question="Will she come back and reconcile?",
    )

    assert result["passed"] is False
    assert "timing_clarity_present" in result["failed_checks"]


def test_relational_answer_evaluator_requires_optional_branch_signal_when_strongly_available():
    result = RelationalAnswerEvaluator.evaluate(
        text=(
            "**Direct Answer**: Reconciliation is possible in the coming months.\n\n"
            "**Main Astrological Evidence**: The 7th house, Moon, and current dasha support renewed dialogue.\n\n"
            "**Timing Windows**: A better phase appears within the next 3 to 5 months.\n\n"
            "FAQ_META: {\"category\":\"marriage\",\"canonical_question\":\"Reconciliation timing\"}"
        ),
        profile={"relation_family": "spouse_romantic", "event_topic": "reconciliation_return"},
        question="Will she come back and reconcile?",
        evidence_spine={
            "ashtakavarga_relational_evidence": {
                "available": True,
                "comparative": {"support": "both_supportive"},
            },
            "sudarshana_relational_evidence": {
                "available": True,
                "comparative": {"both_supportive": True, "native_current_support": "supportive"},
            },
        },
    )

    assert result["passed"] is False
    assert "optional_branch_signal_used" in result["failed_checks"]


def test_relational_answer_evaluator_accepts_optional_branch_signal_when_used():
    result = RelationalAnswerEvaluator.evaluate(
        text=(
            "**Direct Answer**: Reconciliation is possible in the coming months.\n\n"
            "**Main Astrological Evidence**: The 7th house and Moon are active, and Ashtakavarga shows endurance in the relationship houses while Sudarshana's Lagna/Moon/Sun tri-perspective confirms current activation.\n\n"
            "**Timing Windows**: A better phase appears within the next 3 to 5 months.\n\n"
            "FAQ_META: {\"category\":\"marriage\",\"canonical_question\":\"Reconciliation timing\"}"
        ),
        profile={"relation_family": "spouse_romantic", "event_topic": "reconciliation_return"},
        question="Will she come back and reconcile?",
        evidence_spine={
            "ashtakavarga_relational_evidence": {
                "available": True,
                "comparative": {"support": "both_supportive"},
            },
            "sudarshana_relational_evidence": {
                "available": True,
                "comparative": {"both_supportive": True, "native_current_support": "supportive"},
            },
        },
    )

    assert result["passed"] is True


def test_relational_answer_evaluator_rejects_unsupported_ashtakavarga_numbers():
    result = RelationalAnswerEvaluator.evaluate(
        text=(
            "**Direct Answer**: The marriage has pressure.\n\n"
            "**Main Astrological Evidence**: Ashtakavarga shows 27 SAV in the 7th house and only 1 bindu for Saturn, so delivery is strained.\n\n"
            "FAQ_META: {\"category\":\"marriage\",\"canonical_question\":\"Marriage behavior dynamics\"}"
        ),
        profile={"relation_family": "spouse_romantic", "event_topic": "general_relationship"},
        question="Tell me in detail what is Tarun's behaviour towards Deepika and Deepika's behaviour about Tarun",
        evidence_spine={
            "ashtakavarga_relational_evidence": {
                "available": False,
                "reason": "Ashtakavarga payload exists but usable house-indexed SAV/BAV rows were not available for these focus houses.",
            }
        },
    )

    assert result["passed"] is False
    assert "no_unsupported_av_numbers" in result["failed_checks"]


def test_relational_answer_evaluator_requires_behavior_texture_when_expected():
    result = RelationalAnswerEvaluator.evaluate(
        text=(
            "**Direct Answer**: He is intense and she reacts strongly.\n\n"
            "**Main Astrological Evidence**: Their relationship has pressure and karmic tension.\n\n"
            "FAQ_META: {\"category\":\"marriage\",\"canonical_question\":\"Marriage behavior dynamics\"}"
        ),
        profile={"relation_family": "spouse_romantic", "event_topic": "general_relationship"},
        question="Tell me in detail what is Tarun's behaviour towards Deepika and Deepika's behaviour about Tarun",
        evidence_spine={
            "relation_specific_evidence": {
                "sign_flavor_native": [{"sign": "Libra", "sign_flavor": "balancing, diplomatic"}],
                "sign_flavor_partner": [{"sign": "Virgo", "sign_flavor": "critical, analytical"}],
                "nakshatra_flavor_native": {"moon": {"nakshatra": "Swati", "flavor": "independent, peace-seeking"}},
                "nakshatra_flavor_partner": {"moon": {"nakshatra": "Chitra", "flavor": "crafted, exacting"}},
            }
        },
    )

    assert result["passed"] is False
    assert "behavior_sign_texture_present" in result["failed_checks"]
    assert "behavior_nakshatra_texture_present" in result["failed_checks"]


def test_relational_answer_evaluator_rejects_overprecise_timing_when_only_year_supported():
    result = RelationalAnswerEvaluator.evaluate(
        text=(
            "**Direct Answer**: Reconciliation is possible on 2026-05-04.\n\n"
            "**Main Astrological Evidence**: The dasha supports return.\n\n"
            "**Timing Windows**: May 2026 is the key month.\n\n"
            "FAQ_META: {\"category\":\"marriage\",\"canonical_question\":\"Reconciliation timing\"}"
        ),
        profile={"relation_family": "spouse_romantic", "event_topic": "reconciliation_return"},
        question="When will she come back?",
        evidence_spine={"timing_strategy": {"delivery_granularity": "year"}},
    )

    assert result["passed"] is False
    assert "timing_granularity_respected" in result["failed_checks"]
