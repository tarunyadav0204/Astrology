"""Remedies belong only on explicit Remedies CTA follow-ups."""

from utils.query_context import clamp_remedy_modes_on_intent, is_remedy_followup_request
from ai.output_schema import TEMPLATE_DEEP_DIVE, get_response_schema_for_mode


def test_is_remedy_followup_request_requires_cta_flags():
    assert not is_remedy_followup_request({"answer_mode": "remedy_action"})
    assert not is_remedy_followup_request({"query_context": {}})
    assert is_remedy_followup_request({"query_context": {"remedy_followup": True}})
    assert is_remedy_followup_request({"query_context": {"open_remedy": True}})
    assert is_remedy_followup_request({"query_context": {"follow_up_type": "remedy_action"}})
    assert is_remedy_followup_request({"follow_up_type": "remedy_followup", "query_context": {}})


def test_clamp_remedy_modes_demotes_without_cta():
    result = {
        "mode": "RECOMMEND_REMEDY_FOR_PROBLEM",
        "answer_mode": "remedy_action",
        "query_context": {},
    }
    clamp_remedy_modes_on_intent(result, "I have anxiety, what can I do?")
    assert result["answer_mode"] == "problem_diagnosis"
    assert result["mode"] == "ANALYZE_ROOT_CAUSE"


def test_clamp_remedy_modes_keeps_cta():
    result = {
        "mode": "ANALYZE_TOPIC_POTENTIAL",
        "answer_mode": "topic_reading",
        "query_context": {"remedy_followup": True, "follow_up_type": "remedy_action"},
    }
    clamp_remedy_modes_on_intent(result, "Remedies please")
    assert result["answer_mode"] == "remedy_action"
    assert result["mode"] == "RECOMMEND_REMEDY_FOR_PROBLEM"


def test_deep_dive_template_forbids_inline_remedies():
    assert "NO INLINE REMEDIES" in TEMPLATE_DEEP_DIVE
    assert "Analysis + Remedies" not in TEMPLATE_DEEP_DIVE
    assert "wellness/remedy playbook" in TEMPLATE_DEEP_DIVE
    schema = get_response_schema_for_mode("ANALYZE_TOPIC_POTENTIAL")
    assert "NO INLINE REMEDIES" in schema


def test_no_inline_remedy_plan_rule_forbids_lifestyle_playbooks():
    from utils.query_context import NO_INLINE_REMEDY_PLAN_RULE

    assert "yoga" in NO_INLINE_REMEDY_PLAN_RULE.lower()
    assert "pranayama" in NO_INLINE_REMEDY_PLAN_RULE.lower()
    assert "NEXT_ACTION_META" in NO_INLINE_REMEDY_PLAN_RULE


def test_ensure_remedy_cta_next_action_fallback_for_health():
    from utils.query_context import ensure_remedy_cta_next_action

    out = ensure_remedy_cta_next_action(
        None,
        answer_mode="topic_reading",
        category="health",
        question="How is my health?",
        remedy_followup_active=False,
    )
    assert out is not None
    assert out["type"] == "remedy"
    assert out["source"] == "fallback"
    assert out["title"]
    assert out["reason"]
    assert out["follow_up_questions"][0]


def test_ensure_remedy_cta_hindi_fallback():
    from utils.query_context import ensure_remedy_cta_next_action

    out = ensure_remedy_cta_next_action(
        None,
        answer_mode="topic_reading",
        category="health",
        question="मेरी सेहत कैसी रहेगी?",
        remedy_followup_active=False,
        language="hindi",
    )
    assert out is not None
    assert "उपाय" in out["follow_up_questions"][0] or "देखें" in out["follow_up_questions"][0]


