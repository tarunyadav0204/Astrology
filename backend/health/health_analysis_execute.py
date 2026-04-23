"""
Shared async pipeline for health AI (HealthAIContextGenerator + StructuredAnalysisAnalyzer).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import sys
from datetime import date, datetime
from typing import Any, Dict

import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.gemini_errors import transient_gemini_error, user_facing_gemini_error
from ai.health_ai_context_generator import HealthAIContextGenerator
from ai.structured_analyzer import StructuredAnalysisAnalyzer
from context_agents.base import AgentContext
from context_agents.registry import build_agent

HEALTH_STRUCTURED_QUESTION = """
You are an expert Vedic astrologer. Analyze the birth chart for Health and Wellness.

IMPORTANT: You MUST respond with EXACTLY this JSON structure. Do not add extra fields or change field names.

{
  "quick_answer": "Brief, useful health summary based on chart analysis. Mention this is astrological wellness guidance, not medical diagnosis.",
  "detailed_analysis": [
    {
      "question": "What is my core constitution and vitality pattern?",
      "answer": "Analyze Lagna, Lagna lord, Sun, Moon, elemental/dosha balance, and health_agent.ct / health_agent.eb if available",
      "key_points": ["Point 1", "Point 2"],
      "astrological_basis": "Planetary positions and aspects"
    },
    {
      "question": "What are my primary health vulnerabilities?",
      "answer": "Analyze 1st/6th/8th/12th houses, their lords, afflicting grahas, D30 confirmation, and health_agent.ph / health_agent.hh if available",
      "key_points": ["Period 1", "Period 2"],
      "astrological_basis": "Dasha periods and planetary transits"
    },
    {
      "question": "What body parts need special attention?",
      "answer": "Use signs, houses, afflicted planets, body_parts, mrityu_bhaga_analysis, and health_agent.ph.dhatu/body-system cues",
      "key_points": ["Body part 1", "Body part 2"],
      "astrological_basis": "House and sign correlations"
    },
    {
      "question": "How is my mental and emotional health?",
      "answer": "Analyze Moon, Mercury, 4th house, 12th house/sleep, Rahu/Saturn influence, and current activation",
      "key_points": ["Mental aspect 1", "Mental aspect 2"],
      "astrological_basis": "Moon and Mercury positions"
    },
    {
      "question": "How are digestion, metabolism, and recovery capacity shown?",
      "answer": "Analyze 5th house/agni, Sun/Mars/Jupiter, 6th-house immunity, D9 resilience, and any supportive yogas",
      "key_points": ["Agni point 1", "Recovery point 2"],
      "astrological_basis": "5th house, vitality, and recovery indicators"
    },
    {
      "question": "Is the pattern more acute, chronic, sensitivity-based, or preventive?",
      "answer": "Classify the pattern from health_agent.ph, health_agent.hh, health_agent.yg, 6th/8th/12th, Saturn, Mars, Rahu, and Ketu. Acute = Mars/6th flare; chronic = Saturn/8th; sensitivity/irregularity = Rahu/Ketu/Moon/Mercury; preventive = stronger vitality with manageable triggers.",
      "key_points": ["Pattern point 1", "Pattern point 2"],
      "astrological_basis": "Disease pattern indicators"
    },
    {
      "question": "When should I be extra cautious about health?",
      "answer": "Use current dashas first, then transits and health_agent.rw ranked risk windows if present. Give time windows, preferably months or date ranges when available; do not overclaim certainty.",
      "key_points": ["Period 1", "Period 2"],
      "astrological_basis": "Dasha periods, transit triggers, and health windows"
    },
    {
      "question": "What does D30/Trimsamsa add to the health reading?",
      "answer": "Explain D30 disease/misfortune refinement if available. Compare D1 visible vulnerability with D9 resilience and D30 confirmation. If missing, say so.",
      "key_points": ["D30 point 1", "D9/D1 point 2"],
      "astrological_basis": "D1-D9-D30 synthesis"
    },
    {
      "question": "What lifestyle and preventive guidance fits my chart?",
      "answer": "Give non-medical, practical wellness suggestions tied to dosha, planets, sleep, stress, digestion, movement, and routine. Avoid treatment instructions.",
      "key_points": ["Remedy 1", "Remedy 2"],
      "astrological_basis": "Planetary strengthening methods"
    },
    {
      "question": "What should I not ignore?",
      "answer": "State safety boundaries: astrology cannot diagnose; if symptoms, pain, mental distress, or medical concerns exist, consult qualified professionals. Frame chart indicators as areas for proactive monitoring.",
      "key_points": ["Safety point 1", "Safety point 2"],
      "astrological_basis": "Health houses and current activation"
    }
  ],
  "final_thoughts": "Balanced health outlook and path forward",
  "follow_up_questions": [
    "🏥 How to improve my immunity?",
    "🧘 Best yoga/exercise for my body type?",
    "🌿 What diet and routine suits my constitution?",
    "📅 Which months require extra caution?",
    "🧠 How is my stress and sleep pattern?",
    "🪬 Which remedies support my weak health planets?"
  ]
}

