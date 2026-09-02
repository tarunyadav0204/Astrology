from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Mapping, Optional, Sequence

from db import execute, get_conn

from .engine import RECTIFICATION_ENGINE_VERSION
from .registry import RECTIFICATION_REGISTRY_VERSION
from .schema import ensure_rectification_schema


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _decoded(value: Any) -> Any:
    if value is None or isinstance(value, (dict, list)):
        return value
    return json.loads(value)


class RectificationRepository:
    def create_case(
        self,
        *,
        userid: int,
        birth_chart_id: int,
        chart_input_hash: str,
        window_start_seconds: int,
        window_end_seconds: int,
    ) -> Dict[str, Any]:
        case_id = str(uuid.uuid4())
        with get_conn() as conn:
            ensure_rectification_schema(conn)
            execute(
                conn,
                """
                INSERT INTO rectification_cases
                    (id, userid, birth_chart_id, chart_input_hash,
                     window_start_seconds, window_end_seconds)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (case_id, userid, birth_chart_id, chart_input_hash,
                 window_start_seconds, window_end_seconds),
            )
            conn.commit()
        return self.get_case(case_id=case_id, userid=userid)

    def get_case(self, *, case_id: str, userid: int) -> Optional[Dict[str, Any]]:
        with get_conn() as conn:
            ensure_rectification_schema(conn)
            row = execute(
                conn,
                """
                SELECT id, userid, birth_chart_id, chart_input_hash,
                       window_start_seconds, window_end_seconds, status,
                       active_run_id, created_at, updated_at
                FROM rectification_cases WHERE id = %s AND userid = %s
                """,
                (case_id, userid),
            ).fetchone()
        if not row:
            return None
        return {
            "id": row[0], "userid": row[1], "birth_chart_id": row[2],
            "chart_input_hash": row[3], "window_start_seconds": row[4],
            "window_end_seconds": row[5], "status": row[6],
            "active_run_id": row[7], "created_at": row[8], "updated_at": row[9],
        }

    def add_event(self, *, case_id: str, userid: int, event: Mapping[str, Any]) -> Dict[str, Any]:
        with get_conn() as conn:
            ensure_rectification_schema(conn)
            owned = execute(
                conn, "SELECT 1 FROM rectification_cases WHERE id = %s AND userid = %s",
                (case_id, userid),
            ).fetchone()
            if not owned:
                raise KeyError("Rectification case not found")
            row = execute(
                conn,
                """
                INSERT INTO rectification_events
                    (case_id, userid, event_type, subtype, subject, date_start,
                     date_end, precision, source_reliability, metadata_json)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                RETURNING id
                """,
                (
                    case_id, userid, event["event_type"], event.get("subtype") or "",
                    event.get("subject") or "self", event["date_start"], event["date_end"],
                    event["precision"], event["source_reliability"], _json(event.get("metadata") or {}),
                ),
            ).fetchone()
            execute(
                conn,
                """
                UPDATE rectification_cases
                SET active_run_id = NULL, status = 'draft', updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (case_id,),
            )
            conn.commit()
        return self.get_event(event_id=int(row[0]), userid=userid)

    def get_event(self, *, event_id: int, userid: int) -> Optional[Dict[str, Any]]:
        with get_conn() as conn:
            ensure_rectification_schema(conn)
            row = execute(
                conn,
                """
                SELECT id, case_id, event_type, subtype, subject, date_start, date_end,
                       precision, source_reliability, metadata_json, active, created_at, updated_at
                FROM rectification_events WHERE id = %s AND userid = %s
                """,
                (event_id, userid),
            ).fetchone()
        return self._event_row(row) if row else None

    @staticmethod
    def _event_row(row) -> Dict[str, Any]:
        return {
            "id": row[0], "case_id": row[1], "event_type": row[2], "subtype": row[3],
            "subject": row[4], "date_start": row[5], "date_end": row[6],
            "precision": row[7], "source_reliability": row[8],
            "metadata": _decoded(row[9]) or {}, "active": bool(row[10]),
            "created_at": row[11], "updated_at": row[12],
        }

    def list_events(self, *, case_id: str, userid: int) -> List[Dict[str, Any]]:
        with get_conn() as conn:
            ensure_rectification_schema(conn)
            rows = execute(
                conn,
                """
                SELECT id, case_id, event_type, subtype, subject, date_start, date_end,
                       precision, source_reliability, metadata_json, active, created_at, updated_at
                FROM rectification_events
                WHERE case_id = %s AND userid = %s AND active = TRUE
                ORDER BY date_start, id
                """,
                (case_id, userid),
            ).fetchall() or []
        return [self._event_row(row) for row in rows]

    def update_event(self, *, event_id: int, userid: int, changes: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
        allowed = {
            "date_start", "date_end", "precision", "source_reliability",
            "subtype", "subject", "metadata",
        }
        fields = []
        params: List[Any] = []
        for key, value in changes.items():
            if key not in allowed or value is None:
                continue
            column = "metadata_json" if key == "metadata" else key
            fields.append(f"{column} = %s" + ("::jsonb" if key == "metadata" else ""))
            params.append(_json(value) if key == "metadata" else value)
        if not fields:
            return self.get_event(event_id=event_id, userid=userid)
        params.extend([event_id, userid])
        with get_conn() as conn:
            ensure_rectification_schema(conn)
            row = execute(
                conn,
                f"UPDATE rectification_events SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP "
                "WHERE id = %s AND userid = %s RETURNING case_id",
                tuple(params),
            ).fetchone()
            if row:
                execute(
                    conn,
                    """
                    UPDATE rectification_cases
                    SET active_run_id = NULL, status = 'draft', updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND userid = %s
                    """,
                    (row[0], userid),
                )
            conn.commit()
        return self.get_event(event_id=event_id, userid=userid)

    def deactivate_event(self, *, event_id: int, userid: int) -> bool:
        with get_conn() as conn:
            ensure_rectification_schema(conn)
            row = execute(
                conn,
                """
                UPDATE rectification_events
                SET active = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND userid = %s AND active = TRUE
                RETURNING case_id
                """,
                (event_id, userid),
            ).fetchone()
            if row:
                execute(
                    conn,
                    """
                    UPDATE rectification_cases
                    SET active_run_id = NULL, status = 'draft', updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND userid = %s
                    """,
                    (row[0], userid),
                )
            conn.commit()
        return bool(row)

    def find_reusable_run(self, *, case_id: str, userid: int, input_hash: str) -> Optional[Dict[str, Any]]:
        with get_conn() as conn:
            ensure_rectification_schema(conn)
            row = execute(
                conn,
                """
                SELECT id FROM rectification_runs
                WHERE case_id = %s AND userid = %s AND input_hash = %s
                  AND status IN ('pending', 'processing', 'completed')
                ORDER BY created_at DESC LIMIT 1
                """,
                (case_id, userid, input_hash),
            ).fetchone()
        return self.get_run(run_id=row[0], userid=userid) if row else None

    def create_run(
        self, *, case_id: str, userid: int, input_hash: str,
        input_snapshot: Mapping[str, Any], minute_step: int
    ) -> Dict[str, Any]:
        run_id = str(uuid.uuid4())
        with get_conn() as conn:
            ensure_rectification_schema(conn)
            execute(
                conn,
                """
                INSERT INTO rectification_runs
                    (id, case_id, userid, minute_step, input_hash, input_json,
                     engine_version, registry_version)
                VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s)
                """,
                (run_id, case_id, userid, minute_step, input_hash, _json(input_snapshot),
                 RECTIFICATION_ENGINE_VERSION, RECTIFICATION_REGISTRY_VERSION),
            )
            execute(
                conn,
                """
                UPDATE rectification_cases
                SET active_run_id = %s, status = 'queued', updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND userid = %s
                """,
                (run_id, case_id, userid),
            )
            conn.commit()
        return self.get_run(run_id=run_id, userid=userid)

    def claim_run(self, *, run_id: str) -> Optional[Dict[str, Any]]:
        with get_conn() as conn:
            ensure_rectification_schema(conn)
            row = execute(
                conn,
                """
                UPDATE rectification_runs
                SET status = 'processing', stage = 'scanning_candidates',
                    started_at = COALESCE(started_at, CURRENT_TIMESTAMP),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND status = 'pending'
                RETURNING userid
                """,
                (run_id,),
            ).fetchone()
            conn.commit()
        return self.get_run(run_id=run_id, userid=int(row[0])) if row else None

    def update_progress(self, *, run_id: str, current: int, total: int, stage: str) -> None:
        with get_conn() as conn:
            ensure_rectification_schema(conn)
            execute(
                conn,
                """
                UPDATE rectification_runs
                SET progress_current = %s, progress_total = %s, stage = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND status = 'processing'
                """,
                (current, total, stage, run_id),
            )
            conn.commit()

    def complete_run(self, *, run_id: str, result: Mapping[str, Any]) -> None:
        clusters = list(result.get("clusters") or [])
        with get_conn() as conn:
            ensure_rectification_schema(conn)
            execute(conn, "DELETE FROM rectification_result_clusters WHERE run_id = %s", (run_id,))
            for cluster in clusters:
                best = cluster.get("best_candidate") or {}
                execute(
                    conn,
                    """
                    INSERT INTO rectification_result_clusters
                        (run_id, rank, start_local_time, end_local_time, best_local_time,
                         relative_fit, evidence_json)
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
                    """,
                    (
                        run_id, cluster["rank"], cluster["start_local_time"],
                        cluster["end_local_time"], best["candidate_local_time"],
                        cluster["relative_fit"], _json(cluster),
                    ),
                )
            execute(
                conn,
                """
                UPDATE rectification_runs
                SET status = 'completed', stage = 'completed', result_json = %s::jsonb,
                    progress_current = progress_total, completed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (_json(result), run_id),
            )
            execute(
                conn,
                """
                UPDATE rectification_cases SET status = 'completed', updated_at = CURRENT_TIMESTAMP
                WHERE active_run_id = %s
                """,
                (run_id,),
            )
            conn.commit()

    def fail_run(self, *, run_id: str, error: str) -> None:
        with get_conn() as conn:
            ensure_rectification_schema(conn)
            execute(
                conn,
                """
                UPDATE rectification_runs
                SET status = 'failed', stage = 'failed', error_text = %s,
                    completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (str(error)[:2000], run_id),
            )
            execute(
                conn,
                "UPDATE rectification_cases SET status = 'failed', updated_at = CURRENT_TIMESTAMP WHERE active_run_id = %s",
                (run_id,),
            )
            conn.commit()

    def get_run(self, *, run_id: str, userid: int) -> Optional[Dict[str, Any]]:
        with get_conn() as conn:
            ensure_rectification_schema(conn)
            row = execute(
                conn,
                """
                SELECT id, case_id, userid, status, stage, progress_current, progress_total,
                       minute_step, input_hash, input_json, engine_version, registry_version, result_json,
                       error_text, created_at, started_at, completed_at, updated_at
                FROM rectification_runs WHERE id = %s AND userid = %s
                """,
                (run_id, userid),
            ).fetchone()
        if not row:
            return None
        return {
            "id": row[0], "case_id": row[1], "userid": row[2], "status": row[3],
            "stage": row[4], "progress_current": row[5], "progress_total": row[6],
            "minute_step": row[7], "input_hash": row[8], "input_snapshot": _decoded(row[9]),
            "engine_version": row[10], "registry_version": row[11],
            "result": _decoded(row[12]), "error": row[13],
            "created_at": row[14], "started_at": row[15], "completed_at": row[16],
            "updated_at": row[17],
        }
