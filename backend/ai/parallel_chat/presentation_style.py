"""Presentation-only instructions for parallel-chat merge writers.

Specialist branches always remain fully technical.  This module is deliberately
used only by final synthesis prompts so presentation choices cannot change the
calculated evidence, branch verdicts, timing windows, or confidence.
"""

from __future__ import annotations


def normalize_merge_response_style(value: object) -> str:
    """Only an explicit ``simple`` request opts into translated presentation.

    Every legacy value (including ``detailed`` and ``concise``) stays on the
    existing technical prompt path for backward compatibility.
    """

    return "simple" if str(value or "").strip().lower() == "simple" else "technical"


def build_simple_merge_instruction(response_style: object) -> str:
    """Return an additive instruction for Simple mode; Technical is untouched."""

    if normalize_merge_response_style(response_style) != "simple":
        return ""

    return """
SIMPLE PRESENTATION MODE — FINAL SYNTHESIS ONLY:
- The specialist branch outputs are already complete and authoritative. Preserve their verdict, rankings, dates, timing windows, contradictions, confidence, cautions, and practical implications exactly; do not recalculate or discard evidence.
- Answer the user's exact question first in warm, clear everyday language.
- Keep astrology visible without specialist jargon: name at least one evidence-bound planet when it materially explains the answer, then translate its effect into recognizable human behavior or a life outcome.
- Describe houses by their life meaning (for example, "the partnership area" or "the education area") instead of numbered houses.
- Do not expose chart codes, house numbers, lordship chains, degrees, padas, dignity labels, yoga names, divisional abbreviations, dasha-level abbreviations, KP sign-star-sub chains, bindu tables, or school-by-school technical narration in the visible answer.
- Translate technical evidence rather than replacing it with generic psychology. Every important conclusion must remain traceable to supplied branch evidence.
- Preserve the response depth appropriate to Standard or Premium and retain all user-relevant conclusions. Simple changes vocabulary and presentation, not analytical coverage.
- This block overrides earlier presentation or formatting rules that ask for Key Insights, Astrological Analysis, school-by-school sections, technical deep dives, or explicit specialist terminology. Those rules remain analysis guidance only and must not determine the visible format in Simple mode.
- Do not use visible headings named Parashari, Jaimini, Nadi, KP, Ashtakavarga, Sudarshana, Nakshatra Insights, Divisional Chart Analysis, or similar method labels.
- Keep required machine-readable metadata exactly as instructed elsewhere.
""".strip()


def build_simple_merge_depth_instruction(*, premium_analysis: bool) -> str:
    """Replace the legacy comprehensive/technical length rule in Simple mode."""

    tier = "Premium" if premium_analysis else "Standard"
    return f"""
SIMPLE {tier.upper()} RESPONSE DEPTH:
- Give a complete {tier} answer without turning it into a technical report.
- Lead with the direct conclusion. Then explain the 2-4 strongest evidence-backed planetary reasons in everyday language, what they mean in lived experience, any important timing or uncertainty, and one practical takeaway.
- Use short paragraphs and only a few descriptive headings when they genuinely improve readability.
- Do not pad the answer with branch-by-branch repetition. Premium may cover more relevant conclusions and nuance than Standard, but both must remain easy to understand.
""".strip()


def build_simple_merge_response_format() -> str:
    """User-visible answer shape for Simple parallel synthesis."""

    return """
SIMPLE ANSWER FORMAT (VISIBLE RESPONSE):
1. Start with the direct answer in 1-2 sentences.
2. Explain the strongest chart pattern through named planets and ordinary life language. A planet name is not enough—state the human effect it creates.
3. If the question asks when, include the supplied ranked timing windows and explain what changes in each one without exposing dasha abbreviations or calculation chains.
4. State the most important qualification, pressure, or uncertainty without alarmism.
5. End with a practical takeaway or one natural follow-up question when the surrounding contract permits it.
Do not output Key Insights, Astrological Analysis, method-by-method sections, degrees, bindu tables, KP steps, chart-code sections, or a glossary in the visible answer.
""".strip()


def build_simple_final_precedence_block(
    response_style: object,
    *,
    premium_analysis: bool,
) -> str:
    """Return the final prompt block that wins over evidence-shape contracts."""

    if normalize_merge_response_style(response_style) != "simple":
        return ""
    return "\n\n".join(
        [
            """FINAL SIMPLE PRESENTATION OVERRIDE — HIGHEST PRECEDENCE:
All preceding timing, ontology, specialist, and response-contract instructions control what evidence to analyze, which dates and rankings to preserve, and which conclusions are allowed. They do NOT control the visible answer layout or vocabulary. If an earlier block requests Executive Summary, Event Arc, Ranked Potential Windows, Technical Deep Dive, method sections, house numbers, dasha labels, divisional codes, bindus, degrees, or calculation terminology, translate that content into the Simple format below instead of displaying those technical structures. Never omit a supported timing window or qualification merely to simplify it.""",
            build_simple_merge_depth_instruction(premium_analysis=premium_analysis),
            build_simple_merge_response_format(),
            build_simple_merge_instruction(response_style),
        ]
    )


__all__ = [
    "build_simple_final_precedence_block",
    "build_simple_merge_depth_instruction",
    "build_simple_merge_instruction",
    "build_simple_merge_response_format",
    "normalize_merge_response_style",
]
