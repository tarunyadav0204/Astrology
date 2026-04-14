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
from ai.structured_analyzer import StructuredAnalysisAnalyzer

MARRIAGE_STRUCTURED_QUESTION = """
As an expert Vedic astrologer, analyze the birth chart for Relationship and Marriage Destiny.

CRITICAL: You MUST respond with ONLY a JSON object. NO other text.
{
  "quick_answer": "Summary of marriage prospects and timing.",
  "detailed_analysis": [
    {
      "question": "What is the timeline for major relationship events?",
      "answer": "Analyze timing using Vimshottari Dasha and Jupiter/Saturn transits"
    },
    {
      "question": "What is the personality and nature of my partner?",
      "answer": "Describe spouse traits from 7th house and D9 Navamsa"
    },
    {
      "question": "Are there any Doshas affecting harmony?",
      "answer": "Analyze Mangal Dosha and Saturn aspects"
    },
    {
      "question": "Is my destiny inclined towards Love or Traditional connection?",
      "answer": "Analyze 5th-7th house connection and relationship style"
    },
    {
      "question": "What is the key to happiness in my specific chart?",
      "answer": "Guidance based on D9 Navamsa analysis"
    }
  ],
  "final_thoughts": "Encouraging summary focusing on marriage potential.",
  "follow_up_questions": [
    "📅 Best timing for marriage?",
    "❤️ How to improve compatibility?",
    "💍 What are my partner's key traits?",
    "⚡ Remedies for relationship peace?"
  ]
}

CRITICAL RULES:
1. Response must be ONLY valid JSON.
2. Use EXACTLY the field names shown above.
3. Include exactly 5 questions in detailed_analysis array.
4. Use <br> for line breaks within JSON strings when needed.
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
        "current_year": date.today().year,
    }

    context_generator = MarriageAIContextGenerator()
    context = await asyncio.get_event_loop().run_in_executor(
        None,
        context_generator.build_marriage_context,
        birth_data,
    )

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