CRITICAL RULES:
1. Response must be ONLY valid JSON - no extra text
2. Use EXACTLY the field names shown above
3. Include exactly 10 questions in detailed_analysis array
4. Always mention this is astrological guidance, not medical advice
5. Use ** for bold text in JSON strings
6. Do NOT diagnose disease, prescribe treatment, or tell the user to avoid medical care
7. If a specific disease/symptom is not named in the user input/context, speak in body-system and vulnerability language only
8. Use the `health_agent` block as the evidence spine when available, especially health_agent.hs, health_agent.ct, health_agent.ph, health_agent.hh, health_agent.rw, and health_agent.d30
"""


def health_birth_hash(request: Any) -> str:
    chart_id = getattr(request, 'chart_id', None)
    if chart_id:
        return f"chart:{chart_id}"
    return hashlib.md5(f"{request.date}_{request.time}_{request.place}".encode()).hexdigest()


def health_birth_hash_legacy(request: Any) -> str:
    return hashlib.md5(f"{request.date}_{request.time}_{request.place}".encode()).hexdigest()


def ensure_ai_health_insights_table(conn: Any, execute_fn: Any) -> None:
    execute_fn(
        conn,
        """
        CREATE TABLE IF NOT EXISTS ai_health_insights (
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


def get_cached_health(userid: int, birth_hash: str, get_conn: Any, execute_fn: Any) -> Any:
    with get_conn() as conn:
        ensure_ai_health_insights_table(conn, execute_fn)
        cur = execute_fn(
            conn,
            """
            SELECT insights_data
            FROM ai_health_insights
            WHERE userid = %s AND birth_hash = %s
            """,
            (userid, birth_hash),
        )
        row = cur.fetchone()
    return json.loads(row[0]) if row else None


def store_health_cache(userid: int, birth_hash: str, health_insights: Dict, get_conn: Any, execute_fn: Any) -> None:
    with get_conn() as conn:
        ensure_ai_health_insights_table(conn, execute_fn)
        execute_fn(
            conn,
            """
            INSERT INTO ai_health_insights (userid, birth_hash, insights_data, updated_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (userid, birth_hash)
            DO UPDATE SET insights_data = EXCLUDED.insights_data,
                          updated_at = EXCLUDED.updated_at
            """,
            (userid, birth_hash, json.dumps(health_insights)),
        )
        conn.commit()


def attach_health_agent_context(context: Dict[str, Any], birth_data: Dict[str, Any]) -> Dict[str, Any]:
    """Attach the compact health context-agent block used by agentic chat."""
    try:
        context["health_agent"] = build_agent(
            "health",
            AgentContext(
                birth_data=birth_data,
                user_question="Health & Wellness Analysis",
                intent_result={"category": "health", "divisional_charts": ["D1", "D9", "D30"]},
                precomputed_static=context,
                precomputed_dynamic=context,
            ),
        )
    except Exception as exc:
        context["health_agent"] = {"a": "health", "error": str(exc)[:300]}
    return context


async def execute_health_analysis(
    userid: int,
    request: Any,
    health_cost: int,
    *,
    credit_service: Any,
    get_conn: Any,
    execute_fn: Any,
) -> Dict[str, Any]:
    """
    Returns:
      { "ok": True, "health_insights": {...}, "cached": bool }
      { "ok": False, "error": str }
    """
    birth_hash = health_birth_hash(request)
    legacy_birth_hash = health_birth_hash_legacy(request)

    if not request.force_regenerate:
        cached = get_cached_health(userid, birth_hash, get_conn, execute_fn)
        if not cached and legacy_birth_hash != birth_hash:
            cached = get_cached_health(userid, legacy_birth_hash, get_conn, execute_fn)
        if cached:
            out = dict(cached)
            out["cached"] = True
            return {"ok": True, "health_insights": out, "cached": True}

    birth_data = {
        "name": request.name,
        "date": request.date,
        "time": request.time,
        "place": request.place,
        "latitude": request.latitude or 28.6139,
        "longitude": request.longitude or 77.2090,
        "timezone": request.timezone or "UTC+0",
        "gender": request.gender,
        "current_year": date.today().year,
    }

    health_context_generator = HealthAIContextGenerator()
    context = await asyncio.get_event_loop().run_in_executor(
        None,
        health_context_generator.build_health_context,
        birth_data,
    )
    context = attach_health_agent_context(context, birth_data)

    analyzer = StructuredAnalysisAnalyzer()
    max_retries = 3
    retry_delay = 10
    ai_result = None
    lang = request.language or "english"

    for attempt in range(max_retries):
        try:
            print(f"🔄 Health: attempt {attempt + 1}/{max_retries} — Structured API")
            ai_result = await analyzer.generate_structured_report(
                HEALTH_STRUCTURED_QUESTION,
                context,
                lang,
            )
        except Exception as api_error:
            ai_result = {"success": False, "error": str(api_error)}
            print(f"⚠️ Health API attempt {attempt + 1} raised: {ai_result['error'][:500]}")

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
                "detailed_analysis": [],
                "final_thoughts": "Analysis provided in detailed format.",
                "follow_up_questions": [],
            }
        else:
            raw_data = ai_result.get("data", {})
            detailed_analysis = []
            for item in raw_data.get("detailed_analysis", []):
                detailed_analysis.append({
                    "question": item.get("question", ""),
                    "answer": item.get("answer", ""),
                    "key_points": item.get("key_points", []),
                    "astrological_basis": item.get("astrological_basis", ""),
                })
            parsed_response = {
                "quick_answer": raw_data.get("quick_answer", "Analysis completed successfully."),
                "detailed_analysis": detailed_analysis,
                "final_thoughts": raw_data.get("final_thoughts", ""),
                "follow_up_questions": raw_data.get("follow_up_questions", []),
                "terms": ai_result.get("terms", []),
                "glossary": ai_result.get("glossary", {}),
            }

        detailed_analysis = []
        for item in parsed_response.get("detailed_analysis", []):
            detailed_analysis.append({
                "question": item.get("question", ""),
                "answer": item.get("answer", ""),
                "key_points": item.get("key_points", []),
                "astrological_basis": item.get("astrological_basis", ""),
            })

        formatted_response = {
            "quick_answer": parsed_response.get("quick_answer", "Analysis completed successfully."),
            "detailed_analysis": detailed_analysis,
            "final_thoughts": parsed_response.get("final_thoughts", ""),
            "follow_up_questions": parsed_response.get("follow_up_questions", []),
            "terms": ai_result.get("terms", []),
            "glossary": ai_result.get("glossary", {}),
        }

        health_insights = {
            "analysis": formatted_response,
            "terms": ai_result.get("terms", []),
            "glossary": ai_result.get("glossary", {}),
            "enhanced_context": True,
            "advanced_calculations": {
                "mrityu_bhaga": True,
                "badhaka_analysis": True,
                "d30_trimsamsa": True,
                "functional_malefics": True,
            },
            "questions_covered": len(detailed_analysis),
            "context_type": "structured_analyzer",
            "generated_at": datetime.now().isoformat(),
        }

        if not credit_service.spend_credits(
            userid,
            health_cost,
            "health_analysis",
            f"Health analysis for {birth_data.get('name', 'user')}",
        ):
            return {"ok": False, "error": "Credit deduction failed"}

        try:
            with get_conn() as conn:
                ensure_ai_health_insights_table(conn, execute_fn)
                execute_fn(
                    conn,
                    """
                    INSERT INTO ai_health_insights (userid, birth_hash, insights_data, updated_at)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (userid, birth_hash)
                    DO UPDATE SET insights_data = EXCLUDED.insights_data,
                                  updated_at = EXCLUDED.updated_at
                    """,
                    (userid, birth_hash, json.dumps(health_insights)),
                )
                conn.commit()
            print("💾 Health analysis cached successfully")
        except Exception as cache_error:
            print(f"⚠️ Failed to cache health analysis: {cache_error}")

        return {"ok": True, "health_insights": health_insights, "cached": False}
    except Exception as e:
        print(f"❌ Health response processing failed: {e}")
        return {"ok": False, "error": str(e)}
