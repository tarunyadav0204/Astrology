"""Shared async pipeline for career AI (CareerAIContextGenerator + StructuredAnalysisAnalyzer)."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.career_ai_context_generator import CareerAIContextGenerator
from ai.gemini_errors import transient_gemini_error, user_facing_gemini_error
from ai.parallel_chat.parallel_agent_payloads import (
    build_jaimini_agent_payload,
    build_nadi_agent_payload,
    build_parashari_agent_payload,
)
from ai.structured_analyzer import StructuredAnalysisAnalyzer
from context_agents.base import AgentContext

CAREER_STRUCTURED_QUESTION = """
You are an expert Vedic astrologer specializing in Career and Professional direction (Karma). Analyze the birth chart for Professional Success.

CRITICAL INPUT DATA TO ANALYZE (Priority Order):
1. **Amatyakaraka (AmK) in D10 (Dasamsa):** MOST IMPORTANT - Check 'd10_detailed.amatyakaraka_analysis'.
   - AmK in 10th of D10 = MASSIVE SUCCESS/CEO Potential.
   - AmK in 1st/5th/9th = Smooth steady growth.
   - AmK in 6th/8th/12th = Success through struggle, research, or foreign lands.
2. **Modern Career Indicators (Rahu/Ketu in D10):**
   - **CRITICAL:** If Rahu is in D10 Kendra (1,4,7,10) or Upachaya (3,6,11), predict TECHNOLOGY, AI, CODING, AVIATION, or FOREIGN MNC careers.
   - Ketu in D10 Kendra/Upachaya = Coding, Research, Mathematics, Precision work.
3. **Agentic Career Evidence Spine:**
   - Use `career_evidence.parashari.px.career` first for mode, work-function scores, ranked function tags, visibility, dominant houses, and active dasha/house links.
   - Use `career_evidence.parashari.px.dx.career` for D10/Karkamsa/AL divisional confirmation and current dasha support.
   - Use `career_evidence.jaimini.jx.career` for AmK, Karkamsa/KL, AL, image/status, and Chara dasha support.
   - Use `career_evidence.nadi.nx.career` for dominant Nadi grahas, career signatures, work-style tags, and age activation.

