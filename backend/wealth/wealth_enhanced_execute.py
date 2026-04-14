"""
Shared async pipeline for enhanced wealth AI (ChatContextBuilder + StructuredAnalysisAnalyzer).
Used by job-based polling and optionally by thin streaming wrappers.
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime
from types import SimpleNamespace
from typing import Any, Dict, Optional

import os

from ai.gemini_errors import transient_gemini_error, user_facing_gemini_error

# wealth_routes helpers are imported lazily inside functions to avoid circular imports at module load


WEALTH_STRUCTURED_QUESTION = """
{
  "summary": "Brief wealth overview with key insights",
  "detailed_analysis": [
    {
      "title": "Wealth Houses Analysis",
      "content": "Analysis of 2nd, 11th, and 9th houses for wealth indicators"
    },
    {
      "title": "Planetary Wealth Indicators",
      "content": "Jupiter, Venus, and other wealth-giving planets analysis"
    },
    {
      "title": "Dhana Yogas",
      "content": "Wealth combinations and yogas in the chart"
    },
    {
      "title": "Dasha Periods for Wealth",
      "content": "Current and upcoming periods for financial gains"
    },
    {
      "title": "Investment & Business Guidance",
      "content": "Recommendations for investments and business ventures"
    }
  ],
  "final_thoughts": "Concluding summary with key takeaways and overall wealth outlook",
  "glossary": {
    "term_id": "Simple explanation of the term"
  }
}

Analyze the wealth potential focusing on:
- 2nd House (Wealth accumulation)
- 11th House (Gains and income)
- 9th House (Fortune and luck)
- Jupiter and Venus placements
- Dhana Yogas and wealth combinations
- Current and upcoming dasha periods
- Investment recommendations
- Business vs job suitability

