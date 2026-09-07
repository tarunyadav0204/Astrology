from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from calculators.chart_calculator import ChartCalculator  # noqa: E402
from chat.instant_chat_pipeline import (  # noqa: E402
    _RELATIVE_PROFILE_DIVISION,
    TARGET_SUBJECTS,
    _build_instant_composer_context,
    _build_instant_composer_prompt_v3,
    _build_person_profile_axes,
    _compact_relative_profile_evidence,
    _normalize_event_category,
    _relative_profile_answer_from_evidence,
    _validate_relative_profile_answer,
)


def _abc_chart():
    birth = SimpleNamespace(
        name="ABC",
        date="1980-04-02",
        time="14:55:00",
        latitude=29.2396596,
        longitude=75.8174505,
        timezone="UTC+5:30",
        place="Hisar, Haryana, India",
    )
    return ChartCalculator({}).calculate_chart(birth)


def test_father_profile_uses_h9_sun_and_d12_without_global_factor_leakage() -> None:
    profile = _compact_relative_profile_evidence(
        _abc_chart(),
        {"key": "father", "label": "father", "base_house": 9},
        {"key": "father", "label": "father", "anchor_house": 9},
    )

    assert _normalize_event_category("father") == "father"
    assert profile["evidence_complete"] is True
    assert profile["layers"]["d1_relative_anchor"]["native_anchor_house"] == 9
    assert profile["layers"]["d1_relative_anchor"]["lord"] == "Jupiter"
    assert profile["layers"]["natural_significator"]["planet"] == "Sun"
    assert profile["layers"]["natural_significator"]["native_house"] == 9
    assert profile["layers"]["divisional_confirmation"]["chart"] == "D12"

    context = {
        "birth_summary": {"name": "father", "ascendant": {"sign": "Pisces"}},
        "intent_summary": {
            "category": "father",
            "answer_mode": "relationship_person",
            "target_subject": {"key": "father", "label": "father", "base_house": 9},
        },
        "normalized_evidence": {"relative_profile_context": profile},
    }
    packet = {
        "query_plan": {
            "category": "father",
            "answer_mode": "relationship_person",
            "target_subject": {"key": "father", "label": "father", "base_house": 9},
        },
        "verdict": {"confidence": "medium"},
        "answer_spec": {"max_words": 180},
        "user_derivation": {
            "natal_promise": {
                "d1_house_factors": [{
                    "house": 2,
                    "special_support_notes": ["Mercury is Yogi lord for Virgo."],
                    "special_caution_notes": ["Mars is in Gandanta and rules a Dagdha sign."],
                }],
            },
        },
    }
    composer = _build_instant_composer_context(context, packet)
    prompt = _build_instant_composer_prompt_v3("Tell me about my father", composer, "english")

    assert set(composer["evidence"]) == {"relative_profile_context"}
    assert not composer.get("native")
    assert "Mercury is Yogi" not in prompt
    assert "Mars is in Gandanta" not in prompt
    assert "RELATIVE PROFILE EVIDENCE CHECK" in prompt


def test_rotated_person_profile_is_not_rotated_by_native_anchor_twice() -> None:
    target_context = {
        "key": "father",
        "target_house_lordships": {"Jupiter": [1, 10], "Mars": [2, 9]},
        "target_key_planets": {
            "Jupiter": {"sign": "Leo", "house": 6, "house_from_target": 6},
            "Mars": {"sign": "Leo", "house": 6, "house_from_target": 6},
            "Sun": {"sign": "Pisces", "house": 1, "house_from_target": 1},
        },
    }
    axes = _build_person_profile_axes(
        {"house_lordships": target_context["target_house_lordships"], "key_planets": target_context["target_key_planets"]},
        {},
        {"key": "father", "label": "father", "base_house": 9},
        target_context,
    )

    assert axes
    assert "key house is 1" in axes[0]
    assert "its lord is Jupiter" in axes[0]
    assert "key house is 9" not in " ".join(axes)


