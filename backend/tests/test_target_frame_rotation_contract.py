from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from chat.instant_chat_pipeline import (  # noqa: E402
    TARGET_SUBJECTS,
    _build_instant_composer_context,
    _build_target_chart_context,
    _build_target_frame_foundation,
    _compact_context_for_speech,
    _fit_composer_brief,
    _multi_target_house_ledger,
    _slim_event_prediction_payload,
    _target_house_to_native_house,
)


def _native_snapshot() -> dict:
    # Put one uniquely named synthetic carrier in every native house by
    # cycling the nine supported planets. Individual mapping assertions use
    # the explicit house value, so duplicate names are unnecessary.
    return {
        "key_planets": {
            "Sun": {"sign": "Aries", "house": 1},
            "Moon": {"sign": "Taurus", "house": 2},
            "Mars": {"sign": "Gemini", "house": 3},
            "Mercury": {"sign": "Cancer", "house": 4},
            "Jupiter": {"sign": "Leo", "house": 5},
            "Venus": {"sign": "Virgo", "house": 6},
            "Saturn": {"sign": "Libra", "house": 7},
            "Rahu": {"sign": "Scorpio", "house": 8},
            "Ketu": {"sign": "Sagittarius", "house": 9},
        }
    }


@pytest.mark.parametrize("target_key", sorted(TARGET_SUBJECTS))
def test_every_supported_relation_has_bijective_house_rotation(target_key: str) -> None:
    configured = TARGET_SUBJECTS[target_key]
    anchor = configured["base_house"]
    ctx = _build_target_chart_context(
        {"ascendant": {"sign": "Cancer"}},
        _native_snapshot(),
        {"Jupiter": {"sign": "Gemini", "house_from_lagna": 12}},
        {"key": target_key, **configured},
    )

    mapped_native_houses = {
        _target_house_to_native_house(target_house, anchor)
        for target_house in range(1, 13)
    }
    assert mapped_native_houses == set(range(1, 13)), target_key
    for row in ctx["target_key_planets"].values():
        assert _target_house_to_native_house(row["house_from_target"], anchor) == row["native_house"]


@pytest.mark.parametrize("target_key", sorted(TARGET_SUBJECTS))
def test_every_target_house_ledger_keeps_native_and_relative_labels_distinct(target_key: str) -> None:
    configured = TARGET_SUBJECTS[target_key]
    ctx = _build_target_chart_context(
        {"ascendant": {"sign": "Cancer"}},
        _native_snapshot(),
        {},
        {"key": target_key, **configured},
    )
    ledger = _multi_target_house_ledger(ctx, list(range(1, 13)))
    assert len(ledger) == 12
    for row in ledger:
        assert row["corresponding_native_house"] == _target_house_to_native_house(
            row["house_from_target"], configured["base_house"]
        )


def test_target_frame_foundation_never_exposes_native_planet_house_as_target_house() -> None:
    husband = {"key": "husband", **TARGET_SUBJECTS["husband"]}
    ctx = _build_target_chart_context(
        {"ascendant": {"sign": "Cancer"}},
        {
            "key_planets": {
                "Mars": {"sign": "Leo", "house": 2, "nakshatra": {"name": "Magha"}},
                "Mercury": {"sign": "Aquarius", "house": 8},
                "Ketu": {"sign": "Aquarius", "house": 8},
            }
        },
        {},
        husband,
    )
    foundation = _build_target_frame_foundation(
        target_subject=husband,
        target_chart_context=ctx,
        focus_houses=[2, 6, 8],
    )
    assert foundation["planet_positions"]["Mars"]["house_from_target"] == 8
    assert "native_house" not in foundation["planet_positions"]["Mars"]
    husband_h2 = next(
        row for row in foundation["focus_house_ledger"] if row["house_from_target"] == 2
    )
    assert husband_h2["corresponding_native_house"] == 8
    assert husband_h2["occupants"] == ["Mercury", "Ketu"]


def test_slim_event_payload_preserves_target_frame_and_drops_native_fallbacks() -> None:
    husband = {"key": "husband", **TARGET_SUBJECTS["husband"]}
    native_planets = {
        "Mars": {"sign": 4, "sign_name": "Leo", "house": 2, "degree": 1.0},
        "Mercury": {"sign": 10, "sign_name": "Aquarius", "house": 8, "degree": 2.0},
        "Ketu": {"sign": 10, "sign_name": "Aquarius", "house": 8, "degree": 3.0},
    }
    native_snapshot = {
        "house_lordships": {"Moon": [1], "Sun": [2], "Saturn": [7, 8]},
        "key_planets": {
            name: {"sign": row["sign_name"], "house": row["house"], "degree": row["degree"]}
            for name, row in native_planets.items()
        },
    }
    ctx = _build_target_chart_context(
        {"ascendant": {"sign": "Cancer"}}, native_snapshot, {}, husband,
    )
    payload = _slim_event_prediction_payload(
        birth_summary={"name": "husband", "ascendant": {"sign": "Capricorn"}},
        natal_snapshot={
            "house_lordships": ctx["target_house_lordships"],
            "key_planets": ctx["target_key_planets"],
        },
        target_chart_context=ctx,
        current_dashas_levels={},
        current_transits_formatted={},
        instant_parashari={"focus_houses": [2], "forward_event_dasha_scan": {}, "horizon_dasha_segments": {}},
        normalized_evidence={"natal_promise": {"native_h2_mars": True}},
        period_window={"kind": "open_future", "start": "2026-09-08", "end": "2028-09-08"},
        category="family",
        question="shared habit timing",
        chart_data={"ascendant": 90.0, "planets": native_planets},
        house_lordships=native_snapshot["house_lordships"],
    )
    normalized = payload["normalized_evidence"]
    assert normalized["natal_promise"] == {}
    assert normalized["target_frame_foundation"]["planet_positions"]["Mars"]["house_from_target"] == 8
    assert payload["_user_evidence"]["natal_topic_factors"] == {}
    assert payload["instant_parashari"]["divisional_support"] == {}


