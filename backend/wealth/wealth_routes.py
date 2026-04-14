from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Optional
import sys
import os
import hashlib
import json
import uuid
from datetime import datetime
from auth import get_current_user, User
from credits.credit_service import CreditService
from db import get_conn, execute

# Add the parent directory to the path to import calculators
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculators.chart_calculator import ChartCalculator
from calculators.wealth_calculator import WealthCalculator

class BirthDetailsRequest(BaseModel):
    chart_id: Optional[int] = None
    birth_date: str  # YYYY-MM-DD
    birth_time: str  # HH:MM
    birth_place: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    force_regenerate: Optional[bool] = False
    user_role: Optional[str] = None
    language: Optional[str] = 'english'

class WealthAnalysisRequest(BaseModel):
    chart_id: Optional[int] = None
    name: Optional[str] = None
    date: str
    time: str
    place: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    gender: Optional[str] = None
    language: Optional[str] = 'english'
    response_style: Optional[str] = 'detailed'
    force_regenerate: Optional[bool] = False

router = APIRouter(prefix="/wealth", tags=["wealth"])
credit_service = CreditService()

@router.post("/analyze")
async def analyze_wealth(
    request: WealthAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """Mobile: start async wealth job — returns job_id; poll GET /ai-insights-enhanced/status/{job_id}."""
    print(f"📱 MOBILE WEALTH ANALYSIS (job): {request.date} {request.time}")
    birth_request = BirthDetailsRequest(
        chart_id=request.chart_id,
        birth_date=request.date,
        birth_time=request.time,
        birth_place=request.place,
        latitude=request.latitude,
        longitude=request.longitude,
        timezone=request.timezone,
        force_regenerate=request.force_regenerate,
        language=request.language,
    )
    return await start_wealth_enhanced_job(birth_request, background_tasks, current_user)

def _create_birth_hash(birth_data):
    """Create unique hash for birth data; prefer chart-id when available."""
    chart_id = getattr(birth_data, 'chart_id', None)
    if chart_id:
        return f"chart:{chart_id}"
    birth_string = f"{birth_data.date}_{birth_data.time}_{birth_data.latitude}_{birth_data.longitude}"
    return hashlib.sha256(birth_string.encode()).hexdigest()


def _create_birth_hash_legacy(birth_data):
    """Backward-compatible pre-chart-id hash."""
    birth_string = f"{birth_data.date}_{birth_data.time}_{birth_data.latitude}_{birth_data.longitude}"
    return hashlib.sha256(birth_string.encode()).hexdigest()

def _init_ai_insights_table():
    """Initialize AI insights table if not exists"""
    with get_conn() as conn:
        execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS ai_wealth_insights (
                id SERIAL PRIMARY KEY,
                userid INTEGER NOT NULL DEFAULT 0,
                birth_hash TEXT NOT NULL,
                insights_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                , UNIQUE(userid, birth_hash)
            )
            """,
        )
        conn.commit()

def _get_stored_ai_insights(userid: int, birth_hash: str):
    """Get stored AI insights from database"""
    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT insights_data
            FROM ai_wealth_insights
            WHERE userid = %s AND birth_hash = %s
            """,
            (userid, birth_hash),
        )
        result = cur.fetchone()
    return json.loads(result[0]) if result else None

def _store_ai_insights(userid: int, birth_hash: str, insights_data):
    """Store AI insights in database"""
    with get_conn() as conn:
        execute(
            conn,
            """
            INSERT INTO ai_wealth_insights (userid, birth_hash, insights_data, updated_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (userid, birth_hash)
            DO UPDATE SET insights_data = EXCLUDED.insights_data,
                          updated_at = EXCLUDED.updated_at
            """,
            (userid, birth_hash, json.dumps(insights_data), datetime.now().isoformat()),
        )
        conn.commit()


