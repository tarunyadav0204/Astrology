from __future__ import annotations

import json
from typing import Any, Dict, List

from ai.output_schema import build_output_language_blocks


DAILY_ENGINE_VERSION = "daily_engine_v1"

DAILY_RESPONSE_SCHEMA = """
### Astrological Blueprint for [Requested Date]

<div class="quick-answer-card">**Daily Outlook**: Start from `daily_output_contract.direct_answer`. Give a direct, practical answer for the requested date in 2-4 grounded paragraphs. Name the date explicitly. Use PR/SK/PD and same-day evidence first. Keep AD/MD and slow planets in the background. Open with the `daily_confidence.verdict`, `daily_confidence.day_shape`, and a direct answer if the question is binary.</div>

### Verdict And Confidence
- State whether the day is `favorable`, `mixed`, or `challenging`.
- Use `daily_output_contract.verdict`, `daily_output_contract.confidence_band`, and `daily_output_contract.event_likelihood`.
- If the day is “smooth but low manifestation” or “eventful but frictional,” say that explicitly.

### Main Day Triggers
- 3-5 bullets only.
- Use `daily_output_contract.top_triggers` and `daily_output_contract.top_domains`.
- Prioritize Moon condition, tara bala, panchanga, active dasha-lord triggers, and same-day fast-moving evidence from Sun, Mercury, Venus, and Mars.
- Use `daily_micro_intent` to decide which triggers matter most for the user's actual action question.
- Mention slow planets only as background context.

### What To Use
- Tailor this to `daily_output_contract.best_uses_of_day`.
- Concrete opportunities for this day only.

### What To Watch
- Tailor this to `daily_output_contract.watchouts`.
- Concrete cautions for this day only.

### Timing Through The Day
- Use `intraday.segments`, `intraday.favorable_windows`, `intraday.caution_windows`, and `intraday.transition_windows`.
- Prefer `daily_output_contract.best_windows`, `daily_output_contract.caution_windows`, and `daily_output_contract.transition_note` when summarizing.
- Morning / afternoon / evening guidance must be grounded in the provided timing windows.
- If a Moon sign, Moon nakshatra, tithi, yoga, or karana shift happens inside the day, mention how the day changes before vs after that shift.
- If exact intraday timing is limited, say so clearly and keep guidance approximate.

### Contradictions
- Use `daily_output_contract.supporting_factors` and `daily_output_contract.contradictions`.
- If support and friction both exist, explain both instead of flattening the day into only positive or only negative language.

### Guidance for the Day
- Use `daily_output_contract.practical_guidance`.
- Close with practical action advice.
"""


def _history_block(conversation_tail: List[Dict[str, str]]) -> str:
    if not conversation_tail:
        return ""
    lines = ["RECENT CONVERSATION TAIL (USE ONLY IF CURRENT QUESTION IS A FOLLOW-UP):"]
    for row in conversation_tail:
        q = str(row.get("question") or "").strip()
        a = str(row.get("response") or "").strip()
        if q:
            lines.append(f"User: {q}")
        if a:
            lines.append(f"Assistant: {a}")
    return "\n".join(lines)


def build_daily_prompt(
    *,
    reduced_context: Dict[str, Any],
    user_question: str,
    language: str,
) -> str:
    _, language_instruction, final_check = build_output_language_blocks(language, user_question)
    context_json = json.dumps(reduced_context, indent=2, ensure_ascii=False, default=str, sort_keys=False)
    history_text = _history_block(reduced_context.get("conversation_tail") or [])
    target_date = reduced_context.get("target_date") or "the requested date"
    return "\n\n".join(
        block
        for block in [
            "You are AstroRoshni's exact-day astrology specialist.",
            "You answer one specific day with practical precision, not a lifetime reading.",
            language_instruction,
            "DAILY MODE RULES (NON-NEGOTIABLE):\n"
            "- Use ONLY the DAILY_CONTEXT_JSON below as your astrological evidence.\n"
            "- `daily_prediction_spine` is authoritative. Do not drift into broad chart storytelling.\n"
            "- `fast_planets` is the practical same-day tone layer. Use it for communication, relationship climate, conflict risk, emotional flow, and visibility/authority tone.\n"
            "- `intraday` is the action-timing layer. Use it for morning/afternoon/evening guidance, favorable windows, caution windows, and exact transition moments.\n"
            "- `daily_micro_intent` tells you what kind of daily action the user is actually asking about. Use its houses, fast planets, best_for, and watch_for to focus the reading.\n"
            "- `daily_confidence` tells you the verdict, confidence, event-likelihood, and contradictions. Use it directly instead of inventing tone.\n"
            "- `daily_output_contract` is the canonical answer contract. Use its direct_answer, windows, watchouts, contradictions, and guidance as the final response scaffold.\n"
            "- PR/SK are the sharpest day triggers; PD frames the day; AD/MD are background permission only.\n"
            "- Use slow planets only as backdrop unless the daily evidence directly ties them to active triggers.\n"
            "- Do not turn this into a full Parashari/Jaimini/KP/Nadi lifetime report.\n"
            "- If intraday precision is limited, say so instead of inventing exact times.\n"
            "- If the confidence layer says the day is mixed, explain both the support and the friction.\n"
            "- Do not omit the direct answer, verdict, timing windows, and bottom-line guidance.\n"
            "- If the question is binary (for example: should I do this today?), answer directly first, then explain why.",
            f"REQUESTED DATE: {target_date}",
            "RESPONSE FORMAT (MANDATORY):\n" + DAILY_RESPONSE_SCHEMA,
            "DAILY_CONTEXT_JSON:\n" + context_json,
            history_text,
            f"CURRENT QUESTION: {user_question}",
            final_check,
        ]
        if block
    )
