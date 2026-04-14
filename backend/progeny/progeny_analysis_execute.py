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
    if request.analysis_focus == "parenting":
        focus_instruction = f"The user already has {request.children_count} children. Do NOT predict conception timing. Focus on parenting and child relationship guidance."
    elif request.analysis_focus == "next_child":
        focus_instruction = f"The user has {request.children_count} children and wants guidance for the next child timing and potential."
    else:
        focus_instruction = "Focus on first child promise, fertility support, and favorable timing windows."

    progeny = context.get("progeny_analysis", {})
    sphuta = progeny.get("fertility_sphuta", {})
    d7 = progeny.get("d7_analysis", {})
    timing_indicators = progeny.get("timing_indicators", [])
    dasha = context.get("current_dashas", {})

    return f"""
As an expert Vedic astrologer, analyze the birth chart for Progeny and Family Expansion.

USER SITUATION:
- Focus: {focus_instruction}
- Gender: {request.gender}
- Current Children: {request.children_count}
- Fertility Sphuta Type: {sphuta.get('type', 'unknown')}
- Fertility Sphuta Strength: {sphuta.get('strength', 'unknown')}

CHART ANALYSIS POINTS:
1. D7 Saptamsa:
   - Lagna Lord: {d7.get('d7_lagna_lord', 'unknown')}
   - 5th House Planets: {', '.join(d7.get('planets_in_d7_5th', []) or []) or 'Empty'}
   - Summary: {d7.get('summary', 'Not available')}
2. Timing Indicators: {', '.join(timing_indicators or []) or 'Not available'}
3. Current Dasha: {dasha.get('mahadasha', {}).get('planet', 'Unknown')} MD / {dasha.get('antardasha', {}).get('planet', 'Unknown')} AD

CRITICAL: You MUST respond with ONLY a JSON object.
{{
  "quick_answer": "Summary of progeny prospects and timing based on chart analysis.",
  "detailed_analysis": [
    {{
      "question": "What does my chart indicate about progeny and family expansion?",
      "answer": "Core progeny promise from D1 + D7 with chart-specific detail."
    }},
    {{
      "question": "Are there delays or obstacles and what are the likely reasons?",
      "answer": "Explain likely astrological reasons and whether they are temporary."
    }},
    {{
      "question": "When are the favorable periods for conception / family milestones?",
      "answer": "Use dasha and transit windows with practical timing guidance."
    }},
    {{
      "question": "What practical remedies and actions are supportive?",
      "answer": "Give realistic, compassionate, non-fatalistic remedies and guidance."
    }}
  ],
  "final_thoughts": "Supportive summary with practical next steps."
}}

ETHICAL RULES:
- Use supportive language.
- Avoid deterministic or harmful wording.
- No text outside JSON.
"""


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
                "detailed_analysis": [
                    {
                        "question": "What does my chart indicate about family expansion?",
                        "answer": ai_result.get("response", "Analysis completed successfully."),
                    }
                ],
                "final_thoughts": "Your chart has been analyzed for progeny prospects.",
            }
        else:
            raw_data = ai_result.get("data", {})
            detailed_analysis = []
            for item in raw_data.get("detailed_analysis", []):
                detailed_analysis.append(
                    {
                        "question": item.get("question", ""),
                        "answer": item.get("answer", ""),
                    }
                )
            parsed_response = {
                "quick_answer": raw_data.get("quick_answer", "Analysis completed successfully."),
                "detailed_analysis": detailed_analysis,
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
