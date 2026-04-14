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

from career_analysis.career_analysis_execute import (
    execute_career_analysis,
    career_birth_hash,
    career_birth_hash_legacy,
    ensure_ai_career_insights_table,
)


class CareerAnalysisRequest(BaseModel):
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


router = APIRouter(prefix="/career", tags=["career"])
credit_service = CreditService()


def _career_credit_check_or_raise(current_user: User) -> int:
    base_cost = credit_service.get_credit_setting("career_analysis_cost")
    career_cost = credit_service.get_effective_cost(current_user.userid, base_cost, "career_analysis_cost")
    user_balance = credit_service.get_user_credits(current_user.userid)
    if user_balance < career_cost:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits. You need {career_cost} credits but have {user_balance}.",
        )
    return career_cost


def init_career_analysis_jobs_table():
    with get_conn() as conn:
        execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS career_analysis_jobs (
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
        execute(conn, "CREATE INDEX IF NOT EXISTS idx_career_jobs_user ON career_analysis_jobs (user_id)")
        execute(conn, "CREATE INDEX IF NOT EXISTS idx_career_jobs_status ON career_analysis_jobs (status)")
        conn.commit()


async def process_career_analysis_job(job_id: str, user_id: int, request_json: str, career_cost: int):
    try:
        req_data = json.loads(request_json)
        request = CareerAnalysisRequest(**req_data)

        with get_conn() as conn:
            execute(
                conn,
                "UPDATE career_analysis_jobs SET status = %s, started_at = %s WHERE job_id = %s",
                ("processing", datetime.now(), job_id),
            )
            conn.commit()

        result = await execute_career_analysis(
            user_id,
            request,
            career_cost,
            credit_service=credit_service,
            get_conn=get_conn,
            execute_fn=execute,
        )

        with get_conn() as conn:
            if result.get("ok"):
                payload = {
                    "career_insights": result["career_insights"],
                    "cached": result.get("cached", False),
                }
                execute(
                    conn,
                    """
                    UPDATE career_analysis_jobs
                    SET status = %s, result_data = %s, completed_at = %s
                    WHERE job_id = %s
                    """,
                    ("completed", json.dumps(payload), datetime.now(), job_id),
                )
            else:
                execute(
                    conn,
                    """
                    UPDATE career_analysis_jobs
                    SET status = %s, error_message = %s, completed_at = %s
                    WHERE job_id = %s
                    """,
                    ("failed", result.get("error") or "Analysis failed", datetime.now(), job_id),
                )
            conn.commit()
    except Exception as e:
        print(f"❌ process_career_analysis_job: {e}")
        import traceback

        traceback.print_exc()
        with get_conn() as conn:
            execute(
                conn,
                """
                UPDATE career_analysis_jobs
                SET status = %s, error_message = %s, completed_at = %s
                WHERE job_id = %s
                """,
                ("failed", str(e), datetime.now(), job_id),
            )
            conn.commit()


@router.post("/ai-insights/start")
async def start_career_analysis_job(
    request: CareerAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """Start career AI in background; poll GET /career/ai-insights/status/{job_id}."""
    career_cost = _career_credit_check_or_raise(current_user)
    init_career_analysis_jobs_table()
    job_id = str(uuid.uuid4())
    req_dump = request.model_dump() if hasattr(request, "model_dump") else request.dict()
    request_json = json.dumps(req_dump)

    with get_conn() as conn:
        execute(
            conn,
            """
            INSERT INTO career_analysis_jobs (job_id, user_id, status, request_json)
            VALUES (%s, %s, %s, %s)
            """,
            (job_id, current_user.userid, "pending", request_json),
        )
        conn.commit()

    background_tasks.add_task(
        process_career_analysis_job,
        job_id,
        current_user.userid,
        request_json,
        career_cost,
    )

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Career analysis started — poll status until completed.",
    }


@router.get("/ai-insights/status/{job_id}")
async def get_career_analysis_job_status(job_id: str, current_user: User = Depends(get_current_user)):
    init_career_analysis_jobs_table()
    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT status, result_data, error_message, started_at, completed_at
            FROM career_analysis_jobs
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
        out["data"] = payload.get("career_insights")
        out["cached"] = payload.get("cached", False)
        out["completed_at"] = completed_at
    elif status == "failed":
        out["error"] = error_message or "Analysis failed"
    elif status in ("pending", "processing"):
        out["message"] = "Analyzing chart and generating career insights..."
        if started_at:
            out["started_at"] = started_at
    return out


@router.post("/ai-insights")
async def get_career_ai_insights(
    request: CareerAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """Mobile/web: returns job_id — poll GET /career/ai-insights/status/{job_id}."""
    return await start_career_analysis_job(request, background_tasks, current_user)


@router.post("/check-cache")
async def check_career_cache(request: CareerAnalysisRequest, current_user: User = Depends(get_current_user)):
    """Return cached career insights if present (same birth hash as /ai-insights)."""
    try:
        birth_hash = career_birth_hash(request)
        legacy_birth_hash = career_birth_hash_legacy(request)
        with get_conn() as conn:
            ensure_ai_career_insights_table(conn, execute)
            cur = execute(
                conn,
                """
                SELECT insights_data
                FROM ai_career_insights
                WHERE userid = %s AND birth_hash IN (%s, %s)
                """,
                (current_user.userid, birth_hash, legacy_birth_hash),
            )
            row = cur.fetchone()

        if not row or not row[0]:
            return {"success": False, "message": "No cached data found"}

        stored = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        return {"success": True, "cached": True, "analysis": stored}
    except Exception as e:
        print(f"❌ Career check-cache error: {e}")
        return {"success": False, "message": str(e)}
