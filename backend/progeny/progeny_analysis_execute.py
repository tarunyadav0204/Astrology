"""Shared async pipeline for progeny AI (ProgenyAIContextGenerator + StructuredAnalysisAnalyzer)."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.gemini_errors import transient_gemini_error, user_facing_gemini_error
from ai.progeny_ai_context_generator import ProgenyAIContextGenerator
from ai.structured_analyzer import StructuredAnalysisAnalyzer


def progeny_birth_hash(request: Any) -> str:
    chart_id = getattr(request, 'chart_id', None)
    if chart_id:
        focus = getattr(request, 'analysis_focus', 'first_child')
        children_count = getattr(request, 'children_count', 0)
        return f"chart:{chart_id}:progeny:{focus}:{children_count}"
    # Include focus + children_count to avoid cross-focus cache collisions.
    return hashlib.md5(
        f"{request.date}_{request.time}_{request.place}_{request.gender}_{request.analysis_focus}_{request.children_count}_progeny".encode()
    ).hexdigest()


def progeny_birth_hash_legacy(request: Any) -> str:
    return hashlib.md5(
        f"{request.date}_{request.time}_{request.place}_{request.gender}_{request.analysis_focus}_{request.children_count}_progeny".encode()
    ).hexdigest()


def ensure_ai_progeny_insights_table(conn: Any, execute_fn: Any) -> None:
    execute_fn(
        conn,
        """
        CREATE TABLE IF NOT EXISTS ai_progeny_insights (
            id SERIAL PRIMARY KEY,
            userid INTEGER NOT NULL DEFAULT 0,
            birth_hash TEXT NOT NULL,
            insights_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(userid, birth_hash)
        )
        """,
    )


def get_cached_progeny(userid: int, birth_hash: str, get_conn: Any, execute_fn: Any) -> Any:
    with get_conn() as conn:
        ensure_ai_progeny_insights_table(conn, execute_fn)
        cur = execute_fn(
            conn,
            """
            SELECT insights_data
            FROM ai_progeny_insights
            WHERE userid = %s AND birth_hash = %s
            """,
            (userid, birth_hash),
        )
        row = cur.fetchone()
    return json.loads(row[0]) if row else None


def _build_progeny_question(request: Any, context: Dict[str, Any]) -> str:
    analysis_focus = request.analysis_focus or "first_child"
    if analysis_focus == "parenting":
        focus_instruction = (
            f"The user already has {request.children_count} children. Do NOT predict conception timing. "
            "Focus on parenting style, child relationship, support periods, and family harmony."
        )
    elif analysis_focus == "next_child":
        focus_instruction = (
            f"The user currently has {request.children_count} children. Focus only on timing and promise for the next child. "
            "Do not reframe the question as first-child analysis."
        )
    else:
        focus_instruction = (
            "Focus on first-child promise, supportive timing windows, and any obstacles or remedies. "
            "Keep the language compassionate and non-fatalistic."
        )

    progeny = context.get("progeny_analysis", {})
    sphuta = progeny.get("fertility_sphuta", {})
    d7 = progeny.get("d7_analysis", {})
    timing_indicators = progeny.get("timing_indicators", [])
    dasha = context.get("current_dashas", {})
    evidence = context.get("progeny_evidence", {})
    timing_summary = context.get("current_timing_summary", {})
    guardrails = evidence.get("safety_rules", []) or context.get("interpretative_guidelines", {}).get("safety_rule", "")

    return f"""
As an expert Vedic astrologer, analyze the birth chart for Progeny and Family Expansion.

USER SITUATION:
- Focus: {focus_instruction}
- Gender: {request.gender}
- Current Children: {request.children_count}
- Fertility Sphuta Type: {sphuta.get('type', 'unknown')}
- Fertility Sphuta Strength: {sphuta.get('strength', 'unknown')}
- Current Dasha Summary: {timing_summary.get('summary', 'Not available')}
- Progeny Promise Rating: {evidence.get('promise', {}).get('rating', 'Unknown')}
- Progeny Promise Notes: {', '.join(evidence.get('promise', {}).get('notes', [])) or 'Not available'}

CHART ANALYSIS POINTS:
1. D1 Promise:
   - 5th House Sign: {progeny.get('d1_fifth_house', {}).get('sign', 'unknown')}
   - 5th House Lord: {progeny.get('d1_fifth_house', {}).get('lord', 'unknown')}
   - 5th House Planets: {', '.join(progeny.get('d1_fifth_house', {}).get('planets', []) or []) or 'Empty'}
   - Malefic Pressure: {progeny.get('d1_fifth_house', {}).get('has_malefics', False)}