def init_wealth_analysis_jobs_table():
    """DB table for async wealth AI jobs (polling, same idea as event_timeline_jobs)."""
    with get_conn() as conn:
        execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS wealth_analysis_jobs (
                job_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
                request_json TEXT NOT NULL,
                result_data TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP
            )
            """,
        )
        execute(conn, "CREATE INDEX IF NOT EXISTS idx_wealth_jobs_user ON wealth_analysis_jobs (user_id)")
        execute(conn, "CREATE INDEX IF NOT EXISTS idx_wealth_jobs_status ON wealth_analysis_jobs (status)")
        conn.commit()


async def process_wealth_analysis_job(job_id: str, user_id: int, request_json: str, wealth_cost: int):
    from wealth.wealth_enhanced_execute import execute_wealth_enhanced

    try:
        request = BirthDetailsRequest(**json.loads(request_json))
        with get_conn() as conn:
            execute(
                conn,
                "UPDATE wealth_analysis_jobs SET status = %s, started_at = %s WHERE job_id = %s",
                ("processing", datetime.now(), job_id),
            )
            conn.commit()

        result = await execute_wealth_enhanced(
            user_id,
            request,
            wealth_cost,
            credit_service=credit_service,
            create_birth_hash=_create_birth_hash,
            create_birth_hash_legacy=_create_birth_hash_legacy,
            init_ai_insights_table=_init_ai_insights_table,
            get_stored_ai_insights=_get_stored_ai_insights,
            store_ai_insights=_store_ai_insights,
        )

        with get_conn() as conn:
            if result.get("ok"):
                payload = {
                    "enhanced_insights": result["enhanced_insights"],
                    "cached": result.get("cached", False),
                }
                execute(
                    conn,
                    """
                    UPDATE wealth_analysis_jobs
                    SET status = %s, result_data = %s, completed_at = %s
                    WHERE job_id = %s
                    """,
                    ("completed", json.dumps(payload), datetime.now(), job_id),
                )
            else:
                execute(
                    conn,
                    """
                    UPDATE wealth_analysis_jobs
                    SET status = %s, error_message = %s, completed_at = %s
                    WHERE job_id = %s
                    """,
                    ("failed", result.get("error") or "Analysis failed", datetime.now(), job_id),
                )
            conn.commit()
    except Exception as e:
        print(f"❌ process_wealth_analysis_job: {e}")
        import traceback

        traceback.print_exc()
        with get_conn() as conn:
            execute(
                conn,
                """
                UPDATE wealth_analysis_jobs
                SET status = %s, error_message = %s, completed_at = %s
                WHERE job_id = %s
                """,
                ("failed", str(e), datetime.now(), job_id),
            )
            conn.commit()


def parse_gemini_astrology_response(raw_text):
    """
    Parses the raw text response from Gemini into a structured dictionary
    suitable for UI rendering.
    """
    import re
    import html
    
    # Debug: Print the complete response format
    print("\n" + "="*100)
    print("COMPLETE GEMINI RESPONSE - FULL TEXT:")
    print("="*100)
    print(raw_text)
    print("="*100)
    print(f"Total length: {len(raw_text)} characters")
    print("="*100 + "\n")
    
    parsed_data = {
        "quick_answer": None,
        "key_insights": [],
        "detailed_analysis": [],
        "final_thoughts": None,
        "follow_up_questions": []
    }

    # Extract Quick Answer from div structure
    quick_answer_match = re.search(r'&lt;div class=&quot;quick-answer-card&quot;&gt;(.*?)&lt;/div&gt;', raw_text, re.DOTALL)
    if quick_answer_match:
        quick_content = quick_answer_match.group(1)
        # Decode HTML entities
        quick_content = html.unescape(quick_content)
        # Convert ** to <strong> tags
        quick_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', quick_content)
        parsed_data["quick_answer"] = quick_content.strip()
        print(f"✅ EXTRACTED QUICK ANSWER: {parsed_data['quick_answer'][:100]}...")
        
        # Also add to detailed_analysis for frontend display
        parsed_data["detailed_analysis"].append({
            "title": "Wealth Analysis Summary",
            "content": quick_content.strip()
        })
    
    # If no quick answer found, add fallback content
    if not parsed_data["quick_answer"]:
        parsed_data["quick_answer"] = "Analysis in progress..."
        parsed_data["detailed_analysis"].append({
            "title": "Complete Analysis",
            "content": raw_text[:1000] + "..." if len(raw_text) > 1000 else raw_text
        })

    return parsed_data

def _parse_ai_response(response_text):
    """Parse JSON response from Gemini"""
    
    # Log the response for debugging
    print("\n" + "="*100)
    print("GEMINI JSON RESPONSE:")
    print("="*100)
    print(response_text)
    print("="*100 + "\n")
    
    import re
    import html
    
    # Extract JSON from markdown code blocks
    json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', response_text, re.DOTALL)
    if json_match:
        json_text = json_match.group(1)
        # Decode HTML entities
        json_text = html.unescape(json_text)
        print(f"✅ Extracted and decoded JSON: {json_text[:100]}...")
    else:
        json_text = response_text
    
    try:
        json_response = json.loads(json_text)
        print(f"✅ Successfully parsed JSON response")
        
        return {
            "summary": "Comprehensive wealth analysis based on Vedic astrology principles.",
            "json_response": json_response,
            "wealth_analysis": {
                "json_response": json_response,
                "summary": "Comprehensive wealth analysis based on Vedic astrology principles."
            }
        }
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON: {e}")
        return {
            "summary": "Comprehensive wealth analysis based on Vedic astrology principles.",
            "raw_response": response_text,
            "wealth_analysis": {
                "raw_response": response_text,
                "summary": "Comprehensive wealth analysis based on Vedic astrology principles."
            }
        }



@router.post("/overall-assessment")
async def get_overall_wealth_assessment(request: BirthDetailsRequest, current_user: User = Depends(get_current_user)):
    """Complete wealth assessment with technical analysis"""
    try:
        # Prepare birth data
        from types import SimpleNamespace
        birth_data = SimpleNamespace(
            chart_id=request.chart_id,
            date=request.birth_date,
            time=request.birth_time,
            place=request.birth_place,
            latitude=request.latitude or 28.6139,
            longitude=request.longitude or 77.2090,
            timezone=request.timezone or 'UTC+0'
        )
        
        # Calculate chart
        calculator = ChartCalculator({})
        chart_data = calculator.calculate_chart(birth_data)
        
        # Calculate wealth analysis
        wealth_calculator = WealthCalculator(chart_data, birth_data)
        wealth_data = wealth_calculator.calculate_overall_wealth()
        
        return {"success": True, "data": wealth_data}
        
    except Exception as e:
        print(f"❌ Wealth assessment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _wealth_credit_check_or_raise(current_user: User) -> int:
    base_cost = credit_service.get_credit_setting("wealth_analysis_cost")
    wealth_cost = credit_service.get_effective_cost(current_user.userid, base_cost, "wealth_analysis_cost")
    user_balance = credit_service.get_user_credits(current_user.userid)
    print(f"💳 WEALTH CREDIT CHECK: user={current_user.userid} cost={wealth_cost} balance={user_balance}")
    if user_balance < wealth_cost:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits. You need {wealth_cost} credits but have {user_balance}.",
        )
    return wealth_cost


@router.post("/ai-insights-enhanced/start")
async def start_wealth_enhanced_job(
    request: BirthDetailsRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    Start enhanced wealth AI in the background; poll GET /ai-insights-enhanced/status/{job_id}.
    Same credits check as the legacy streaming endpoint.
    """
    wealth_cost = _wealth_credit_check_or_raise(current_user)
    init_wealth_analysis_jobs_table()
    job_id = str(uuid.uuid4())
    request_json = json.dumps(
        request.model_dump() if hasattr(request, "model_dump") else request.dict()
    )
    with get_conn() as conn:
        execute(
            conn,
            """
            INSERT INTO wealth_analysis_jobs (job_id, user_id, status, request_json)
            VALUES (%s, %s, %s, %s)
            """,
            (job_id, current_user.userid, "pending", request_json),
        )
        conn.commit()
    background_tasks.add_task(
        process_wealth_analysis_job,
        job_id,
        current_user.userid,
        request_json,
        wealth_cost,
    )
    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Wealth analysis started — poll status until completed.",
    }