def test_relative_profile_validator_rejects_the_reported_failure_class() -> None:
    profile = _compact_relative_profile_evidence(
        _abc_chart(),
        {"key": "father", "label": "father", "base_house": 9},
        {"key": "father", "label": "father", "anchor_house": 9},
    )
    bad = (
        "Mercury, as Yogi lord for your Virgo ascendant, supports the family. "
        "Mars sits in your 9th house in Gandanta. The evidence is partial and D12 is unavailable."
    )
    errors = _validate_relative_profile_answer(bad, profile)

    assert any("global natal factors" in error for error in errors)
    assert any("ascendant frames" in error for error in errors)
    assert any("unsupported placement" in error for error in errors)
    assert any("D12" in error for error in errors)


def test_relative_profile_validator_rejects_wrong_aspect_origin_and_invented_psychology() -> None:
    profile = _compact_relative_profile_evidence(
        _abc_chart(),
        {"key": "father", "label": "father", "base_house": 9},
        {"key": "father", "label": "father", "anchor_house": 9},
    )
    bad = (
        "The chart indications here are limited and the confidence is modest. "
        "Mars aspects this 9th house from your 10th house, so love was shown through provision rather than words. "
        "In D12, Saturn adds structure. He was not always emotionally transparent and his approval carries weight."
    )
    errors = _validate_relative_profile_answer(bad, profile)

    assert any("understates" in error for error in errors)
    assert any("aspect origin" in error for error in errors)
    assert any("unsupported psychology" in error for error in errors)


def test_mother_in_law_renderer_cannot_invent_the_reported_hidden_psychology() -> None:
    profile = _compact_relative_profile_evidence(
        _abc_chart(),
        {"key": "mother_in_law", "label": "mother-in-law", "base_house": 10},
        {"key": "mother_in_law", "label": "mother-in-law", "anchor_house": 10},
    )
    answer = _relative_profile_answer_from_evidence(profile, technical=True)

    assert "derived anchor for your mother-in-law is your H10 in Aries" in answer
    assert "Mars is in your H2—H5 from your mother-in-law—in Leo" in answer
    assert "In D12, the same derived H10 falls in Pisces" in answer
    assert "The derived anchor contains Ketu" in answer
    assert "hidden motives" not in answer
    assert "easily overwhelmed" not in answer
    assert "emotionally" not in answer
    assert "warmth" not in answer
    assert "retrograde" not in answer
    assert _validate_relative_profile_answer(answer, profile) == []

    simple = _relative_profile_answer_from_evidence(profile, technical=False)
    assert "D1" not in simple
    assert "D12" not in simple
    assert " H10" not in simple


def test_reported_mother_in_law_failure_is_rejected_as_a_general_claim_class() -> None:
    profile = _compact_relative_profile_evidence(
        _abc_chart(),
        {"key": "mother_in_law", "label": "mother-in-law", "base_house": 10},
        {"key": "mother_in_law", "label": "mother-in-law", "anchor_house": 10},
    )
    bad = (
        "A clear, unified read isn't fully supported because the evidence points in different directions. "
        "Mars is retrograde, which turns that directness inward. In D12, Ketu adds detachment or inward focus. "
        "She is easily overwhelmed and her warmth is practical rather than emotional."
    )
    errors = _validate_relative_profile_answer(bad, profile)

    assert any("understates" in error for error in errors)
    assert any("unsupported psychology" in error for error in errors)


def test_one_renderer_contract_covers_every_supported_relative_target() -> None:
    chart = _abc_chart()
    for key in _RELATIVE_PROFILE_DIVISION:
        configured = TARGET_SUBJECTS[key]
        profile = _compact_relative_profile_evidence(
            chart,
            {"key": key, **configured},
            {"key": key, "label": configured["label"], "anchor_house": configured["base_house"]},
        )
        answer = _relative_profile_answer_from_evidence(profile, technical=True)

        assert profile["evidence_complete"] is True, key
        assert profile["layers"]["divisional_confirmation"]["chart"] in answer, key
        assert _validate_relative_profile_answer(answer, profile) == [], key