2. D7 Saptamsa:
   - Lagna Lord: {d7.get('d7_lagna_lord', 'unknown')}
   - 5th House Planets: {', '.join(d7.get('planets_in_d7_5th', []) or []) or 'Empty'}
   - 9th House Planets: {', '.join(d7.get('planets_in_d7_9th', []) or []) or 'Empty'}
   - 2nd House Planets: {', '.join(d7.get('planets_in_d7_2nd', []) or []) or 'Empty'}
   - Summary: {d7.get('summary', 'Not available')}
   - Support Level: {d7.get('support_level', 'Unknown')}
3. Jupiter Status:
   - Sign: {progeny.get('jupiter_status', {}).get('sign', 'unknown')}
   - House: {progeny.get('jupiter_status', {}).get('house', 'unknown')}
   - Status: {progeny.get('jupiter_status', {}).get('status', 'unknown')}
4. Timing Indicators: {', '.join(timing_indicators or []) or 'Not available'}
5. Current Dasha: {dasha.get('mahadasha', {}).get('planet', 'Unknown')} MD / {dasha.get('antardasha', {}).get('planet', 'Unknown')} AD
6. Focus Guardrail: {focus_instruction}
7. Safety Rules: {guardrails if isinstance(guardrails, str) else '; '.join(guardrails)}

CRITICAL: You MUST respond with ONLY a JSON object.
{{
  "analysis_mode": "{analysis_focus}",
  "promise_strength": "Strong, Moderate, or Sensitive",
  "quick_answer": "A 3-4 sentence summary of the progeny promise, timing, and focus-specific takeaway.",
  "detailed_analysis": [
    {{
      "question": "What is the core progeny promise in the chart?",
      "answer": "Explain the D1 5th house, D7 support, Jupiter, and fertility sphuta together."
    }},
    {{
      "question": "What does the D1 5th house say about children?",
      "answer": "Explain the 5th house sign, lord, occupants, and whether it is protected or pressured."
    }},
    {{
      "question": "What does D7 say about progeny strength?",
      "answer": "Use the D7 lagna lord, 5th house, 9th house, and 2nd house together."
    }},
    {{
      "question": "What is Jupiter and fertility sphuta showing?",
      "answer": "Explain Jupiter's role, fertility sphuta polarity, and whether the body/seed-field symbolism is supportive."
    }},
    {{
      "question": "What current timing or activation is present?",
      "answer": "Use the active Mahadasha, Antardasha, and any matching timing indicators."
    }},
    {{
      "question": "Which timing windows look most supportive?",
      "answer": "Give the best near-term windows and explain why they are better than other periods."
    }},
    {{
      "question": "What are the main support factors?",
      "answer": "List the strongest supportive factors first, in priority order."
    }},
    {{
      "question": "What are the main obstacles or delays?",
      "answer": "List the main cautions, delays, or mixed indications without being fatalistic."
    }},
    {{
      "question": "How should this be read for the selected focus?",
      "answer": "If first_child, talk about first-child promise. If next_child, talk only about next-child timing. If parenting, focus on existing children and do not predict conception timing."
    }},
    {{
      "question": "What practical remedies and actions are supportive?",
      "answer": "Give realistic, compassionate, non-fatalistic remedies and family-supportive actions."
    }}
  ],
  "timing_windows": [],
  "obstacles_and_support": [],
  "parenting_guidance": "",
  "final_thoughts": "Supportive summary with practical next steps."
}}