def test_complete_remedy_fomo_preserves_llm_copy():
    from utils.query_context import ensure_remedy_cta_next_action

    out = ensure_remedy_cta_next_action(
        {
            "type": "remedy",
            "title": "Saturn-Rahu दबाव अभी चरम पर",
            "reason": "इस खिड़की में उपाय ज़्यादा असरदार रहते हैं।",
            "follow_up_questions": ["उपाय देखें"],
            "source": "merge",
        },
        answer_mode="topic_reading",
        category="health",
        question="मेरी सेहत?",
        remedy_followup_active=False,
    )
    assert out["title"] == "Saturn-Rahu दबाव अभी चरम पर"
    assert out["follow_up_questions"][0] == "उपाय देखें"

    from utils.query_context import ensure_remedy_cta_next_action

    assert ensure_remedy_cta_next_action(
        None,
        answer_mode="remedy_action",
        category="health",
        question="Remedies please",
        remedy_followup_active=True,
    ) is None


def test_ensure_remedy_cta_strips_llm_remedy_card_in_remedy_mode():
    from utils.query_context import ensure_remedy_cta_next_action

    llm_remedy_card = {
        "type": "remedy",
        "title": "More remedies",
        "reason": "You should act now",
        "follow_up_questions": ["Show remedies"],
    }
    assert ensure_remedy_cta_next_action(
        llm_remedy_card,
        answer_mode="remedy_action",
        category="health",
        question="Generate remedy-only reading",
        remedy_followup_active=True,
    ) is None
    assert ensure_remedy_cta_next_action(
        llm_remedy_card,
        answer_mode="remedy_action",
        category="health",
        question="Generate remedy-only reading",
        remedy_followup_active=False,
    )["type"] == "remedy"


def test_answer_mode_alone_does_not_hide_normal_remedy_card():
    from utils.query_context import ensure_remedy_cta_next_action, is_in_remedy_delivery_mode

    assert not is_in_remedy_delivery_mode(
        remedy_followup_active=False,
        answer_mode="remedy_action",
    )
    action = ensure_remedy_cta_next_action(
        None,
        answer_mode="remedy_action",
        category="health",
        question="How is my health?",
        remedy_followup_active=False,
    )
    assert action is not None
    assert action["type"] == "remedy"


def test_parse_next_action_with_faq_after():
    from ai.response_parser import ResponseParser

    text = (
        "Answer body here.\n"
        'NEXT_ACTION_META: {"type":"remedy","title":"Health remedies","reason":"Pressure themes","confidence":"high","follow_up_questions":["Generate remedies"],"source":"merge"}\n'
        'FAQ_META: {"category":"health","canonical_question":"Health outlook"}'
    )
    cleaned, faq = ResponseParser.parse_faq_metadata(text)
    cleaned2, action = ResponseParser.parse_next_action_metadata(cleaned)
    assert faq is not None
    assert action is not None
    assert action["type"] == "remedy"
    assert "NEXT_ACTION_META" not in cleaned2


def test_recommend_remedy_mode_uses_remedial_template():
    schema = get_response_schema_for_mode("RECOMMEND_REMEDY_FOR_PROBLEM")
    assert "Guidance and Remedies" in schema or "Remedy layers" in schema


def test_resolve_remedy_followup_from_chain_text():
    from utils.query_context import is_remedy_chain_question, resolve_remedy_followup_active

    chain = (
        "Generate a remedy-only reading.\n"
        "Issue: Health & Vitality Remedies\n"
        "Do not give a general chart reading. Give practical remedies only."
    )
    assert is_remedy_chain_question(chain)
    assert resolve_remedy_followup_active({"query_context": {}}, combined_question=f"All {chain}")


def test_fetal_sex_gate_skips_short_clarification_picks():
    from ai.fetal_sex_query_classifier import is_short_clarification_reply

    assert is_short_clarification_reply("All")
    assert is_short_clarification_reply("Type B")
    assert not is_short_clarification_reply("Will my baby be a boy or girl?")


def test_resolve_remedy_followup_from_answer_mode():
    from utils.query_context import resolve_remedy_followup_active

    # answer_mode alone must NOT suppress the Remedies CTA on normal questions
    assert not resolve_remedy_followup_active({"answer_mode": "remedy_action"})
    assert not resolve_remedy_followup_active({"answer_mode": "topic_reading"})
    assert resolve_remedy_followup_active(
        {"query_context": {"remedy_followup": True}, "answer_mode": "remedy_action"}
    )


