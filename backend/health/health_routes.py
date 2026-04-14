from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict
import sys
import os
import json
import uuid
from datetime import datetime
from auth import get_current_user, User
from credits.credit_service import CreditService
from db import get_conn, execute

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from health.health_analysis_execute import (
    execute_health_analysis,
    health_birth_hash,
    health_birth_hash_legacy,
    ensure_ai_health_insights_table,
)

class HealthAnalysisRequest(BaseModel):
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

router = APIRouter(prefix="/health", tags=["health"])

credit_service = CreditService()


def _health_credit_check_or_raise(current_user: User) -> int:
    base_cost = credit_service.get_credit_setting("health_analysis_cost")
    health_cost = credit_service.get_effective_cost(current_user.userid, base_cost, "health_analysis_cost")
    user_balance = credit_service.get_user_credits(current_user.userid)
    if user_balance < health_cost:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits. You need {health_cost} credits but have {user_balance}.",
        )
    return health_cost


def init_health_analysis_jobs_table():
    with get_conn() as conn:
        execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS health_analysis_jobs (
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
        execute(conn, "CREATE INDEX IF NOT EXISTS idx_health_jobs_user ON health_analysis_jobs (user_id)")
        execute(conn, "CREATE INDEX IF NOT EXISTS idx_health_jobs_status ON health_analysis_jobs (status)")
        conn.commit()


async def process_health_analysis_job(job_id: str, user_id: int, request_json: str, health_cost: int):
    try:
        req_data = json.loads(request_json)
        request = HealthAnalysisRequest(**req_data)
        with get_conn() as conn:
            execute(
                conn,
                "UPDATE health_analysis_jobs SET status = %s, started_at = %s WHERE job_id = %s",
                ("processing", datetime.now(), job_id),
            )
            conn.commit()

        result = await execute_health_analysis(
            user_id,
            request,
            health_cost,
            credit_service=credit_service,
            get_conn=get_conn,
            execute_fn=execute,
        )

        with get_conn() as conn:
            if result.get("ok"):
                payload = {
                    "health_insights": result["health_insights"],
                    "cached": result.get("cached", False),
                }
                execute(
                    conn,
                    """
                    UPDATE health_analysis_jobs
                    SET status = %s, result_data = %s, completed_at = %s
                    WHERE job_id = %s
                    """,
                    ("completed", json.dumps(payload), datetime.now(), job_id),
                )
            else:
                execute(
                    conn,
                    """
                    UPDATE health_analysis_jobs
                    SET status = %s, error_message = %s, completed_at = %s
                    WHERE job_id = %s
                    """,
                    ("failed", result.get("error") or "Analysis failed", datetime.now(), job_id),
                )
            conn.commit()
    except Exception as e:
        print(f"❌ process_health_analysis_job: {e}")
        import traceback

        traceback.print_exc()
        with get_conn() as conn:
            execute(
                conn,
                """
                UPDATE health_analysis_jobs
                SET status = %s, error_message = %s, completed_at = %s
                WHERE job_id = %s
                """,
                ("failed", str(e), datetime.now(), job_id),
            )
            conn.commit()


@router.post("/analyze/start")
async def start_health_analysis_job(
    request: HealthAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """Start health AI in background; poll GET /health/analyze/status/{job_id}."""
    health_cost = _health_credit_check_or_raise(current_user)
    init_health_analysis_jobs_table()
    job_id = str(uuid.uuid4())
    req_dump = (
        request.model_dump() if hasattr(request, "model_dump") else request.dict()
    )
    request_json = json.dumps(req_dump)
    with get_conn() as conn:
        execute(
            conn,
            """
            INSERT INTO health_analysis_jobs (job_id, user_id, status, request_json)
            VALUES (%s, %s, %s, %s)
            """,
            (job_id, current_user.userid, "pending", request_json),
        )
        conn.commit()
    background_tasks.add_task(
        process_health_analysis_job,
        job_id,
        current_user.userid,
        request_json,
        health_cost,
    )
    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Health analysis started — poll status until completed.",
    }


@router.get("/analyze/status/{job_id}")
async def get_health_analysis_job_status(job_id: str, current_user: User = Depends(get_current_user)):
    init_health_analysis_jobs_table()
    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT status, result_data, error_message, started_at, completed_at
            FROM health_analysis_jobs
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
        out["data"] = payload.get("health_insights")
        out["cached"] = payload.get("cached", False)
        out["completed_at"] = completed_at
    elif status == "failed":
        out["error"] = error_message or "Analysis failed"
    elif status in ("pending", "processing"):
        out["message"] = "Analyzing chart and generating health insights..."
        if started_at:
            out["started_at"] = started_at
    return out


@router.post("/analyze")
async def analyze_health(
    request: HealthAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """Mobile/web: returns job_id — poll GET /health/analyze/status/{job_id}."""
    return await start_health_analysis_job(request, background_tasks, current_user)

@router.post("/get-analysis")
async def get_previous_analysis(request: HealthAnalysisRequest, current_user: User = Depends(get_current_user)):
    """Get previously generated health analysis if exists"""
    try:
        birth_hash = health_birth_hash(request)
        legacy_birth_hash = health_birth_hash_legacy(request)
        with get_conn() as conn:
            ensure_ai_health_insights_table(conn, execute)
            cur = execute(
                conn,
                """
                SELECT insights_data
                FROM ai_health_insights
                WHERE userid = %s AND birth_hash IN (%s, %s)
                """,
                (current_user.userid, birth_hash, legacy_birth_hash),
            )
            result = cur.fetchone()
        
        if result:
            analysis_data = json.loads(result[0])
            analysis_data['cached'] = True
            return {"analysis": analysis_data}
        
        return {"analysis": None}
        
    except Exception as e:
        print(f"Error fetching previous analysis: {e}")
        return {"analysis": None}

@router.post("/ai-insights")
async def generate_health_ai_insights(
    request: HealthAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """Alias for POST /health/analyze (job + polling)."""
    return await analyze_health(request, background_tasks, current_user)

@router.post("/overall-assessment")
async def get_overall_health_assessment(request: HealthAnalysisRequest, current_user: User = Depends(get_current_user)):
    """Get overall health assessment with technical analysis"""
    try:
        # Create birth data object
        from types import SimpleNamespace
        birth_data = SimpleNamespace(
            date=request.date,
            time=request.time,
            place=request.place,
            latitude=request.latitude or 28.6139,
            longitude=request.longitude or 77.2090,
            timezone=request.timezone or 'UTC+0'
        )
        
        # Calculate birth chart
        from calculators.chart_calculator import ChartCalculator
        chart_calc = ChartCalculator({})
        chart_data = chart_calc.calculate_chart(birth_data)
        
        # Calculate health analysis
        from calculators.health_calculator import HealthCalculator
        health_calc = HealthCalculator(chart_data, birth_data)
        health_analysis = health_calc.calculate_overall_health()
        
        return {
            "status": "success",
            "data": health_analysis
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Health calculation error: {error_details}")
        raise HTTPException(status_code=500, detail=f"Health calculation error: {str(e)}\n{error_details}")

@router.get("/test")
async def test_health_routes():
    """Test endpoint to verify health routes are working"""
    return {"status": "success", "message": "Health routes are working"}