@pytest.mark.parametrize(
    ("category", "answer_mode"),
    [
        ("career", "topic_reading"),
        ("health", "potential_capacity"),
        ("education", "topic_reading"),
        ("wealth", "topic_reading"),
        ("property", "comparison_choice"),
        ("foreign", "timing_window"),
        ("family", "event_prediction"),
        ("general", "factual_chart_lookup"),
    ],
)
def test_cross_domain_relative_composer_uses_only_target_frame(
    category: str, answer_mode: str,
) -> None:
    foundation = {
        "schema_version": "target-frame-foundation/v1",
        "target": {"key": "husband", "label": "husband", "native_anchor_house": 7},
        "focus_house_ledger": [{"house_from_target": 2, "corresponding_native_house": 8}],
    }
    composer = _build_instant_composer_context(
        {
            "birth_summary": {"name": "husband"},
            "intent_summary": {
                "category": category,
                "answer_mode": answer_mode,
                "target_subject": {"key": "husband", "label": "husband", "base_house": 7},
            },
            "normalized_evidence": {
                "target_frame_foundation": foundation,
                "natal_promise": {"native": True},
                "career_foundation": {"native": True},
                "wealth_foundation": {"native": True},
                "education_foundation": {"native": True},
                "home_foundation": {"native": True},
                "foreign_foundation": {"native": True},
                "special_natal_factors": [{"native": True}],
            },
        },
        {
            "query_plan": {
                "category": category,
                "answer_mode": answer_mode,
                "target_subject": {"key": "husband", "label": "husband", "base_house": 7},
            },
            "verdict": {"direction": "native-domain-verdict", "confidence": "high"},
            "answer_spec": {
                "career_contract": {"native": True},
                "career_answer_rules": {"native": True},
                "knowledge_graph_policy": {"live": True, "domain": category},
            },
            "user_derivation": {},
        },
    )
    assert composer["evidence"] == {"target_frame_foundation": foundation}
    assert composer["verdict"]["direction"] == "bounded_target_relative_indications"
    assert "knowledge_graph_policy" not in composer["answer_contract"]


def test_prompt_fitter_preserves_complete_target_frame_under_emergency_budget() -> None:
    foundation = {
        "schema_version": "target-frame-foundation/v1",
        "target": {"key": "husband", "native_anchor_house": 7},
        "house_mapping": [
            {"house_from_target": house, "corresponding_native_house": (house + 5) % 12 + 1}
            for house in range(1, 13)
        ],
        "focus_house_ledger": [
            {
                "house_from_target": 2,
                "corresponding_native_house": 8,
                "occupants": ["Mercury", "Ketu"],
            }
        ],
        "frame_rules": ["use the target frame"],
    }
    fitted = _fit_composer_brief(
        {
            "evidence": {
                "target_frame_foundation": foundation,
                "irrelevant": [{"large": "x" * 1000}] * 20,
            }
        },
        target_chars=500,
    )
    restored = fitted["evidence"]["target_frame_foundation"]
    assert len(restored["house_mapping"]) == 12
    assert restored["focus_house_ledger"][0]["corresponding_native_house"] == 8


def test_speech_compaction_preserves_target_frame_foundation() -> None:
    foundation = {
        "schema_version": "target-frame-foundation/v1",
        "target": {"key": "husband", "native_anchor_house": 7},
        "focus_house_ledger": [
            {"house_from_target": 2, "corresponding_native_house": 8}
        ],
    }
    compact = _compact_context_for_speech({
        "intent_summary": {"target_subject": {"key": "husband"}},
        "normalized_evidence": {"target_frame_foundation": foundation},
        "target_chart_context": {"key": "husband", "anchor_house": 7},
    })
    assert compact["normalized_evidence"]["target_frame_foundation"] == foundation


def test_prompt_fitter_keeps_multi_target_rows_separate() -> None:
    contexts = [
        {
            "target_subject": {"key": "husband"},
            "target_house_ledger": [
                {"house_from_target": 2, "corresponding_native_house": 8}
            ],
        },
        {
            "target_subject": {"key": "child"},
            "target_house_ledger": [
                {"house_from_target": 2, "corresponding_native_house": 6}
            ],
        },
    ]
    contract = {"answer_each_subject_separately": True}
    fitted = _fit_composer_brief({
        "evidence": {
            "multi_target_contexts": contexts,
            "multi_target_contract": contract,
            "irrelevant": [{"large": "x" * 1000}] * 20,
        }
    }, target_chars=500)
    evidence = fitted["evidence"]
    assert evidence["multi_target_contexts"] == contexts
    assert evidence["multi_target_contract"] == contract