IMPORTANT: You MUST respond with EXACTLY this JSON structure. Do not add extra fields.
{
  "quick_answer": "A sharp 3-4 sentence summary naming the top 1-2 career directions, likely work function, employment/business tendency, visibility level, and next timing focus.",
  "detailed_analysis": [
    {
      "question": "What is my true professional purpose and work function?",
      "answer": "Analyze Amatyakaraka, 10th house/lord, D10, Karkamsa, and career_evidence.parashari.px.career.fn. State the concrete work function: builder, analyst, advisor, communicator, manager, creator, healer/service provider, researcher, trader, operator, or technical specialist.",
      "key_points": ["Purpose point 1", "Work-function point 2"],
      "astrological_basis": "AmK, 10th house/lord, D10, Karkamsa, career function tags"
    },
    {
      "question": "What specific industry, niche, or role cluster suits me best?",
      "answer": "Rank the top 3 fields only. Use 10th lord nakshatra, D10, AmK, dominant planets, career_evidence.nadi.nx.career.tags/sig, and career_evidence.parashari.px.career.fn. Avoid vague baskets; explain why each field fits.",
      "key_points": ["Field 1", "Field 2"],
      "astrological_basis": "Nakshatra, D10, Nadi signatures, dominant career grahas"
    },
    {
      "question": "What exactly will I do day-to-day?",
      "answer": "Translate chart evidence into practical day-to-day tasks: coding/building, analysis, selling, teaching, managing people, operations, design, strategy, healing/service, research, finance, consulting, public-facing work, or backend/private work. Use career_evidence.parashari.px.career.work and mode.",
      "key_points": ["Task pattern 1", "Task pattern 2"],
      "astrological_basis": "6th/10th/2nd/11th patterns, Mercury/Saturn/Mars/Venus/Jupiter/Rahu emphasis"
    },
    {
      "question": "Should I choose job, business, freelancing, or leadership?",
      "answer": "Use 6th for employment/service, 7th for business/public dealing, 10th for authority, 11th for networks/gains, and career_evidence.parashari.px.career.mode/work. Give a ranked recommendation, not a generic yes to everything.",
      "key_points": ["Income model point 1", "Work setup point 2"],
      "astrological_basis": "6th/7th/10th/11th houses and D10"
    },
    {
      "question": "Status vs. reality: will I gain visibility, authority, or mostly work hard behind the scenes?",
      "answer": "Compare AL, A10/Rajya Pada, 10th house, Sun/Saturn, D10, and career_evidence.jaimini.jx.career.img plus career_evidence.parashari.px.career.vis. Separate real capability from public recognition.",
      "key_points": ["Visibility point 1", "Authority point 2"],
      "astrological_basis": "AL, A10/Rajya Pada, Sun, Saturn, D10"
    },
    {
      "question": "Government, corporate, startup, foreign/MNC, or independent path?",
      "answer": "Use Sun/Mars/Saturn for government/authority, Mercury/Venus for commerce/design, Rahu for tech/foreign/startups, Jupiter for advisory/education, and D10 confirmation. Rank likely ecosystems and state what to avoid.",
      "key_points": ["Ecosystem point 1", "Avoidance point 2"],
      "astrological_basis": "Planetary significators, Rahu/Ketu in D10, house patterns"
    },
    {
      "question": "What are my strongest professional skills and unfair advantages?",
      "answer": "Identify 3-5 unique talents using strongest career grahas, nakshatra_career_analysis, d10_detailed, career_yogas, and career_evidence.nadi.nx.career.sig. Make these actionable as skills to build or monetize.",
      "key_points": ["Skill 1", "Skill 2"],
      "astrological_basis": "Strong grahas, nakshatras, yogas, D10"
    },
    {
      "question": "Where can career instability, blocks, or wrong choices come from?",
      "answer": "Analyze 8th/12th/6th pressure, weak 10th lord, afflicted AmK/Saturn, D10 dusthana placements, and negative evidence in career_evidence.parashari.px.career.dom/work. State concrete risks: wrong industry, burnout, politics, frequent switches, hidden work, foreign displacement, or delayed recognition.",
      "key_points": ["Risk point 1", "Correction point 2"],
      "astrological_basis": "Dusthana pressure, 10th lord dignity, Saturn/AmK, D10"
    },
    {
      "question": "When is my next big career breakthrough or change window?",
      "answer": "Use current Vimshottari dasha first, then career_timing, career_evidence.parashari.px.D/HI/TR, divisional current support in px.dx.career, and career_evidence.jaimini.jx.career.md/ad. Give windows as supportive/mixed/weak; do not promise guaranteed events.",
      "key_points": ["Timing window 1", "Timing window 2"],
      "astrological_basis": "Dasha, transits, D10/Karkamsa activation"
    },
    {
      "question": "What action plan should I follow now?",
      "answer": "Give a 90-day and 12-month action plan aligned with the top field, work function, skill gaps, timing, and risk factors. The advice must be practical and chart-specific.",
      "key_points": ["90-day action", "12-month action"],
      "astrological_basis": "Full career synthesis"
    }
  ],
  "final_thoughts": "One empowering concluding paragraph summarizing the career trajectory.",
  "follow_up_questions": [
    "📅 When will I get a promotion?",
    "💼 Is a startup suitable for me?",
    "✈️ Chances of working abroad?",
    "💰 When will my income peak?"
  ]
}

