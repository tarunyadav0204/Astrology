"""Karma Analysis Routes - API endpoints for past life karma analysis."""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
import os
import sys
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import get_current_user, User
from ai.karma_gemini_analyzer import KarmaGeminiAnalyzer
from credits.credit_service import CreditService
from db import get_conn, execute

load_dotenv()

router = APIRouter()
credit_service = CreditService()


class KarmaAnalysisRequest(BaseModel):
    chart_id: str
    force_regenerate: bool = False


def _load_chart_data(chart_id: str, user_id: int) -> dict:
    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT name, date, time, latitude, longitude, timezone, place, gender
            FROM birth_charts
            WHERE id = %s AND userid = %s
            """,
            (chart_id, user_id),
        )
        result = cur.fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="Chart not found")

    from encryption_utils import EncryptionManager

    try:
        encryptor = EncryptionManager()
    except ValueError:
        encryptor = None

    if encryptor:
        return {
            "name": encryptor.decrypt(result[0]),
            "date": encryptor.decrypt(result[1]),
            "time": encryptor.decrypt(result[2]),
            "latitude": float(encryptor.decrypt(str(result[3]))),
            "longitude": float(encryptor.decrypt(str(result[4]))),
            "timezone": result[5],
            "place": encryptor.decrypt(result[6] or ""),
            "gender": result[7] or "",
        }

    return {
        "name": result[0],
        "date": result[1],
        "time": result[2],
        "latitude": result[3],
        "longitude": result[4],
        "timezone": result[5],
        "place": result[6] or "",
        "gender": result[7] or "",
    }


def init_karma_analysis_jobs_table():
    with get_conn() as conn:
        execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS karma_analysis_jobs (
                job_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                chart_id TEXT NOT NULL,
                status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
                result_data TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP
            )
            """,
        )
        execute(conn, "CREATE INDEX IF NOT EXISTS idx_karma_jobs_user ON karma_analysis_jobs (user_id)")
        execute(conn, "CREATE INDEX IF NOT EXISTS idx_karma_jobs_chart ON karma_analysis_jobs (chart_id)")
        execute(conn, "CREATE INDEX IF NOT EXISTS idx_karma_jobs_status ON karma_analysis_jobs (status)")
        # Ensure legacy/prod DBs have karma_insights + unique constraint required by ON CONFLICT.
        execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS karma_insights (
                id SERIAL PRIMARY KEY,
                chart_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                karma_context TEXT,
                ai_interpretation TEXT,
                sections TEXT,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
        )
        cur = execute(
            conn,
            """
            SELECT 1
            FROM information_schema.table_constraints
            WHERE table_schema = 'public'
              AND table_name = 'karma_insights'
              AND constraint_name = 'karma_insights_chart_user_key'
            """,
        )
        has_unique = cur.fetchone()
        if not has_unique:
            # Keep newest row per (chart_id, user_id) before adding unique constraint.
            execute(
                conn,
                """
                DELETE FROM karma_insights a
                USING karma_insights b
                WHERE a.chart_id = b.chart_id
                  AND a.user_id = b.user_id
                  AND a.id < b.id
                """,
            )
            execute(
                conn,
                """
                ALTER TABLE karma_insights
                ADD CONSTRAINT karma_insights_chart_user_key UNIQUE (chart_id, user_id)
                """,
            )
        conn.commit()


def process_karma_analysis_background(job_id: str, chart_id: str, user_id: int, birth_data: dict, karma_cost: int):
    """Background task to process karma analysis and persist to job + cache tables."""
    try:
        with get_conn() as conn:
            execute(
                conn,
                "UPDATE karma_analysis_jobs SET status = 'processing', started_at = CURRENT_TIMESTAMP WHERE job_id = %s",
                (job_id,),
            )
            execute(
                conn,
                """
                INSERT INTO karma_insights (chart_id, user_id, status, created_at, updated_at)
                VALUES (%s, %s, 'processing', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (chart_id, user_id)
                DO UPDATE SET status = EXCLUDED.status, updated_at = EXCLUDED.updated_at
                """,
                (chart_id, user_id),
            )
            conn.commit()

        from types import SimpleNamespace

        birth_obj = SimpleNamespace(**birth_data)
        from calculators.chart_calculator import ChartCalculator

        chart_calc = ChartCalculator({})
        chart_data = chart_calc.calculate_chart(birth_obj)

        from calculators.divisional_chart_calculator import DivisionalChartCalculator

        div_calc = DivisionalChartCalculator(chart_data)
        d9_result = div_calc.calculate_divisional_chart(9)
        d60_result = div_calc.calculate_divisional_chart(60)
        divisional_charts = {
            "d9_navamsa": d9_result["divisional_chart"],
            "d60_shashtiamsa": d60_result["divisional_chart"],
        }

        api_key = os.getenv("GEMINI_API_KEY")
        analyzer = KarmaGeminiAnalyzer(api_key)
        analysis = analyzer.analyze_karma(
            chart_data,
            divisional_charts,
            native_name=birth_data.get("name", "the native"),
            log_request=True,
        )

        if analysis.get("success"):
            payload = {
                "karma_context": analysis["karma_context"],
                "ai_interpretation": analysis["ai_interpretation"],
                "sections": analysis["sections"],
            }

            with get_conn() as conn:
                execute(
                    conn,
                    """
                    UPDATE karma_insights
                    SET status = 'complete',
                        karma_context = %s,
                        ai_interpretation = %s,
                        sections = %s,
                        error = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE chart_id = %s AND user_id = %s
                    """,
                    (
                        json.dumps(analysis["karma_context"]),
                        analysis["ai_interpretation"],
                        json.dumps(analysis["sections"]),
                        chart_id,
                        user_id,
                    ),
                )
                execute(
                    conn,
                    """
                    UPDATE karma_analysis_jobs
                    SET status = 'completed', result_data = %s, completed_at = CURRENT_TIMESTAMP
                    WHERE job_id = %s
                    """,
                    (json.dumps(payload), job_id),
                )
                conn.commit()

            credit_service.spend_credits(
                user_id,
                karma_cost,
                "karma_analysis",
                f"Karma analysis for chart {chart_id}",
            )
        else:
            err = analysis.get("error", "Unknown error")
            with get_conn() as conn:
                execute(
                    conn,
                    """
                    UPDATE karma_insights
                    SET status = 'error', error = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE chart_id = %s AND user_id = %s
                    """,
                    (err, chart_id, user_id),
                )
                execute(
                    conn,
                    """
                    UPDATE karma_analysis_jobs
                    SET status = 'failed', error_message = %s, completed_at = CURRENT_TIMESTAMP
                    WHERE job_id = %s
                    """,
                    (err, job_id),
                )
                conn.commit()
    except Exception as e:
        import traceback

        traceback.print_exc()
        with get_conn() as conn:
            execute(
                conn,
                """
                UPDATE karma_insights
                SET status = 'error', error = %s, updated_at = CURRENT_TIMESTAMP
                WHERE chart_id = %s AND user_id = %s
                """,
                (str(e), chart_id, user_id),
            )
            execute(
                conn,
                """
                UPDATE karma_analysis_jobs
                SET status = 'failed', error_message = %s, completed_at = CURRENT_TIMESTAMP
                WHERE job_id = %s
                """,
                (str(e), job_id),
            )
            conn.commit()


