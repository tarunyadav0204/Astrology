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

from progeny.progeny_analysis_execute import (
    execute_progeny_analysis,
    progeny_birth_hash,
    progeny_birth_hash_legacy,
    ensure_ai_progeny_insights_table,
)


class ProgenyAnalysisRequest(BaseModel):
    chart_id: Optional[int] = None
    name: Optional[str] = None
    date: str
    time: str
    place: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    gender: str  # Mandatory for Progeny
    language: Optional[str] = "english"
    response_style: Optional[str] = "detailed"
    force_regenerate: Optional[bool] = False
    analysis_focus: str = "first_child"
    children_count: int = 0


router = APIRouter(prefix="/progeny", tags=["progeny"])
credit_service = CreditService()


def _progeny_credit_check_or_raise(current_user: User) -> int:
    base_cost = credit_service.get_credit_setting("progeny_analysis_cost") or 15
    analysis_cost = credit_service.get_effective_cost(current_user.userid, base_cost, "progeny_analysis_cost")
    user_balance = credit_service.get_user_credits(current_user.userid)
    if user_balance < analysis_cost:
        raise HTTPException(status_code=402, detail=f"Insufficient credits. Need {analysis_cost}")
    return analysis_cost


def init_progeny_analysis_jobs_table():
    with get_conn() as conn:
        execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS progeny_analysis_jobs (
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
        execute(conn, "CREATE INDEX IF NOT EXISTS idx_progeny_jobs_user ON progeny_analysis_jobs (user_id)")
        execute(conn, "CREATE INDEX IF NOT EXISTS idx_progeny_jobs_status ON progeny_analysis_jobs (status)")
        conn.commit()


async def process_progeny_analysis_job(job_id: str, user_id: int, request_json: str, analysis_cost: int):
    try:
        req_data = json.loads(request_json)
        request = ProgenyAnalysisRequest(**req_data)

        with get_conn() as conn:
            execute(
                conn,
                "UPDATE progeny_analysis_jobs SET status = %s, started_at = %s WHERE job_id = %s",
                ("processing", datetime.now(), job_id),
            )
            conn.commit()

        result = await execute_progeny_analysis(
            user_id,
            request,
            analysis_cost,
            credit_service=credit_service,
            get_conn=get_conn,
            execute_fn=execute,
        )

        with get_conn() as conn:
            if result.get("ok"):
                payload = {
                    "progeny_insights": result["progeny_insights"],
                    "cached": result.get("cached", False),
                }
                execute(
                    conn,
                    """
                    UPDATE progeny_analysis_jobs
                    SET status = %s, result_data = %s, completed_at = %s
                    WHERE job_id = %s
                    """,
                    ("completed", json.dumps(payload), datetime.now(), job_id),
                )
            else:
                execute(
                    conn,
                    """
                    UPDATE progeny_analysis_jobs
                    SET status = %s, error_message = %s, completed_at = %s
                    WHERE job_id = %s
                    """,
                    ("failed", result.get("error") or "Analysis failed", datetime.now(), job_id),
                )
            conn.commit()
    except Exception as e:
        print(f"❌ process_progeny_analysis_job: {e}")
        import traceback

        traceback.print_exc()
        with get_conn() as conn:
            execute(
                conn,
                """
                UPDATE progeny_analysis_jobs
                SET status = %s, error_message = %s, completed_at = %s
                WHERE job_id = %s
                """,
                ("failed", str(e), datetime.now(), job_id),
            )
            conn.commit()


@router.post("/ai-insights/start")
async def start_progeny_insights_job(
    request: ProgenyAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """Start progeny AI in background; poll GET /progeny/ai-insights/status/{job_id}."""
    if not request.gender or not request.gender.strip():
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "GENDER_REQUIRED",
                "message": "Gender is required for progeny analysis. Please update your profile to continue.",
            },
        )

    analysis_cost = _progeny_credit_check_or_raise(current_user)
    init_progeny_analysis_jobs_table()
    job_id = str(uuid.uuid4())
    req_dump = request.model_dump() if hasattr(request, "model_dump") else request.dict()
    request_json = json.dumps(req_dump)

    with get_conn() as conn:
        execute(
            conn,
            """
            INSERT INTO progeny_analysis_jobs (job_id, user_id, status, request_json)
            VALUES (%s, %s, %s, %s)
            """,
            (job_id, current_user.userid, "pending", request_json),
        )
        conn.commit()

    background_tasks.add_task(
        process_progeny_analysis_job,
        job_id,
        current_user.userid,
        request_json,
        analysis_cost,
    )

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Progeny analysis started — poll status until completed.",
    }


@router.get("/ai-insights/status/{job_id}")
async def get_progeny_analysis_job_status(job_id: str, current_user: User = Depends(get_current_user)):
    init_progeny_analysis_jobs_table()
    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT status, result_data, error_message, started_at, completed_at
            FROM progeny_analysis_jobs
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
        out["data"] = payload.get("progeny_insights")
        out["cached"] = payload.get("cached", False)
        out["completed_at"] = completed_at
    elif status == "failed":
        out["error"] = error_message or "Analysis failed"
    elif status in ("pending", "processing"):
        out["message"] = "Analyzing chart and generating progeny insights..."
        if started_at:
            out["started_at"] = started_at
    return out


@router.post("/ai-insights")
async def get_progeny_insights(
    request: ProgenyAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """Mobile/web: returns job_id — poll GET /progeny/ai-insights/status/{job_id}."""
    return await start_progeny_insights_job(request, background_tasks, current_user)


@router.post("/check-cache")
async def check_progeny_cache(request: ProgenyAnalysisRequest, current_user: User = Depends(get_current_user)):
    try:
        birth_hash = progeny_birth_hash(request)
        legacy_birth_hash = progeny_birth_hash_legacy(request)
        with get_conn() as conn:
            ensure_ai_progeny_insights_table(conn, execute)
            cur = execute(
                conn,
                """
                SELECT insights_data FROM ai_progeny_insights
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
        print(f"❌ Progeny check-cache error: {e}")
        return {"success": False, "message": str(e)}
