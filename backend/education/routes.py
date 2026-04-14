"""Education Analysis API Routes"""

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
from calculators.chart_calculator import ChartCalculator
from .education_analyzer import EducationAnalyzer
from db import get_conn, execute

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from education.education_analysis_execute import (
    execute_education_analysis,
    education_birth_hash,
    education_birth_hash_legacy,
    ensure_ai_education_insights_table,
)


class EducationAnalysisRequest(BaseModel):
    chart_id: Optional[int] = None
    name: Optional[str] = None
    date: str
    time: str
    place: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    gender: Optional[str] = None
    language: Optional[str] = "english"
    response_style: Optional[str] = "detailed"
    force_regenerate: Optional[bool] = False


router = APIRouter(prefix="/education", tags=["education"])
credit_service = CreditService()


def _education_credit_check_or_raise(current_user: User) -> int:
    base_cost = credit_service.get_credit_setting("education_analysis_cost")
    education_cost = credit_service.get_effective_cost(current_user.userid, base_cost, "education_analysis_cost")
    user_balance = credit_service.get_user_credits(current_user.userid)
    if user_balance < education_cost:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits. You need {education_cost} credits but have {user_balance}.",
        )
    return education_cost


def init_education_analysis_jobs_table():
    with get_conn() as conn:
        execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS education_analysis_jobs (
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
        execute(conn, "CREATE INDEX IF NOT EXISTS idx_education_jobs_user ON education_analysis_jobs (user_id)")
        execute(conn, "CREATE INDEX IF NOT EXISTS idx_education_jobs_status ON education_analysis_jobs (status)")
        conn.commit()


async def process_education_analysis_job(job_id: str, user_id: int, request_json: str, education_cost: int):
    try:
        req_data = json.loads(request_json)
        request = EducationAnalysisRequest(**req_data)

        with get_conn() as conn:
            execute(
                conn,
                "UPDATE education_analysis_jobs SET status = %s, started_at = %s WHERE job_id = %s",
                ("processing", datetime.now(), job_id),
            )
            conn.commit()

        result = await execute_education_analysis(
            user_id,
            request,
            education_cost,
            credit_service=credit_service,
            get_conn=get_conn,
            execute_fn=execute,
        )

        with get_conn() as conn:
            if result.get("ok"):
                payload = {
                    "education_insights": result["education_insights"],
                    "cached": result.get("cached", False),
                }
                execute(
                    conn,
                    """
                    UPDATE education_analysis_jobs
                    SET status = %s, result_data = %s, completed_at = %s
                    WHERE job_id = %s
                    """,
                    ("completed", json.dumps(payload), datetime.now(), job_id),
                )
            else:
                execute(
                    conn,
                    """
                    UPDATE education_analysis_jobs
                    SET status = %s, error_message = %s, completed_at = %s
                    WHERE job_id = %s
                    """,
                    ("failed", result.get("error") or "Analysis failed", datetime.now(), job_id),
                )
            conn.commit()
    except Exception as e:
        print(f"❌ process_education_analysis_job: {e}")
        import traceback

        traceback.print_exc()
        with get_conn() as conn:
            execute(
                conn,
                """
                UPDATE education_analysis_jobs
                SET status = %s, error_message = %s, completed_at = %s
                WHERE job_id = %s
                """,
                ("failed", str(e), datetime.now(), job_id),
            )
            conn.commit()


@router.post("/ai-analyze/start")
async def start_education_analysis_job(
    request: EducationAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """Start education AI in background; poll GET /education/ai-analyze/status/{job_id}."""
    education_cost = _education_credit_check_or_raise(current_user)
    init_education_analysis_jobs_table()
    job_id = str(uuid.uuid4())
    req_dump = request.model_dump() if hasattr(request, "model_dump") else request.dict()
    request_json = json.dumps(req_dump)

    with get_conn() as conn:
        execute(
            conn,
            """
            INSERT INTO education_analysis_jobs (job_id, user_id, status, request_json)
            VALUES (%s, %s, %s, %s)
            """,
            (job_id, current_user.userid, "pending", request_json),
        )
        conn.commit()

    background_tasks.add_task(
        process_education_analysis_job,
        job_id,
        current_user.userid,
        request_json,
        education_cost,
    )

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Education analysis started — poll status until completed.",
    }


@router.get("/ai-analyze/status/{job_id}")
async def get_education_analysis_job_status(job_id: str, current_user: User = Depends(get_current_user)):
    init_education_analysis_jobs_table()
    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT status, result_data, error_message, started_at, completed_at
            FROM education_analysis_jobs
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
        out["data"] = payload.get("education_insights")
        out["cached"] = payload.get("cached", False)
        out["completed_at"] = completed_at
    elif status == "failed":
        out["error"] = error_message or "Analysis failed"
    elif status in ("pending", "processing"):
        out["message"] = "Analyzing chart and generating education insights..."
        if started_at:
            out["started_at"] = started_at
    return out


@router.post("/ai-analyze")
async def analyze_education_ai(
    request: EducationAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """Mobile/web: returns job_id — poll GET /education/ai-analyze/status/{job_id}."""
    return await start_education_analysis_job(request, background_tasks, current_user)


@router.post("/analyze")
async def analyze_education(
    request: EducationAnalysisRequest,
    current_user: User = Depends(get_current_user),
):
    """Classical education analysis endpoint (non-AI)."""
    try:
        birth_data = {
            "date": request.date,
            "time": request.time,
            "place": request.place,
            "latitude": request.latitude or 28.6139,
            "longitude": request.longitude or 77.2090,
            "timezone": request.timezone or "UTC+0",
        }

        from types import SimpleNamespace

        birth_obj = SimpleNamespace(**birth_data)
        chart_calc = ChartCalculator({})
        chart_data = chart_calc.calculate_chart(birth_obj)

        analyzer = EducationAnalyzer(birth_data, chart_data)
        analysis = analyzer.analyze_education()

        return {
            "success": True,
            "analysis": analysis,
            "birth_data": birth_data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/get-analysis")
async def get_previous_education_analysis(request: EducationAnalysisRequest, current_user: User = Depends(get_current_user)):
    """Get previously generated education analysis if exists."""
    try:
        birth_hash = education_birth_hash(request)
        legacy_birth_hash = education_birth_hash_legacy(request)
        with get_conn() as conn:
            ensure_ai_education_insights_table(conn, execute)
            cur = execute(
                conn,
                """
                SELECT insights_data
                FROM ai_education_insights
                WHERE userid = %s AND birth_hash IN (%s, %s)
                """,
                (current_user.userid, birth_hash, legacy_birth_hash),
            )
            result = cur.fetchone()

        if result:
            analysis_data = json.loads(result[0])
            analysis_data["cached"] = True
            return {"analysis": analysis_data}

        return {"analysis": None}
    except Exception as e:
        print(f"Error fetching previous analysis: {e}")
        return {"analysis": None}


@router.get("/constants")
async def get_education_constants():
    """Get education analysis constants and explanations."""
    from .constants import EDUCATION_HOUSES, EDUCATION_PLANETS, SUBJECT_RECOMMENDATIONS

    return {
        "houses": EDUCATION_HOUSES,
        "planets": EDUCATION_PLANETS,
        "subjects": SUBJECT_RECOMMENDATIONS,
    }