@router.post("/karma-analysis/start")
async def start_karma_analysis(
    request: KarmaAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    base_cost = credit_service.get_credit_setting("karma_analysis_cost") or 25
    karma_cost = credit_service.get_effective_cost(current_user.userid, base_cost, "karma_analysis_cost")
    user_balance = credit_service.get_user_credits(current_user.userid)

    if user_balance < karma_cost:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits. You need {karma_cost} credits but have {user_balance}.",
        )

    chart_data = _load_chart_data(request.chart_id, current_user.userid)

    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT status, karma_context, ai_interpretation, sections
            FROM karma_insights
            WHERE chart_id = %s AND user_id = %s
            """,
            (request.chart_id, current_user.userid),
        )
        existing = cur.fetchone()

        if existing and existing[0] == "complete" and not request.force_regenerate:
            return {
                "status": "completed",
                "data": {
                    "karma_context": json.loads(existing[1]),
                    "ai_interpretation": existing[2],
                    "sections": json.loads(existing[3]),
                },
                "cached": True,
            }

    init_karma_analysis_jobs_table()
    job_id = str(uuid.uuid4())
    with get_conn() as conn:
        execute(
            conn,
            """
            INSERT INTO karma_analysis_jobs (job_id, user_id, chart_id, status)
            VALUES (%s, %s, %s, 'pending')
            """,
            (job_id, current_user.userid, request.chart_id),
        )
        conn.commit()

    background_tasks.add_task(
        process_karma_analysis_background,
        job_id,
        request.chart_id,
        current_user.userid,
        chart_data,
        karma_cost,
    )

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Karma analysis started. Poll status endpoint until completed.",
    }


@router.get("/karma-analysis/status/{job_id}")
async def get_karma_status_by_job(job_id: str, current_user: User = Depends(get_current_user)):
    init_karma_analysis_jobs_table()
    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT status, result_data, error_message, completed_at
            FROM karma_analysis_jobs
            WHERE job_id = %s AND user_id = %s
            """,
            (job_id, current_user.userid),
        )
        row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Job not found")

    status, result_data, error_message, completed_at = row
    out = {"status": status}
    if status == "completed" and result_data:
        out["data"] = json.loads(result_data)
        out["completed_at"] = completed_at
    elif status == "failed":
        out["error"] = error_message or "Analysis failed"
    return out


@router.post("/karma-analysis")
async def analyze_karma(
    request: KarmaAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    force_regenerate: bool = False,
):
    """Backward-compatible alias that now returns job_id."""
    if force_regenerate:
        request.force_regenerate = True
    return await start_karma_analysis(request, background_tasks, current_user)


@router.get("/karma-analysis/status")
async def get_karma_status(chart_id: str, current_user: User = Depends(get_current_user)):
    """Backward-compatible status lookup by chart_id."""
    try:
        with get_conn() as conn:
            cur = execute(
                conn,
                """
                SELECT status, karma_context, ai_interpretation, sections, error
                FROM karma_insights
                WHERE chart_id = %s AND user_id = %s
                """,
                (chart_id, current_user.userid),
            )
            result = cur.fetchone()

        if not result:
            return {"status": "not_found"}

        status = result[0]
        if status == "complete":
            return {
                "status": "completed",
                "data": {
                    "karma_context": json.loads(result[1]),
                    "ai_interpretation": result[2],
                    "sections": json.loads(result[3]),
                },
            }
        if status == "error":
            return {"status": "failed", "error": result[4]}
        return {"status": "processing" if status == "processing" else "pending"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