CRITICAL RULES:
1. Response must be ONLY valid JSON.
2. Use EXACTLY the field names shown above.
3. Include exactly 10 questions in detailed_analysis array.
4. Use ** for bold text in JSON strings where needed.
5. Be realistic and specific.
6. Rank likely fields; do not list more than 3 top fields as equal recommendations.
7. Every answer must separate at least one of: aptitude, field selection, work function, ecosystem, visibility/status, income model, risk, or timing.
8. Use `career_evidence` when available; it is the compact evidence spine from the agentic chat system.
"""


def career_birth_hash(request: Any) -> str:
    chart_id = getattr(request, 'chart_id', None)
    if chart_id:
        return f"chart:{chart_id}"
    return hashlib.md5(f"{request.date}_{request.time}_{request.place}".encode()).hexdigest()


def career_birth_hash_legacy(request: Any) -> str:
    return hashlib.md5(f"{request.date}_{request.time}_{request.place}".encode()).hexdigest()


def ensure_ai_career_insights_table(conn: Any, execute_fn: Any) -> None:
    execute_fn(
        conn,
        """
        CREATE TABLE IF NOT EXISTS ai_career_insights (
            id SERIAL PRIMARY KEY,
            userid INTEGER NOT NULL DEFAULT 0,
            birth_hash TEXT NOT NULL,
            insights_data TEXT,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(userid, birth_hash)
        )
        """,
    )


def get_cached_career(userid: int, birth_hash: str, get_conn: Any, execute_fn: Any) -> Any:
    with get_conn() as conn:
        ensure_ai_career_insights_table(conn, execute_fn)
        cur = execute_fn(
            conn,
            """
            SELECT insights_data
            FROM ai_career_insights
            WHERE userid = %s AND birth_hash = %s
            """,
            (userid, birth_hash),
        )
        row = cur.fetchone()
    return json.loads(row[0]) if row else None


def attach_career_agentic_context(context: Dict[str, Any], birth_data: Dict[str, Any]) -> Dict[str, Any]:
    """Attach compact branch evidence used by the agentic chat career flow."""
    agent_ctx = AgentContext(
        birth_data=birth_data,
        user_question="Career Analysis",
        intent_result={"category": "career", "divisional_charts": ["D1", "D9", "D10", "Karkamsa"]},
        precomputed_static=context,
        precomputed_dynamic=context,
    )
    evidence: Dict[str, Any] = {}
    builders = {
        "parashari": build_parashari_agent_payload,
        "jaimini": build_jaimini_agent_payload,
        "nadi": build_nadi_agent_payload,
    }
    for name, builder in builders.items():
        try:
            payload = builder(agent_ctx, "Career Analysis")
            if name == "parashari":
                evidence[name] = {"px": payload.get("px")}
            elif name == "jaimini":
                evidence[name] = {"jx": payload.get("jx")}
            elif name == "nadi":
                evidence[name] = {"nx": payload.get("nx")}
        except Exception as exc:
            evidence[name] = {"error": str(exc)[:300]}
    context["career_evidence"] = evidence
    return context


async def execute_career_analysis(
    userid: int,
    request: Any,
    career_cost: int,
    *,
    credit_service: Any,
    get_conn: Any,
    execute_fn: Any,
) -> Dict[str, Any]:
    birth_hash = career_birth_hash(request)
    legacy_birth_hash = career_birth_hash_legacy(request)

    if not request.force_regenerate:
        cached = get_cached_career(userid, birth_hash, get_conn, execute_fn)
        if not cached and legacy_birth_hash != birth_hash:
            cached = get_cached_career(userid, legacy_birth_hash, get_conn, execute_fn)
        if cached:
            out = dict(cached)
            out["cached"] = True
            return {"ok": True, "career_insights": out, "cached": True}

    birth_data = {
        "name": request.name,
        "date": request.date,
        "time": request.time,
        "place": request.place,
        "latitude": request.latitude or 28.6139,
        "longitude": request.longitude or 77.2090,
        "timezone": request.timezone or "UTC+0",
        "gender": request.gender,
    }

    context_generator = CareerAIContextGenerator()
    context = await asyncio.get_event_loop().run_in_executor(
        None,
        context_generator.build_career_context,
        birth_data,
    )
    context = attach_career_agentic_context(context, birth_data)

    analyzer = StructuredAnalysisAnalyzer()
    max_retries = 3
    retry_delay = 10
    ai_result = None
    lang = request.language or "english"

    for attempt in range(max_retries):
        try:
            print(f"🔄 Career: attempt {attempt + 1}/{max_retries} — Structured API")
            ai_result = await analyzer.generate_structured_report(CAREER_STRUCTURED_QUESTION, context, lang)
        except Exception as api_error:
            ai_result = {"success": False, "error": str(api_error)}
            print(f"⚠️ Career API attempt {attempt + 1} raised: {ai_result['error'][:500]}")

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
                detailed_analysis.append(
                    {
                        "question": item.get("question", ""),
                        "answer": item.get("answer", ""),
                        "key_points": item.get("key_points", []),
                        "astrological_basis": item.get("astrological_basis", ""),
                    }
                )
            parsed_response = {
                "quick_answer": raw_data.get("quick_answer", "Analysis completed successfully."),
                "detailed_analysis": detailed_analysis,
                "final_thoughts": raw_data.get("final_thoughts", ""),
                "follow_up_questions": raw_data.get("follow_up_questions", []),
                "terms": ai_result.get("terms", []),
                "glossary": ai_result.get("glossary", {}),
            }

        career_insights = {
            "analysis": parsed_response,
            "terms": ai_result.get("terms", []),
            "glossary": ai_result.get("glossary", {}),
            "enhanced_context": True,
            "questions_covered": len(parsed_response.get("detailed_analysis", [])),
            "context_type": "structured_analyzer",
            "generated_at": datetime.now().isoformat(),
        }

        if not credit_service.spend_credits(
            userid,
            career_cost,
            "career_analysis",
            f"Career analysis for {birth_data.get('name', 'user')}",
        ):
            return {"ok": False, "error": "Credit deduction failed"}

        with get_conn() as conn:
            ensure_ai_career_insights_table(conn, execute_fn)
            execute_fn(
                conn,
                """
                INSERT INTO ai_career_insights (userid, birth_hash, insights_data, updated_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (userid, birth_hash) DO UPDATE SET
                    insights_data = EXCLUDED.insights_data,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (userid, birth_hash, json.dumps(career_insights)),
            )
            conn.commit()

        return {"ok": True, "career_insights": career_insights, "cached": False}
    except Exception as e:
        print(f"❌ Career response processing failed: {e}")
        return {"ok": False, "error": str(e)}
