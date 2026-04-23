"""Marriage Analysis API Routes"""

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

from marriage.marriage_analysis_execute import (
    execute_marriage_analysis,
    marriage_birth_hash,
    marriage_birth_hash_legacy,
    ensure_ai_marriage_insights_table,
)


class MarriageAnalysisRequest(BaseModel):
    chart_id: Optional[int] = None
    name: Optional[str] = None
    date: str
    time: str
    place: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    language: Optional[str] = "english"
    response_style: Optional[str] = "detailed"
    force_regenerate: Optional[bool] = False


router = APIRouter(prefix="/marriage", tags=["marriage"])
credit_service = CreditService()


def _marriage_credit_check_or_raise(current_user: User) -> int:
    base_cost = credit_service.get_credit_setting("marriage_analysis_cost")
    marriage_cost = credit_service.get_effective_cost(current_user.userid, base_cost, "marriage_analysis_cost")
    user_balance = credit_service.get_user_credits(current_user.userid)
    if user_balance < marriage_cost:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits. You need {marriage_cost} credits but have {user_balance}.",
        )
    return marriage_cost


def init_marriage_analysis_jobs_table():
    with get_conn() as conn:
        execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS marriage_analysis_jobs (
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
        execute(conn, "CREATE INDEX IF NOT EXISTS idx_marriage_jobs_user ON marriage_analysis_jobs (user_id)")
        execute(conn, "CREATE INDEX IF NOT EXISTS idx_marriage_jobs_status ON marriage_analysis_jobs (status)")
        conn.commit()


async def process_marriage_analysis_job(job_id: str, user_id: int, request_json: str, marriage_cost: int):
    try:
        req_data = json.loads(request_json)
        request = MarriageAnalysisRequest(**req_data)

        with get_conn() as conn:
            execute(
                conn,
                "UPDATE marriage_analysis_jobs SET status = %s, started_at = %s WHERE job_id = %s",
                ("processing", datetime.now(), job_id),
            )
            conn.commit()

        result = await execute_marriage_analysis(
            user_id,
            request,
            marriage_cost,
            credit_service=credit_service,
            get_conn=get_conn,
            execute_fn=execute,
        )

        with get_conn() as conn:
            if result.get("ok"):
                payload = {
                    "marriage_insights": result["marriage_insights"],
                    "cached": result.get("cached", False),
                }
                execute(
                    conn,
                    """
                    UPDATE marriage_analysis_jobs
                    SET status = %s, result_data = %s, completed_at = %s
                    WHERE job_id = %s
                    """,
                    ("completed", json.dumps(payload), datetime.now(), job_id),
                )
            else:
                execute(
                    conn,
                    """
                    UPDATE marriage_analysis_jobs
                    SET status = %s, error_message = %s, completed_at = %s
                    WHERE job_id = %s
                    """,
                    ("failed", result.get("error") or "Analysis failed", datetime.now(), job_id),
                )
            conn.commit()
    except Exception as e:
        print(f"❌ process_marriage_analysis_job: {e}")
        import traceback

        traceback.print_exc()
        with get_conn() as conn:
            execute(
                conn,
                """
                UPDATE marriage_analysis_jobs
                SET status = %s, error_message = %s, completed_at = %s
                WHERE job_id = %s
                """,
                ("failed", str(e), datetime.now(), job_id),
            )
            conn.commit()


@router.post("/analyze/start")
async def start_marriage_analysis_job(
    request: MarriageAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """Start marriage AI in background; poll GET /marriage/analyze/status/{job_id}."""
    marriage_cost = _marriage_credit_check_or_raise(current_user)
    init_marriage_analysis_jobs_table()
    job_id = str(uuid.uuid4())
    req_dump = request.model_dump() if hasattr(request, "model_dump") else request.dict()
    request_json = json.dumps(req_dump)

    with get_conn() as conn:
        execute(
            conn,
            """
            INSERT INTO marriage_analysis_jobs (job_id, user_id, status, request_json)
            VALUES (%s, %s, %s, %s)
            """,
            (job_id, current_user.userid, "pending", request_json),
        )
        conn.commit()

    background_tasks.add_task(
        process_marriage_analysis_job,
        job_id,
        current_user.userid,
        request_json,
        marriage_cost,
    )

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Marriage analysis started — poll status until completed.",
    }


@router.get("/analyze/status/{job_id}")
async def get_marriage_analysis_job_status(job_id: str, current_user: User = Depends(get_current_user)):
    init_marriage_analysis_jobs_table()
    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT status, result_data, error_message, started_at, completed_at
            FROM marriage_analysis_jobs
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
        out["data"] = payload.get("marriage_insights")
        out["cached"] = payload.get("cached", False)
        out["completed_at"] = completed_at
    elif status == "failed":
        out["error"] = error_message or "Analysis failed"
    elif status in ("pending", "processing"):
        out["message"] = "Analyzing chart and generating marriage insights..."
        if started_at:
            out["started_at"] = started_at
    return out


@router.post("/analyze")
async def analyze_marriage(
    request: MarriageAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """Mobile/web: returns job_id — poll GET /marriage/analyze/status/{job_id}."""
    return await start_marriage_analysis_job(request, background_tasks, current_user)


@router.post("/check-cache")
async def check_marriage_cache(request: MarriageAnalysisRequest, current_user: User = Depends(get_current_user)):
    """Return cached marriage insights if present (same birth hash as /analyze)."""
    try:
        birth_hash = marriage_birth_hash(request)
        legacy_birth_hash = marriage_birth_hash_legacy(request)

        with get_conn() as conn:
            ensure_ai_marriage_insights_table(conn, execute)
            cur = execute(
                conn,
                """
                SELECT insights_data FROM ai_marriage_insights
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
        print(f"❌ Marriage check-cache error: {e}")
        return {"success": False, "message": str(e)}