@router.get("/ai-insights-enhanced/status/{job_id}")
async def get_wealth_enhanced_job_status(job_id: str, current_user: User = Depends(get_current_user)):
    init_wealth_analysis_jobs_table()
    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT status, result_data, error_message, started_at, completed_at
            FROM wealth_analysis_jobs
            WHERE job_id = %s AND user_id = %s
            """,
            (job_id, current_user.userid),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    status, result_data, error_message, started_at, completed_at = row
    out: Dict = {"status": status}
    if status == "completed" and result_data:
        payload = json.loads(result_data)
        out["data"] = payload.get("enhanced_insights")
        out["cached"] = payload.get("cached", False)
        out["completed_at"] = completed_at
    elif status == "failed":
        out["error"] = error_message or "Analysis failed"
    elif status in ("pending", "processing"):
        out["message"] = "Analyzing chart and generating wealth insights..."
        if started_at:
            out["started_at"] = started_at
    return out


@router.post("/ai-insights-enhanced")
async def get_enhanced_wealth_insights(request: BirthDetailsRequest, current_user: User = Depends(get_current_user)):
    """Legacy SSE: thin wrapper around the same pipeline (prefer /start + polling for long runs)."""
    from fastapi.responses import StreamingResponse

    wealth_cost = _wealth_credit_check_or_raise(current_user)
    print(f"Enhanced wealth insights (SSE) request: {request.birth_date} {request.birth_time}")

    from wealth.wealth_enhanced_execute import execute_wealth_enhanced

    async def generate_streaming_response():
        try:
            yield f"data: {json.dumps({'status': 'processing', 'message': 'Running wealth analysis...'})}\n\n"
            result = await execute_wealth_enhanced(
                current_user.userid,
                request,
                wealth_cost,
                credit_service=credit_service,
                create_birth_hash=_create_birth_hash,
                create_birth_hash_legacy=_create_birth_hash_legacy,
                init_ai_insights_table=_init_ai_insights_table,
                get_stored_ai_insights=_get_stored_ai_insights,
                store_ai_insights=_store_ai_insights,
            )
            if result.get("ok"):
                final_response = {
                    "status": "complete",
                    "data": result["enhanced_insights"],
                    "cached": result.get("cached", False),
                }
                yield f"data: {json.dumps(final_response)}\n\n"
            else:
                err = result.get("error", "Unknown error")
                yield f"data: {json.dumps({'status': 'error', 'error': err})}\n\n"
        except Exception as e:
            print(f"❌ ENHANCED WEALTH ANALYSIS ERROR: {e}")
            import traceback

            traceback.print_exc()
            yield f"data: {json.dumps({'status': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        generate_streaming_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

@router.post("/check-cache")
async def check_cached_insights(request: BirthDetailsRequest, current_user: User = Depends(get_current_user)):
    """Check if cached insights exist without generating new ones"""
    try:
        # Create birth data object
        from types import SimpleNamespace
        birth_data = SimpleNamespace(
            date=request.birth_date,
            time=request.birth_time,
            place=request.birth_place,
            latitude=request.latitude or 28.6139,
            longitude=request.longitude or 77.2090,
            timezone=request.timezone or 'UTC+0'
        )
        
        birth_hash = _create_birth_hash(birth_data)
        legacy_birth_hash = _create_birth_hash_legacy(birth_data)
        _init_ai_insights_table()

        stored_insights = _get_stored_ai_insights(current_user.userid, birth_hash)
        if not stored_insights and legacy_birth_hash != birth_hash:
            stored_insights = _get_stored_ai_insights(current_user.userid, legacy_birth_hash)
        
        if stored_insights:
            # Format cached response for mobile compatibility
            cached_response = {
                'analysis': stored_insights,
                'terms': stored_insights.get('terms', []),
                'glossary': stored_insights.get('glossary', {}),
                'enhanced_context': True,
                'questions_covered': len(stored_insights.get('detailed_analysis', [])),
                'context_type': 'cached_analysis',
                'generated_at': datetime.now().isoformat()
            }
            return {"success": True, "data": cached_response, "cached": True}
        else:
            return {"success": False, "message": "No cached data found"}
            
    except Exception as e:
        print(f"❌ Cache check error: {e}")
        return {"success": False, "message": str(e)}

@router.post("/astrological-context")
async def get_astrological_context(request: BirthDetailsRequest, current_user: User = Depends(get_current_user)):
    """Get complete astrological context for admin users"""
    try:
        # Check if user is admin
        if current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Import chat context builder
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from chat.chat_context_builder import ChatContextBuilder
        
        # Prepare birth data
        birth_data = {
            'name': request.birth_place,
            'date': request.birth_date,
            'time': request.birth_time,
            'place': request.birth_place,
            'latitude': request.latitude or 28.6139,
            'longitude': request.longitude or 77.2090,
            'timezone': request.timezone or 'UTC+0'
        }
        
        # Build complete context
        context_builder = ChatContextBuilder()
        full_context = context_builder.build_complete_context(birth_data)
        
        return {
            "success": True,
            "context": full_context,
            "context_length": len(str(full_context))
        }
        
    except Exception as e:
        print(f"❌ Context error: {e}")
        raise HTTPException(status_code=500, detail=str(e))