ETHICAL RULES:
- Use supportive language.
- Avoid deterministic or harmful wording.
- Fertility and parenting are guidance topics, not medical diagnosis.
- If the focus is parenting, do not mention conception timing.
- No text outside JSON.
"""


def _merge_or_pad_progeny_questions(
    detailed_analysis: Any,
    context: Dict[str, Any],
    request: Any,
) -> list:
    canonical_questions = [
        "What is the core progeny promise in the chart?",
        "What does the D1 5th house say about children?",
        "What does D7 say about progeny strength?",
        "What is Jupiter and fertility sphuta showing?",
        "What current timing or activation is present?",
        "Which timing windows look most supportive?",
        "What are the main support factors?",
        "What are the main obstacles or delays?",
        "How should this be read for the selected focus?",
        "What practical remedies and actions are supportive?",
    ]

    merged = []
    existing = {}
    for item in detailed_analysis or []:
        if isinstance(item, dict):
            q = (item.get("question") or "").strip()
            if q:
                existing[q] = item.get("answer", "")

    timing_summary = context.get("current_timing_summary", {})
    progeny = context.get("progeny_analysis", {})
    evidence = context.get("progeny_evidence", {})
    d1 = progeny.get("d1_fifth_house", {})
    d7 = progeny.get("d7_analysis", {})
    jupiter = progeny.get("jupiter_status", {})
    sphuta = progeny.get("fertility_sphuta", {})

    fallback_answers = {
        "What is the core progeny promise in the chart?": (
            f"Promise rating: {evidence.get('promise', {}).get('rating', 'Moderate')}. "
            f"D1 5th house is in {d1.get('sign', 'unknown')} with lord {d1.get('lord', 'unknown')}. "
            f"D7 support level is {d7.get('support_level', 'Unknown')}. "
            f"Jupiter is {jupiter.get('status', 'unknown')}. "
            f"Fertility sphuta is {sphuta.get('strength', 'unknown')}."
        ),
        "What does the D1 5th house say about children?": (
            f"The D1 5th house sits in {d1.get('sign', 'unknown')} and is ruled by {d1.get('lord', 'unknown')}. "
            f"Planets present: {', '.join(d1.get('planets', []) or []) or 'none'}. "
            f"Malefic pressure: {d1.get('has_malefics', False)}."
        ),
        "What does D7 say about progeny strength?": (
            f"D7 lagna lord is {d7.get('d7_lagna_lord', 'unknown')}. "
            f"D7 5th house planets: {', '.join(d7.get('planets_in_d7_5th', []) or []) or 'none'}. "
            f"D7 9th house planets: {', '.join(d7.get('planets_in_d7_9th', []) or []) or 'none'}. "
            f"D7 2nd house planets: {', '.join(d7.get('planets_in_d7_2nd', []) or []) or 'none'}. "
            f"Support level: {d7.get('support_level', 'Unknown')}."
        ),
        "What is Jupiter and fertility sphuta showing?": (
            f"Jupiter is in {jupiter.get('sign', 'unknown')} / house {jupiter.get('house', 'unknown')} "
            f"and is {jupiter.get('status', 'unknown')}. "
            f"Fertility sphuta is {sphuta.get('type', 'unknown')} with strength {sphuta.get('strength', 'unknown')}."
        ),
        "What current timing or activation is present?": (
            timing_summary.get("summary")
            or "Current dasha timing is available but no compact summary was generated."
        ),
        "Which timing windows look most supportive?": (
            "Use the current Mahadasha/Antardasha plus any listed timing indicators to rank the most supportive near-term windows."
        ),
        "What are the main support factors?": (
            f"Supportive factors include: {', '.join(evidence.get('promise', {}).get('notes', [])[:3]) or 'No compact support notes available.'}"
        ),
        "What are the main obstacles or delays?": (
            "Identify only the strongest delay indicators, and keep the language mixed or sensitive rather than fatalistic."
        ),
        "How should this be read for the selected focus?": (
            f"Focus is {getattr(request, 'analysis_focus', 'first_child')}. "
            "If parenting, do not predict conception timing; if next_child, keep the answer limited to the next child; if first_child, stay on first-child promise and timing."
        ),
        "What practical remedies and actions are supportive?": (
            "Offer realistic remedies, family-supportive actions, and health-conscious but non-medical suggestions."
        ),
    }

    for question in canonical_questions:
        answer = existing.get(question) or fallback_answers.get(question, "")
        merged.append({"question": question, "answer": answer})

    return merged


async def execute_progeny_analysis(
    userid: int,
    request: Any,
    analysis_cost: int,
    *,
    credit_service: Any,
    get_conn: Any,
    execute_fn: Any,
) -> Dict[str, Any]:
    if not request.gender or not request.gender.strip():
        return {
            "ok": False,
            "error": "GENDER_REQUIRED: Gender is required for progeny analysis. Please update your profile to continue.",
        }

    birth_hash = progeny_birth_hash(request)
    legacy_birth_hash = progeny_birth_hash_legacy(request)

    if not request.force_regenerate:
        cached = get_cached_progeny(userid, birth_hash, get_conn, execute_fn)
        if not cached and legacy_birth_hash != birth_hash:
            cached = get_cached_progeny(userid, legacy_birth_hash, get_conn, execute_fn)
        if cached:
            out = dict(cached)
            out["cached"] = True
            return {"ok": True, "progeny_insights": out, "cached": True}

    birth_data = {
        "name": request.name,
        "date": request.date,
        "time": request.time,
        "place": request.place,
        "latitude": request.latitude or 28.6139,
        "longitude": request.longitude or 77.2090,
        "timezone": request.timezone or "UTC+0",
        "gender": request.gender,
        "analysis_focus": request.analysis_focus,
        "children_count": request.children_count,
    }

    context_generator = ProgenyAIContextGenerator()
    context = await asyncio.get_event_loop().run_in_executor(
        None,
        context_generator.build_progeny_context,
        birth_data,
    )

    # Add dynamic transit/dasha context like legacy path.
    try:
        from chat.chat_context_builder import ChatContextBuilder

        chat_builder = ChatContextBuilder()
        current_year = datetime.now().year
        chat_builder._build_static_context(birth_data)
        transit_context = chat_builder._build_dynamic_context(
            birth_data,
            "progeny timing analysis",
            None,
            {"start_year": current_year, "end_year": current_year + 1},
        )
        if isinstance(transit_context, dict):
            if transit_context.get("transit_activations"):
                context["transit_activations"] = transit_context["transit_activations"]
            if transit_context.get("current_dashas"):
                context["current_dashas"] = transit_context["current_dashas"]
    except Exception as transit_error:
        print(f"⚠️ Progeny transit context failed, continuing: {transit_error}")

    question = _build_progeny_question(request, context)
    analyzer = StructuredAnalysisAnalyzer()

    max_retries = 3
    retry_delay = 10
    ai_result = None
    lang = request.language or "english"

    for attempt in range(max_retries):
        try:
            print(f"🔄 Progeny: attempt {attempt + 1}/{max_retries} — Structured API")
            ai_result = await analyzer.generate_structured_report(question, context, lang)
        except Exception as api_error:
            ai_result = {"success": False, "error": str(api_error)}
            print(f"⚠️ Progeny API attempt {attempt + 1} raised: {ai_result['error'][:500]}")

        if ai_result and ai_result.get("success"):
            break

        err_raw = (ai_result or {}).get("error", "") or ""
        if transient_gemini_error(err_raw) and attempt < max_retries - 1:
            wait_time = retry_delay * (2**attempt)
            print(f"⏳ Transient Gemini failure, retrying in {wait_time}s...")
            await asyncio.sleep(wait_time)
            continue
        break

    if not ai_result or not ai_result.get("success"):
        err = user_facing_gemini_error((ai_result or {}).get("error", "") or "No response from AI")
        return {"ok": False, "error": err}

    try:
        if ai_result.get("is_raw"):
            parsed_response = {
                "quick_answer": "Analysis completed successfully.",
                "analysis_mode": request.analysis_focus,
                "promise_strength": "Moderate",
                "detailed_analysis": _merge_or_pad_progeny_questions(
                    [
                        {
                            "question": "What is the core progeny promise in the chart?",
                            "answer": ai_result.get("response", "Analysis completed successfully."),
                        }
                    ],
                    context,
                    request,
                ),
                "final_thoughts": "Your chart has been analyzed for progeny prospects.",
            }
        else:
            raw_data = ai_result.get("data", {})
            parsed_response = {
                "quick_answer": raw_data.get("quick_answer", "Analysis completed successfully."),
                "analysis_mode": raw_data.get("analysis_mode", request.analysis_focus),
                "promise_strength": raw_data.get("promise_strength", "Moderate"),
                "detailed_analysis": _merge_or_pad_progeny_questions(
                    raw_data.get("detailed_analysis", []),
                    context,
                    request,
                ),
                "timing_windows": raw_data.get("timing_windows", []),
                "obstacles_and_support": raw_data.get("obstacles_and_support", []),
                "parenting_guidance": raw_data.get("parenting_guidance", ""),
                "final_thoughts": raw_data.get("final_thoughts", ""),
            }

        progeny_insights = {
            "analysis": {
                **parsed_response,
                "terms": ai_result.get("terms", []),
                "glossary": ai_result.get("glossary", {}),
            },
            "terms": ai_result.get("terms", []),
            "glossary": ai_result.get("glossary", {}),
            "enhanced_context": True,
            "questions_covered": len(parsed_response.get("detailed_analysis", [])),
            "context_type": "structured_analyzer",
            "generated_at": datetime.now().isoformat(),
        }

        if not credit_service.spend_credits(
            userid,
            analysis_cost,
            "progeny_analysis",
            f"Progeny for {request.name or 'User'}",
        ):
            return {"ok": False, "error": "Credit deduction failed"}

        with get_conn() as conn:
            ensure_ai_progeny_insights_table(conn, execute_fn)
            execute_fn(
                conn,
                """
                INSERT INTO ai_progeny_insights (userid, birth_hash, insights_data, updated_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (userid, birth_hash)
                DO UPDATE SET insights_data = EXCLUDED.insights_data,
                              updated_at = EXCLUDED.updated_at
                """,
                (userid, birth_hash, json.dumps(progeny_insights)),
            )
            conn.commit()

        return {"ok": True, "progeny_insights": progeny_insights, "cached": False}
    except Exception as e:
        print(f"❌ Progeny response processing failed: {e}")
        return {"ok": False, "error": str(e)}
