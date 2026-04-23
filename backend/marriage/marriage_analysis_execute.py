"""Shared async pipeline for marriage AI (MarriageAIContextGenerator + StructuredAnalysisAnalyzer)."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sys
from datetime import date, datetime
from typing import Any, Dict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.gemini_errors import transient_gemini_error, user_facing_gemini_error
from ai.marriage_ai_context_generator import MarriageAIContextGenerator
from ai.parallel_chat.parallel_agent_payloads import (
    build_jaimini_agent_payload,
    build_nadi_agent_payload,
    build_parashari_agent_payload,
)
from ai.structured_analyzer import StructuredAnalysisAnalyzer
from context_agents.base import AgentContext

MARRIAGE_STRUCTURED_QUESTION = """
As an expert Vedic astrologer, analyze the birth chart for Relationship and Marriage Destiny.

The user's marital status may be in `birth_details.marital_status`.
- If marital_status is married, already_married, divorced, separated, widowed, remarried, or engaged: DO NOT frame the report as "when will I get married?" Focus on current bond quality, continuity, repair, second-marriage/remarriage themes if relevant, and future relationship phases.
- If marital_status is single/unmarried or explicitly unknown: you may discuss future marriage timing, but still call it a relationship/marriage milestone rather than assuming the user has never had a serious relationship.
- If marital_status is missing/unknown: use neutral lifecycle wording that works for both unmarried and married users.

CRITICAL: You MUST respond with ONLY a JSON object. NO other text.
{
  "quick_answer": "A precise relationship/marriage lifecycle summary separating promise, current phase/timing, manifestation quality, and continuity/stability.",
  "detailed_analysis": [
    {
      "question": "What is the core relationship and marriage promise in my chart?",
      "answer": "Judge relationship/marriage promise from D1 7th house/lord, Venus/Jupiter, 2/7/11 materialization houses, D9 confirmation, and marriage_evidence.parashari.px.relationship.mode/mat/fr. Do not confuse attraction, wedding, and durable partnership.",
      "key_points": ["Promise point 1", "Promise point 2"],
      "astrological_basis": "D1, D9, 7th lord, karakas, and materialization houses"
    },
    {
      "question": "What relationship or marriage lifecycle phases are active next?",
      "answer": "Use Vimshottari dasha first, then marriage_timing.future_marriage_transits, then marriage_evidence.parashari.px.D/HI/TR and marriage_evidence.jaimini.jx.relationship.md/ad. If the user is married or status is unknown, do not assume first-marriage timing; describe activation as relationship milestones, commitment decisions, harmony tests, repair windows, family expansion, or partnership maturation as evidence allows. If clearly unmarried, distinguish romance, proposal, legal marriage, and stable married life.",
      "key_points": ["Timing window 1", "Timing window 2"],
      "astrological_basis": "Dasha authority, double transit theory, and Jaimini Chara support"
    },
    {
      "question": "What is the personality and nature of my partner?",
      "answer": "Describe spouse traits from D1 7th sign/lord, planets in/aspecting 7th, Darakaraka, Venus/Jupiter, and D9 Navamsa. If evidence conflicts, separate outer spouse traits from inner/mature partner traits.",
      "key_points": ["Partner trait 1", "Partner trait 2"],
      "astrological_basis": "7th house, Darakaraka, karakas, and D9"
    },
    {
      "question": "Is my destiny inclined towards Love or Traditional connection?",
      "answer": "Analyze 5th-7th connection, Venus/Mars/Rahu influence, family houses 2/4, and Jaimini A7 for embodied relationship manifestation. Be concrete about love marriage, arranged/traditional support, family involvement, or unconventional patterns.",
      "key_points": ["Relationship path point 1", "Relationship path point 2"],
      "astrological_basis": "5th-7th connection, A7 manifestation, family houses"
    },
    {
      "question": "How strong is marital harmony and compatibility after marriage?",
      "answer": "Analyze D9, 2nd from UL/7th continuity, 8th-house intimacy/adjustment, Venus condition, and marriage_evidence.jaimini.jx.relationship.ul2_pp/ct. Separate wedding possibility from post-marriage stability.",
      "key_points": ["Harmony point 1", "Continuity point 2"],
      "astrological_basis": "D9, UL continuity, 2nd/8th houses, Venus"
    },
    {
      "question": "Are there doshas, delays, or friction factors?",
      "answer": "Analyze Mangal Dosha/cancellations if present, Saturn delay, Rahu/Ketu irregularity, 6/8/12 pressure, and marriage_evidence.parashari.px.relationship.fr. Name negative evidence directly without fear language.",
      "key_points": ["Friction point 1", "Cancellation/support point 2"],
      "astrological_basis": "Mars, Saturn, nodes, 6/8/12, dosha cancellation"
    },
    {
      "question": "What does Navamsa (D9) reveal about marriage maturity?",
      "answer": "Use marriage_charts.d9_navamsa and marriage_evidence.parashari.px.dx.relationship. Compare D1 root with D9 fruit; identify whether maturity improves, weakens, or complicates the marriage promise.",
      "key_points": ["D9 point 1", "D1 vs D9 point 2"],
      "astrological_basis": "D1-D9 root/fruit synthesis"
    },
    {
      "question": "What does Jaimini show through DK, UL, and A7?",
      "answer": "Use marriage_evidence.jaimini.jx.relationship: DK = partner nature, UL = formal alliance/continuity, A7 = lived relationship manifestation. If GK or malefics affect A7/UL, state the real-world friction.",
      "key_points": ["DK/UL/A7 point 1", "Manifestation point 2"],
      "astrological_basis": "Darakaraka, Upapada Lagna, A7, Chara timing"
    },
    {
      "question": "What practical guidance improves relationship outcomes?",
      "answer": "Give practical, non-fatalistic guidance tied to the afflicted/supporting planets and houses. Separate behavior advice, family-handling advice, timing advice, and spiritual/remedial advice.",
      "key_points": ["Guidance point 1", "Guidance point 2"],
      "astrological_basis": "Chart-specific strengths, friction factors, and remedies"
    },
    {
      "question": "What is the key to happiness in my specific chart?",
      "answer": "Synthesize the strongest marriage promise, the main vulnerability, the best timing strategy, and the maturity lesson. Keep it specific to the chart and avoid generic relationship advice.",
      "key_points": ["Key lesson 1", "Key lesson 2"],
      "astrological_basis": "Full synthesis across Parashari, Jaimini, Nadi, D9, and timing"
    }
  ],
  "final_thoughts": "Balanced summary of marriage potential, best windows, and the path to stable partnership.",
  "follow_up_questions": [
    "📅 Best timing for marriage?",
    "❤️ How to improve compatibility?",
    "💍 What are my partner's key traits?",
    "🏛️ Love, arranged, or family-supported relationship pattern?",
    "🪷 What does my Navamsa say about marriage?",
    "⚡ Remedies for relationship peace?"
  ]
}