def test_strip_inline_remedy_sections_keeps_cta_eligible():
    from utils.query_context import (
        apply_normal_answer_remedy_guards,
        strip_inline_remedy_sections_from_content,
    )

    sample = (
        "### Focused Interpretation\n"
        "Saturn pressure is active in the health houses.\n"
        "Remedy layers\n"
        "\n"
        "Core planetary remedy: Worship Lord Hanuman on Saturdays.\n"
        "Nakshatra remedy (Ashlesha/Magha): Perform Pitru Tarpan.\n"
        "Biological / Vriksha: Plant a Banyan tree.\n"
        "Mantra / Sound: Chant Om Ram Rahave Namah.\n"
        "Dietary: Avoid spicy foods.\n"
        "What to avoid\n"
        "Avoid extreme physical exertion.\n"
    )
    stripped = strip_inline_remedy_sections_from_content(sample)
    assert "Remedy layers" not in stripped
    assert "Core planetary remedy" not in stripped
    assert "Hanuman" not in stripped
    assert "Focused Interpretation" in stripped
    assert "Saturn pressure" in stripped

    cleaned, action, _ = apply_normal_answer_remedy_guards(
        content=sample,
        next_action=None,
        answer_mode="topic_reading",
        category="health",
        question="How is my health?",
        remedy_followup_active=False,
    )
    assert "Remedy layers" not in cleaned
    assert action is not None
    assert action["type"] == "remedy"


def test_strip_remedy_followup_prompts_from_content():
    from utils.query_context import apply_remedy_mode_delivery_guards, strip_remedy_followup_prompts_from_content

    sample_with_questions_heading = (
        "### Final Verdict\n"
        "Done.\n"
        "### Follow-up questions\n"
        "- Tell me more about Ganesha remedies\n"
    )
    stripped_heading = strip_remedy_followup_prompts_from_content(sample_with_questions_heading)
    assert "Follow-up" not in stripped_heading
    assert "Ganesha" not in stripped_heading

    sample = (
        "### Final Verdict\n"
        "Close with remedy summary.\n"
        "### Follow-up\n"
        "- Tell me more about Ganesha remedies for Gandanta\n"
        "- Provide a detailed guide for the Banyan tree ritual\n"
        '<div class="follow-up-questions">\n'
        "- Detailed Ritual Guide\n"
        "- Tell me more about Ganesha remedies for Gandanta\n"
        "</div>"
    )
    stripped = strip_remedy_followup_prompts_from_content(sample)
    assert "Follow-up" not in stripped
    assert "Tell me more about Ganesha" not in stripped
    assert "Final Verdict" in stripped

    cleaned, action, followups = apply_remedy_mode_delivery_guards(
        content=sample,
        next_action={"type": "remedy", "title": "More", "follow_up_questions": ["x"]},
        follow_up_questions=["Tell me more"],
        remedy_followup_active=True,
        answer_mode="remedy_action",
    )
    assert action is None
    assert followups == []
    assert "Follow-up" not in cleaned


def test_remedy_click_delivery_clears_second_card_end_to_end():
    from utils.query_context import (
        apply_normal_answer_remedy_guards,
        resolve_remedy_followup_active,
    )

    intent = {
        "answer_mode": "remedy_action",
        "query_context": {
            "follow_up_type": "remedy_action",
            "remedy_followup": True,
            "open_remedy": True,
        },
    }
    explicit = resolve_remedy_followup_active(intent)
    assert explicit
    content, action, followups = apply_normal_answer_remedy_guards(
        content="### Remedy layers\n- Chant the mantra daily.",
        next_action={
            "type": "remedy",
            "title": "More remedies",
            "reason": "Continue deeper",
            "follow_up_questions": ["Open more"],
        },
        follow_up_questions=["Open more"],
        answer_mode="remedy_action",
        category="health",
        question="Show my remedies",
        remedy_followup_active=explicit,
    )
    assert "Chant the mantra" in content
    assert action is None
    assert followups == []