IMPORTANT: Include meaningful final_thoughts with overall assessment and key advice.
"""


async def execute_wealth_enhanced(
    userid: int,
    birth_request: Any,
    wealth_cost: int,
    *,
    credit_service: Any,
    create_birth_hash: Any,
    create_birth_hash_legacy: Optional[Any],
    init_ai_insights_table: Any,
    get_stored_ai_insights: Any,
    store_ai_insights: Any,
) -> Dict[str, Any]:
    """
    Returns:
      { "ok": True, "enhanced_insights": {...}, "cached": bool }
      { "ok": False, "error": str, "enhanced_insights": optional error-shaped dict }
    """
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from chat.chat_context_builder import ChatContextBuilder
    from ai.structured_analyzer import StructuredAnalysisAnalyzer

    birth_data = {
        "chart_id": getattr(birth_request, "chart_id", None),
        "name": birth_request.birth_place,
        "date": birth_request.birth_date,
        "time": birth_request.birth_time,
        "place": birth_request.birth_place,
        "latitude": birth_request.latitude or 28.6139,
        "longitude": birth_request.longitude or 77.2090,
        "timezone": birth_request.timezone or "UTC+0",
    }
    birth_obj = SimpleNamespace(**birth_data)
    birth_hash = create_birth_hash(birth_obj)
    legacy_birth_hash = create_birth_hash_legacy(birth_obj) if create_birth_hash_legacy else birth_hash

    init_ai_insights_table()
    force_regen = bool(birth_request.force_regenerate)
    stored = get_stored_ai_insights(userid, birth_hash)
    if not stored and legacy_birth_hash != birth_hash:
        stored = get_stored_ai_insights(userid, legacy_birth_hash)

    if stored and not force_regen:
        cached_response = {
            "analysis": stored,
            "terms": stored.get("terms", []),
            "glossary": stored.get("glossary", {}),
            "enhanced_context": True,
            "questions_covered": len(stored.get("detailed_analysis", [])),
            "context_type": "cached_analysis",
            "generated_at": datetime.now().isoformat(),
        }
        return {"ok": True, "enhanced_insights": cached_response, "cached": True}

    print(f"🏗️ STARTING CONTEXT BUILD for: {birth_data['date']} {birth_data['time']}")
    context_builder = ChatContextBuilder()
    try:
        full_context = await asyncio.get_event_loop().run_in_executor(
            None, context_builder.build_complete_context, birth_data
        )
        print(f"✅ CONTEXT BUILD COMPLETED ({len(str(full_context))} chars)")
    except Exception as e:
        print(f"❌ CONTEXT BUILD FAILED: {e}")
        raise

    analyzer = StructuredAnalysisAnalyzer()
    if isinstance(full_context, str):
        context_dict = {
            "astrological_data": full_context,
            "birth_details": {
                "name": birth_data["name"],
                "date": birth_data["date"],
                "time": birth_data["time"],
                "place": birth_data["place"],
            },
        }
    else:
        context_dict = full_context if full_context else {
            "astrological_data": "No astrological context available",
            "birth_details": {
                "name": birth_data["name"],
                "date": birth_data["date"],
                "time": birth_data["time"],
                "place": birth_data["place"],
            },
        }

    max_retries = 3
    retry_delay = 10
    ai_result = None
    language = getattr(birth_request, "language", None) or "english"

    for attempt in range(max_retries):
        try:
            print(f"🔄 Attempt {attempt + 1}/{max_retries} - Calling Structured API...")
            ai_result = await analyzer.generate_structured_report(
                WEALTH_STRUCTURED_QUESTION, context_dict, language
            )
        except Exception as api_error:
            ai_result = {"success": False, "error": str(api_error)}
            print(f"⚠️ API attempt {attempt + 1} raised: {ai_result['error'][:500]}")

        if ai_result and ai_result.get("success"):
            break

        err_raw = (ai_result or {}).get("error", "") or ""
        if transient_gemini_error(err_raw) and attempt < max_retries - 1:
            wait_time = retry_delay * (2**attempt)
            print(f"⏳ Transient Gemini failure, retrying in {wait_time}s...")
            await asyncio.sleep(wait_time)
            continue
        break

    if ai_result and ai_result.get("success"):
        try:
            if ai_result.get("is_raw"):
                parsed_response = {
                    "raw_response": ai_result.get("response", ""),
                    "quick_answer": "Analysis provided below.",
                    "detailed_analysis": [],
                    "final_thoughts": "View the detailed report below.",
                    "follow_up_questions": [],
                }
            else:
                raw_data = ai_result.get("data", {})
                detailed_analysis = []
                for item in raw_data.get("detailed_analysis", []):
                    detailed_analysis.append({
                        "question": item.get("title", ""),
                        "answer": item.get("content", ""),
                    })
                parsed_response = {
                    "quick_answer": raw_data.get("summary", "Analysis completed successfully."),
                    "detailed_analysis": detailed_analysis,
                    "final_thoughts": raw_data.get("final_thoughts", ""),
                    "follow_up_questions": raw_data.get("follow_up_questions", []),
                    "terms": ai_result.get("terms", []),
                    "glossary": ai_result.get("glossary", {}),
                }

            if not credit_service.spend_credits(
                userid, wealth_cost, "wealth_analysis", f"Wealth analysis for {birth_request.birth_date}"
            ):
                return {"ok": False, "error": "Credit deduction failed"}

            store_ai_insights(userid, birth_hash, parsed_response)

            enhanced_insights = {
                "analysis": parsed_response,
                "terms": ai_result.get("terms", []),
                "glossary": ai_result.get("glossary", {}),
                "enhanced_context": True,
                "questions_covered": len(parsed_response.get("detailed_analysis", [])),
                "context_type": "structured_analyzer",
                "generated_at": datetime.now().isoformat(),
            }
            return {"ok": True, "enhanced_insights": enhanced_insights, "cached": False}
        except Exception as parse_error:
            print(f"❌ Response processing failed: {parse_error}")
            return {"ok": False, "error": f"Failed to process AI response: {parse_error}"}

    err = user_facing_gemini_error((ai_result or {}).get("error", "") or "No response from AI")
    return {
        "ok": False,
        "error": err,
        "enhanced_insights": {
            "wealth_analysis": "AI analysis failed. Please try again.",
            "enhanced_context": False,
            "error": err,
        },
    }