CRITICAL RULES:
1. Response must be ONLY valid JSON.
2. Use EXACTLY the field names shown above.
3. Include exactly 10 questions in detailed_analysis array.
4. Use <br> for line breaks within JSON strings when needed.
5. Every answer must explicitly separate at least one of: promise, timing, manifestation, continuity, spouse nature, or friction.
6. Do not overstate certainty. Use "strong window", "supportive", "mixed", or "requires effort" instead of guaranteed language.
7. Use `marriage_evidence` when available: `parashari.px.relationship`, `parashari.px.dx.relationship`, `jaimini.jx.relationship`, and `nadi.nx.relationship` are the compact evidence spine.
8. Trust rule: never use first-marriage wording ("when will I get married", "your future spouse will enter") unless marital_status or the user's request clearly indicates they are unmarried. Prefer "partner/spouse", "relationship phase", "marriage lifecycle", and "commitment window" when status is unknown.
"""


def _normalize_date(value: Any) -> str:
    s = str(value or "").strip()
    if not s:
        return ""
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    return s


def _normalize_time(value: Any) -> str:
    s = str(value or "").strip().upper()
    if not s:
        return ""
    for fmt in ("%H:%M:%S", "%H:%M", "%I:%M %p", "%I:%M:%S %p"):
        try:
            return datetime.strptime(s, fmt).strftime("%H:%M:%S")
        except Exception:
            pass
    if len(s) == 5 and s[2] == ":":
        return f"{s}:00"
    return s


def _normalize_place(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def marriage_birth_hash(request: Any) -> str:
    chart_id = getattr(request, "chart_id", None)
    if chart_id:
        # Prefer stable chart-id cache key when available.
        return f"chart:{chart_id}"

    normalized = (
        _normalize_date(getattr(request, "date", "")),
        _normalize_time(getattr(request, "time", "")),
        _normalize_place(getattr(request, "place", "")),
    )
    return hashlib.md5("|".join(normalized).encode()).hexdigest()


def marriage_birth_hash_legacy(request: Any) -> str:
    """Backward-compatible hash used by earlier releases."""
    raw = f"{getattr(request, 'date', '')}_{getattr(request, 'time', '')}_{getattr(request, 'place', '')}"
    return hashlib.md5(raw.encode()).hexdigest()


def ensure_ai_marriage_insights_table(conn: Any, execute_fn: Any) -> None:
    execute_fn(
        conn,
        """
        CREATE TABLE IF NOT EXISTS ai_marriage_insights (
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


def get_cached_marriage(userid: int, birth_hash: str, get_conn: Any, execute_fn: Any) -> Any:
    with get_conn() as conn:
        ensure_ai_marriage_insights_table(conn, execute_fn)
        cur = execute_fn(
            conn,
            """
            SELECT insights_data
            FROM ai_marriage_insights
            WHERE userid = %s AND birth_hash = %s
            """,
            (userid, birth_hash),
        )
        row = cur.fetchone()
    return json.loads(row[0]) if row else None


def attach_marriage_agentic_context(context: Dict[str, Any], birth_data: Dict[str, Any]) -> Dict[str, Any]:
    """Attach compact branch evidence used by the agentic chat marriage flow."""
    agent_ctx = AgentContext(
        birth_data=birth_data,
        user_question="Marriage Analysis",
        intent_result={"category": "marriage", "divisional_charts": ["D1", "D7", "D9"]},
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
            payload = builder(agent_ctx, "Marriage Analysis")
            if name == "parashari":
                evidence[name] = {"px": payload.get("px")}
            elif name == "jaimini":
                evidence[name] = {"jx": payload.get("jx")}
            elif name == "nadi":
                evidence[name] = {"nx": payload.get("nx")}
        except Exception as exc:
            evidence[name] = {"error": str(exc)[:300]}
    context["marriage_evidence"] = evidence
    return context


async def execute_marriage_analysis(
    userid: int,
    request: Any,
    marriage_cost: int,
    *,
    credit_service: Any,
    get_conn: Any,
    execute_fn: Any,
) -> Dict[str, Any]:
    birth_hash = marriage_birth_hash(request)
    legacy_birth_hash = marriage_birth_hash_legacy(request)

    if not request.force_regenerate:
        cached = get_cached_marriage(userid, birth_hash, get_conn, execute_fn)
        if not cached and legacy_birth_hash != birth_hash:
            cached = get_cached_marriage(userid, legacy_birth_hash, get_conn, execute_fn)
        if cached:
            out = dict(cached)
            out["cached"] = True
            return {"ok": True, "marriage_insights": out, "cached": True}

    birth_data = {
        "name": request.name,
        "date": request.date,
        "time": request.time,
        "place": request.place,
        "latitude": request.latitude or 28.6139,
        "longitude": request.longitude or 77.2090,
        "timezone": request.timezone or "UTC+0",
        "gender": request.gender,
        "marital_status": getattr(request, "marital_status", None),
        "current_year": date.today().year,
    }

    context_generator = MarriageAIContextGenerator()
    context = await asyncio.get_event_loop().run_in_executor(
        None,
        context_generator.build_marriage_context,
        birth_data,
    )
    context = attach_marriage_agentic_context(context, birth_data)

    analyzer = StructuredAnalysisAnalyzer()
    max_retries = 3
    retry_delay = 10
    ai_result = None
    lang = request.language or "english"

    for attempt in range(max_retries):
        try:
            print(f"🔄 Marriage: attempt {attempt + 1}/{max_retries} — Structured API")
            ai_result = await analyzer.generate_structured_report(MARRIAGE_STRUCTURED_QUESTION, context, lang)
        except Exception as api_error:
            ai_result = {"success": False, "error": str(api_error)}
            print(f"⚠️ Marriage API attempt {attempt + 1} raised: {ai_result['error'][:500]}")

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

        marriage_insights = {
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
            marriage_cost,
            "marriage_analysis",
            f"Marriage analysis for {birth_data.get('name', 'user')}",
        ):
            return {"ok": False, "error": "Credit deduction failed"}

        with get_conn() as conn:
            ensure_ai_marriage_insights_table(conn, execute_fn)
            execute_fn(
                conn,
                """
                INSERT INTO ai_marriage_insights (userid, birth_hash, insights_data, updated_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (userid, birth_hash)
                DO UPDATE SET insights_data = EXCLUDED.insights_data,
                              updated_at = EXCLUDED.updated_at
                """,
                (userid, birth_hash, json.dumps(marriage_insights)),
            )
            conn.commit()

        return {"ok": True, "marriage_insights": marriage_insights, "cached": False}
    except Exception as e:
        print(f"❌ Marriage response processing failed: {e}")
        return {"ok": False, "error": str(e)}
