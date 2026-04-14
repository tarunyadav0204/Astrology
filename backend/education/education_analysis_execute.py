"""Shared async pipeline for education AI (EducationAIContextGenerator + StructuredAnalysisAnalyzer)."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sys
from datetime import date, datetime
from typing import Any, Dict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.education_ai_context_generator import EducationAIContextGenerator
from ai.gemini_errors import transient_gemini_error, user_facing_gemini_error
from ai.structured_analyzer import StructuredAnalysisAnalyzer

EDUCATION_STRUCTURED_QUESTION = """
As an expert Vedic astrologer, analyze the birth chart for Education, Intelligence, and Academic Success.

CRITICAL: You MUST respond with ONLY a JSON object.
{
  "quick_answer": "Summary of academic potential, best fields of study, and current educational phase.",
  "detailed_analysis": [
    {
      "question": "What is my natural learning potential and intelligence level?",
      "answer": "Analyze 5th House, Mercury, and Jupiter."
    },
    {
      "question": "Which subjects or career paths suit me best?",
      "answer": "Use technical aptitude and subject indicators with specific recommendations."
    },
    {
      "question": "Will I have success in higher education (Masters/PhD)?",
      "answer": "Analyze 9th House and D-24 chart links."
    },
    {
      "question": "What is the best way for me to study?",
      "answer": "Suggest study methods based on Mercury/Moon learning style."
    },
    {
      "question": "Are there any obstacles or breaks in education?",
      "answer": "Check Saturn/Rahu influences and dasha periods."
    }
  ],
  "final_thoughts": "Encouraging summary focused on maximizing intellectual strengths.",
  "follow_up_questions": [
    "🎓 Best timing for higher studies?",
    "📚 Will I succeed in competitive exams?",
    "🌍 Chances of foreign education?",
    "🧠 Remedies for concentration?"
  ]
}

CRITICAL RULES:
1. Response must be ONLY valid JSON.
2. Use EXACTLY the field names shown above.
3. Include exactly 5 questions in detailed_analysis array.
4. Mention this is astrological guidance, not educational counseling.
"""


def education_birth_hash(request: Any) -> str:
    chart_id = getattr(request, 'chart_id', None)
    if chart_id:
        return f"chart:{chart_id}"
    return hashlib.md5(f"{request.date}_{request.time}_{request.place}".encode()).hexdigest()


def education_birth_hash_legacy(request: Any) -> str:
    return hashlib.md5(f"{request.date}_{request.time}_{request.place}".encode()).hexdigest()


def ensure_ai_education_insights_table(conn: Any, execute_fn: Any) -> None:
    execute_fn(
        conn,
        """
        CREATE TABLE IF NOT EXISTS ai_education_insights (
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


def get_cached_education(userid: int, birth_hash: str, get_conn: Any, execute_fn: Any) -> Any:
    with get_conn() as conn:
        ensure_ai_education_insights_table(conn, execute_fn)
        cur = execute_fn(
            conn,
            """
            SELECT insights_data
            FROM ai_education_insights
            WHERE userid = %s AND birth_hash = %s
            """,
            (userid, birth_hash),
        )
        row = cur.fetchone()
    return json.loads(row[0]) if row else None


async def execute_education_analysis(
    userid: int,
    request: Any,
    education_cost: int,
    *,
    credit_service: Any,
    get_conn: Any,
    execute_fn: Any,
) -> Dict[str, Any]:
    birth_hash = education_birth_hash(request)
    legacy_birth_hash = education_birth_hash_legacy(request)

    if not request.force_regenerate:
        cached = get_cached_education(userid, birth_hash, get_conn, execute_fn)
        if not cached and legacy_birth_hash != birth_hash:
            cached = get_cached_education(userid, legacy_birth_hash, get_conn, execute_fn)
        if cached:
            out = dict(cached)
            out["cached"] = True
            return {"ok": True, "education_insights": out, "cached": True}

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

    context_generator = EducationAIContextGenerator()
    context = await asyncio.get_event_loop().run_in_executor(
        None,
        context_generator.build_education_context,
        birth_data,
    )

    analyzer = StructuredAnalysisAnalyzer()
    max_retries = 3
    retry_delay = 10
    ai_result = None
    lang = request.language or "english"

    for attempt in range(max_retries):
        try:
            print(f"🔄 Education: attempt {attempt + 1}/{max_retries} — Structured API")
            ai_result = await analyzer.generate_structured_report(EDUCATION_STRUCTURED_QUESTION, context, lang)
        except Exception as api_error:
            ai_result = {"success": False, "error": str(api_error)}
            print(f"⚠️ Education API attempt {attempt + 1} raised: {ai_result['error'][:500]}")

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

        education_insights = {
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
            education_cost,
            "education_analysis",
            f"Education analysis for {birth_data.get('name', 'user')}",
        ):
            return {"ok": False, "error": "Credit deduction failed"}

        with get_conn() as conn:
            ensure_ai_education_insights_table(conn, execute_fn)
            execute_fn(
                conn,
                """
                INSERT INTO ai_education_insights (userid, birth_hash, insights_data, updated_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (userid, birth_hash)
                DO UPDATE SET insights_data = EXCLUDED.insights_data,
                              updated_at = EXCLUDED.updated_at
                """,
                (userid, birth_hash, json.dumps(education_insights)),
            )
            conn.commit()

        return {"ok": True, "education_insights": education_insights, "cached": False}
    except Exception as e:
        print(f"❌ Education response processing failed: {e}")
        return {"ok": False, "error": str(e)}
