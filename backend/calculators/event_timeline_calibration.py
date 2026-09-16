"""Immutable forecast snapshots and prospective Event Timeline calibration."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from typing import Any, Dict, Iterable, Mapping, Sequence

from db import execute


CALIBRATION_SCHEMA_VERSION = "event_timeline_calibration_v1"

SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS event_timeline_forecasts (
        id BIGSERIAL PRIMARY KEY,
        job_id TEXT NOT NULL REFERENCES event_timeline_jobs(job_id) ON DELETE CASCADE,
        user_id BIGINT NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
        birth_chart_id BIGINT NOT NULL REFERENCES birth_charts(id) ON DELETE CASCADE,
        candidate_id TEXT NOT NULL,
        target_year INTEGER NOT NULL,
        target_month INTEGER NOT NULL,
        display_rank INTEGER NOT NULL,
        event_key TEXT NOT NULL,
        engine_version TEXT NOT NULL,
        methodology_version TEXT,
        evidence_version TEXT,
        accuracy_layer TEXT,
        support_grade TEXT,
        manifestation_phase TEXT,
        forecast_start DATE,
        forecast_end DATE,
        prediction_hash TEXT NOT NULL,
        forecast_json JSONB NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(job_id, candidate_id, target_month)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS event_timeline_outcomes (
        id BIGSERIAL PRIMARY KEY,
        forecast_id BIGINT NOT NULL UNIQUE REFERENCES event_timeline_forecasts(id) ON DELETE CASCADE,
        user_id BIGINT NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
        occurrence TEXT NOT NULL CHECK (occurrence IN ('occurred', 'partly_occurred', 'did_not_occur')),
        actual_date DATE,
        severity INTEGER CHECK (severity IS NULL OR severity BETWEEN 1 AND 5),
        notes TEXT NOT NULL DEFAULT '',
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS event_timeline_unpredicted_events (
        id BIGSERIAL PRIMARY KEY,
        job_id TEXT NOT NULL REFERENCES event_timeline_jobs(job_id) ON DELETE CASCADE,
        user_id BIGINT NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
        event_key TEXT NOT NULL,
        actual_date DATE NOT NULL,
        severity INTEGER CHECK (severity IS NULL OR severity BETWEEN 1 AND 5),
        notes TEXT NOT NULL DEFAULT '',
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(job_id, user_id, event_key, actual_date)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_timeline_forecasts_calibration ON event_timeline_forecasts(engine_version, accuracy_layer, event_key, target_year)",
    "CREATE INDEX IF NOT EXISTS idx_timeline_outcomes_user ON event_timeline_outcomes(user_id, updated_at DESC)",
)


def ensure_calibration_schema(conn: Any) -> None:
    for statement in SCHEMA_STATEMENTS:
        execute(conn, statement)


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def freeze_forecast(
    conn: Any,
    *,
    job_id: str,
    user_id: int,
    birth_chart_id: int,
    predictions: Mapping[str, Any],
) -> int:
    """Insert immutable candidate snapshots; reruns never overwrite evidence."""
    ensure_calibration_schema(conn)
    inserted = 0
    for month in predictions.get("monthly_predictions") or []:
        try:
            month_id = int(month.get("month_id"))
        except (AttributeError, TypeError, ValueError):
            continue
        primary = list(month.get("events") or [])
        people = list(month.get("people_candidates") or [])
        background = list(month.get("background_candidates") or [])
        people_background = list(month.get("people_background_candidates") or [])
        ranked_events = [
            (rank, event) for rank, event in enumerate(primary, start=1)
        ] + [
            (50 + rank, event) for rank, event in enumerate(people, start=1)
        ] + [
            (100 + rank, event) for rank, event in enumerate(background, start=1)
        ] + [
            (200 + rank, event) for rank, event in enumerate(people_background, start=1)
        ]
        for rank, event in ranked_events:
            if not isinstance(event, Mapping) or not event.get("candidate_id"):
                continue
            payload = dict(event)
            serialized = _json(payload)
            cursor = execute(
                conn,
                """
                INSERT INTO event_timeline_forecasts (
                    job_id, user_id, birth_chart_id, candidate_id, target_year, target_month,
                    display_rank, event_key, engine_version, methodology_version, evidence_version,
                    accuracy_layer, support_grade, manifestation_phase, forecast_start, forecast_end,
                    prediction_hash, forecast_json
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                ON CONFLICT (job_id, candidate_id, target_month) DO NOTHING
                """,
                (
                    job_id, user_id, birth_chart_id, str(event["candidate_id"]), int(predictions.get("year") or 0),
                    month_id, rank, str(event.get("event_key") or event.get("type") or "unknown"),
                    str(predictions.get("engine_version") or "unknown"), predictions.get("methodology_version"),
                    predictions.get("evidence_version"), event.get("accuracy_layer"), event.get("support_grade"),
                    event.get("manifestation_phase"), event.get("start_date"), event.get("end_date"),
                    hashlib.sha256(serialized.encode("utf-8", "ignore")).hexdigest(), serialized,
                ),
            )
            inserted += max(0, int(getattr(cursor, "rowcount", 0) or 0))
    return inserted


def record_outcome(
    conn: Any,
    *,
    user_id: int,
    job_id: str,
    candidate_id: str,
    month: int,
    occurrence: str,
    actual_date: date | None,
    severity: int | None,
    notes: str,
) -> bool:
    ensure_calibration_schema(conn)
    cursor = execute(
        conn,
        """
        SELECT id FROM event_timeline_forecasts
        WHERE job_id=%s AND candidate_id=%s AND target_month=%s AND user_id=%s
        """,
        (job_id, candidate_id, month, user_id),
    )
    row = cursor.fetchone()
    if not row:
        return False
    execute(
        conn,
        """
        INSERT INTO event_timeline_outcomes (forecast_id, user_id, occurrence, actual_date, severity, notes)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (forecast_id) DO UPDATE SET
            occurrence=EXCLUDED.occurrence, actual_date=EXCLUDED.actual_date,
            severity=EXCLUDED.severity, notes=EXCLUDED.notes, updated_at=CURRENT_TIMESTAMP
        """,
        (row[0], user_id, occurrence, actual_date, severity, str(notes or "")[:1000]),
    )
    return True


def record_unpredicted_event(
    conn: Any, *, user_id: int, job_id: str, event_key: str,
    actual_date: date, severity: int | None, notes: str,
) -> bool:
    ensure_calibration_schema(conn)
    owner = execute(
        conn, "SELECT 1 FROM event_timeline_jobs WHERE job_id=%s AND user_id=%s",
        (job_id, user_id),
    ).fetchone()
    if not owner:
        return False
    execute(
        conn,
        """
        INSERT INTO event_timeline_unpredicted_events (job_id, user_id, event_key, actual_date, severity, notes)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (job_id, user_id, event_key, actual_date) DO UPDATE SET
            severity=EXCLUDED.severity, notes=EXCLUDED.notes
        """,
        (job_id, user_id, event_key, actual_date, severity, str(notes or "")[:1000]),
    )
    return True


def calculate_calibration_metrics(
    rows: Sequence[Mapping[str, Any]], unpredicted_events: Sequence[Mapping[str, Any]] = (),
    *, _include_engine_breakdown: bool = True,
) -> Dict[str, Any]:
    """Calculate outcome metrics without treating astrology scores as probabilities."""
    evaluated = [row for row in rows if row.get("occurrence") in {"occurred", "partly_occurred", "did_not_occur"}]
    positives = [row for row in evaluated if row.get("occurrence") in {"occurred", "partly_occurred"}]
    strict_positives = [row for row in evaluated if row.get("occurrence") == "occurred"]
    top3 = [row for row in evaluated if int(row.get("display_rank") or 99) <= 3]
    top3_positive = [row for row in top3 if row.get("occurrence") in {"occurred", "partly_occurred"}]
    timing_errors = []
    for row in positives:
        actual = row.get("actual_date")
        start = row.get("forecast_start")
        end = row.get("forecast_end")
        if not actual or not start or not end:
            continue
        actual_day = actual if isinstance(actual, date) else date.fromisoformat(str(actual)[:10])
        start_day = start if isinstance(start, date) else date.fromisoformat(str(start)[:10])
        end_day = end if isinstance(end, date) else date.fromisoformat(str(end)[:10])
        timing_errors.append((start_day - actual_day).days if actual_day < start_day else (actual_day - end_day).days if actual_day > end_day else 0)
    by_grade: Dict[str, Dict[str, int]] = {}
    by_domain: Dict[str, Dict[str, int]] = {}
    for row in evaluated:
        positive = row.get("occurrence") in {"occurred", "partly_occurred"}
        for bucket, key in ((by_grade, str(row.get("support_grade") or "unknown")), (by_domain, str(row.get("event_key") or "unknown"))):
            value = bucket.setdefault(key, {"evaluated": 0, "positive": 0, "false_positive": 0})
            value["evaluated"] += 1
            value["positive"] += int(positive)
            value["false_positive"] += int(not positive)
    result = {
        "schema_version": CALIBRATION_SCHEMA_VERSION,
        "evaluated": len(evaluated),
        "precision_including_partial": round(len(positives) / len(evaluated), 4) if evaluated else None,
        "strict_precision": round(len(strict_positives) / len(evaluated), 4) if evaluated else None,
        "precision_at_3": round(len(top3_positive) / len(top3), 4) if top3 else None,
        "reported_event_recall": round(len(positives) / (len(positives) + len(unpredicted_events)), 4) if positives or unpredicted_events else None,
        "reported_unpredicted_events": len(unpredicted_events),
        "mean_absolute_timing_error_days": round(sum(abs(value) for value in timing_errors) / len(timing_errors), 2) if timing_errors else None,
        "by_grade": by_grade,
        "by_domain": by_domain,
        "note": "Recall is calculated only across user-reported outcomes and unpredicted events; missing feedback is not treated as a miss.",
    }
    if _include_engine_breakdown:
        engine_keys = sorted({
            (str(row.get("engine_version") or "unknown"), str(row.get("accuracy_layer") or "unknown"))
            for row in evaluated
        })
        result["by_engine_layer"] = {
            f"{engine}:{layer}": calculate_calibration_metrics(
                [
                    row for row in evaluated
                    if str(row.get("engine_version") or "unknown") == engine
                    and str(row.get("accuracy_layer") or "unknown") == layer
                ],
                [
                    row for row in unpredicted_events
                    if str(row.get("engine_version") or "unknown") == engine
                    and str(row.get("accuracy_layer") or "unknown") == layer
                ],
                _include_engine_breakdown=False,
            )
            for engine, layer in engine_keys
        }
    return result
