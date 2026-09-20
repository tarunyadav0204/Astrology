from __future__ import annotations

import asyncio
import json
import logging
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Dict, List, Mapping, Optional, Sequence
from zoneinfo import ZoneInfo

from db import execute, get_conn
from utils.timezone_service import parse_timezone_offset

from .contracts import OpportunityInput
from .deterministic_copy import normalize_locale, timeless_chat_question
from .manifestation_adapter import question_for_match, resolve_manifestations
from .repository import EngagementSuggestionRepository


logger = logging.getLogger(__name__)


def _aware(value: Any, *, end: bool = False) -> Optional[datetime]:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, date):
        return datetime.combine(value, time.max if end else time.min, tzinfo=timezone.utc)
    text_value = str(value).strip()
    if len(text_value) == 10:
        try:
            parsed_date = date.fromisoformat(text_value)
            return datetime.combine(parsed_date, time.max if end else time.min, tzinfo=timezone.utc)
        except ValueError:
            pass
    try:
        parsed = datetime.fromisoformat(text_value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        try:
            parsed_date = date.fromisoformat(text_value[:10])
            return datetime.combine(parsed_date, time.max if end else time.min, tzinfo=timezone.utc)
        except ValueError:
            return None


def _now_for_chart(chart: Mapping[str, Any]) -> datetime:
    timezone_name = str(chart.get("timezone") or "UTC").strip()
    try:
        return datetime.now(ZoneInfo(timezone_name))
    except (ValueError, KeyError):
        offset = parse_timezone_offset(
            timezone_name,
            latitude=float(chart.get("latitude")) if chart.get("latitude") is not None else None,
            longitude=float(chart.get("longitude")) if chart.get("longitude") is not None else None,
        )
        return datetime.now(timezone(timedelta(hours=offset)))


class EngagementSuggestionService:
    def __init__(self, repository: Optional[EngagementSuggestionRepository] = None):
        self.repository = repository or EngagementSuggestionRepository()

    def store_chat_followups(self, *, userid: int, birth_chart_id: Optional[int], chart_name: str, session_id: str, message_id: int, questions: Sequence[str], locale: str = "en", domain: str = "other", model_name: Optional[str] = None) -> int:
        expires = datetime.now(timezone.utc) + timedelta(days=30)
        stored = 0
        for index, raw in enumerate(questions[:3]):
            question = timeless_chat_question(raw)
            if not question:
                continue
            self.repository.upsert(OpportunityInput(
                userid=userid, birth_chart_id=birth_chart_id, chart_name=chart_name,
                source_type="chat_followup", source_reference_id=f"{message_id}:{index}",
                question=question, locale=normalize_locale(locale), domain=domain or "other",
                evidence={"session_id": session_id, "message_id": message_id, "position": index},
                support_strength=1.0, relevance_score=100.0 - index,
                expires_at=expires, semantic_cluster=f"chat:{domain or 'other'}",
                title="Continue your reading", body=question,
                generation_method="existing_llm", model_name=model_name,
                prompt_version="chat-next-action",
            ))
            stored += 1
        if stored and birth_chart_id:
            self.repository.enqueue_refresh(
                userid=userid,
                birth_chart_id=birth_chart_id,
                reason="chat_activity",
            )
        return stored

    def store_monthly_manifestations(self, *, userid: int, birth_chart_id: int, chart_name: str, snapshot_id: str, locale: str, result_payload: Mapping[str, Any], expires_at: Optional[datetime] = None) -> int:
        stored = 0
        seen: set[tuple[str, str, str]] = set()
        for source_index, source in enumerate(result_payload.get("chart_manifestations") or []):
            if not isinstance(source, Mapping):
                continue
            subject = str(source.get("subject") or "self")
            roles = [row for row in (source.get("house_roles") or []) if isinstance(row, Mapping)]
            houses = {
                int(row.get("relative_house") if subject != "self" else row.get("native_house"))
                for row in roles
                if row.get("relative_house" if subject != "self" else "native_house")
            }
            if not houses:
                continue
            window = source.get("window") if isinstance(source.get("window"), Mapping) else {}
            start = _aware(window.get("start_date"))
            end = _aware(window.get("end_date"), end=True)
            expiry = end or expires_at or (datetime.now(timezone.utc) + timedelta(days=31))
            now = datetime.now(timezone.utc)
            phase = "preparatory" if start and start > now else "developing"
            matches = resolve_manifestations(
                houses,
                method="parashari",
                phase=phase,
                calculator_version=str(result_payload.get("engine_version") or "prediction-engine"),
                limit=12,
            )
            for match_index, match in enumerate(matches):
                manifestation_id = str(match["manifestation_id"])
                unique = (subject, manifestation_id, str(window.get("start_date") or ""))
                if unique in seen:
                    continue
                seen.add(unique)
                question = timeless_chat_question(question_for_match(match, phase=phase, subject=subject))
                label = str(match.get("label") or "A timely chart theme")
                relative_title = label if subject == "self" else f"{subject.replace('_', ' ').title()}: {label}"
                self.repository.upsert(OpportunityInput(
                    userid=userid, birth_chart_id=birth_chart_id, chart_name=chart_name,
                    source_type="monthly_manifestation",
                    source_reference_id=f"{snapshot_id}:kg:{subject}:{manifestation_id}:{window.get('start_date') or source_index}",
                    source_version=str(match.get("ontology_version") or "manifestation-kg"),
                    manifestation_id=manifestation_id, question=question,
                    locale=normalize_locale(locale), domain=str(match.get("domain") or "other"),
                    subject=subject,
                    evidence={
                        "snapshot_id": snapshot_id,
                        "activation_source": source,
                        "active_houses": sorted(houses),
                        "manifestation_kg": match,
                    },
                    support_strength=min(1.0, max(0.0, float(match.get("rank_score") or 0) / 100.0)),
                    relevance_score=max(1.0, 85.0 - source_index - match_index),
                    event_window_start=start, event_window_end=end, expires_at=expiry,
                    semantic_cluster=f"kg:{subject}:{manifestation_id}",
                    title=relative_title,
                    body=(
                        f"{label} is active as a possibility during this period."
                        if subject == "self" else question
                    ),
                ))
                stored += 1
        return stored

    def store_kp_daily(self, *, userid: int, birth_chart_id: Optional[int], chart_name: str, locale: str, payload: Mapping[str, Any]) -> int:
        today = payload.get("today") if isinstance(payload.get("today"), Mapping) else payload
        as_of = _aware(payload.get("as_of")) or datetime.now(timezone.utc)
        end = datetime.combine(as_of.date(), time.max, tzinfo=as_of.tzinfo or timezone.utc)
        house_rows = [row for row in (today.get("houses_giving_results") or []) if isinstance(row, Mapping)]
        houses = sorted({int(row.get("house")) for row in house_rows if row.get("house")})
        matches = resolve_manifestations(
            houses,
            method="kp",
            phase="developing",
            calculator_version="kp-fructification/v1",
            limit=12,
        )
        stored = 0
        for index, match in enumerate(matches):
            manifestation_id = str(match["manifestation_id"])
            domain = str(match.get("domain") or "other")
            question = timeless_chat_question(question_for_match(match, phase="developing", daily=True))
            self.repository.upsert(OpportunityInput(
                userid=userid, birth_chart_id=birth_chart_id, chart_name=chart_name,
                source_type="kp_daily", source_reference_id=f"{as_of.date().isoformat()}:kg:{manifestation_id}",
                source_version=str(match.get("ontology_version") or "manifestation-kg"),
                manifestation_id=manifestation_id,
                question=question, locale=normalize_locale(locale), domain=domain,
                evidence={
                    "as_of": payload.get("as_of"),
                    "houses_giving_results": house_rows,
                    "active_houses": houses,
                    "manifestation_kg": match,
                    "source": "kp_fructification",
                },
                support_strength=min(1.0, max(0.0, float(match.get("rank_score") or 0) / 100.0)),
                relevance_score=max(1.0, 60.0 - index),
                event_window_start=datetime.combine(as_of.date(), time.min, tzinfo=as_of.tzinfo or timezone.utc),
                event_window_end=end, expires_at=end,
                semantic_cluster=f"kg:self:{manifestation_id}",
                title=str(match.get("label") or "Today's active chart theme"),
                body=f"{match.get('label')} is one of today's supported possibilities.",
            ))
            stored += 1
        return stored

    def store_event_timeline(self, *, userid: int, birth_chart_id: int, chart_name: str, job_id: str, locale: str, payload: Mapping[str, Any]) -> int:
        """Store only Event Timeline candidates explicitly backed by the shared KG."""
        today = datetime.now(timezone.utc).date()
        stored = 0
        for month in payload.get("monthly_predictions") or []:
            if not isinstance(month, Mapping):
                continue
            try:
                month_id = int(month.get("month_id") or 0)
            except (TypeError, ValueError):
                continue
            for index, event in enumerate(month.get("events") or []):
                if not isinstance(event, Mapping):
                    continue
                kg = event.get("manifestation_kg") if isinstance(event.get("manifestation_kg"), Mapping) else {}
                manifestation_id = str(kg.get("manifestation_id") or "")
                if not manifestation_id:
                    continue
                start = _aware(event.get("start_date")) or _aware(f"{today.year:04d}-{month_id:02d}-01")
                end = _aware(event.get("end_date"), end=True)
                if end is None:
                    next_month = date(today.year + (month_id == 12), 1 if month_id == 12 else month_id + 1, 1)
                    end = datetime.combine(next_month, time.min, tzinfo=timezone.utc) - timedelta(microseconds=1)
                if end.date() < today or (start and start.date() > today + timedelta(days=62)):
                    continue
                label = str(event.get("type") or manifestation_id).split(" · ", 1)[-1]
                phase = str(event.get("manifestation_phase") or "developing")
                match = {
                    "label": label,
                    "manifestation_id": manifestation_id,
                    "prompt_key": kg.get("prompt_key"),
                }
                subject = str(event.get("subject_key") or "self")
                question = timeless_chat_question(question_for_match(match, phase=phase, subject=subject))
                relative_title = label if subject == "self" else f"{subject.replace('_', ' ').title()}: {label}"
                self.repository.upsert(OpportunityInput(
                    userid=userid, birth_chart_id=birth_chart_id, chart_name=chart_name,
                    source_type="monthly_manifestation",
                    source_reference_id=f"event-timeline:{job_id}:{event.get('candidate_id') or index}",
                    source_version=str(kg.get("ontology_version") or payload.get("explanation_version") or "manifestation-kg"),
                    manifestation_id=manifestation_id, question=question,
                    locale=normalize_locale(locale), domain=str(event.get("life_domain") or "other"),
                    subject=subject,
                    evidence={"event_timeline_job_id": job_id, "candidate": event, "manifestation_kg": kg},
                    support_strength=min(1.0, max(0.0, float(event.get("support_score") or 0) / 100.0)),
                    relevance_score=max(1.0, float(event.get("priority_score") or 75) - index),
                    event_window_start=start, event_window_end=end,
                    eligible_from=datetime.now(timezone.utc), expires_at=end,
                    semantic_cluster=f"kg:{event.get('subject_key') or 'self'}:{manifestation_id}",
                    title=relative_title,
                    body=(
                        f"{label} passed the Event Timeline's deterministic evidence gates for this period."
                        if subject == "self" else question
                    ),
                ))
                stored += 1
        return stored

    def repair_from_stored_sources(self, *, lookback_hours: int = 48, limit: int = 500) -> Dict[str, int]:
        summary = {
            "chat_followups": 0,
            "monthly_manifestations": 0,
            "event_timeline_manifestations": 0,
            "expired": self.repository.expire_stale(),
        }
        with get_conn() as conn:
            chat_rows = execute(conn, """
                SELECT cm.message_id, cs.user_id, cs.birth_chart_id,
                       COALESCE(bc.name, ''), cs.session_id,
                       cm.follow_up_questions, COALESCE(cm.language, 'en'),
                       COALESCE(cm.category, 'other'), COALESCE(cs.chat_llm_model, '')
                FROM chat_messages cm
                JOIN chat_sessions cs ON cs.session_id = cm.session_id
                LEFT JOIN birth_charts bc ON bc.id = cs.birth_chart_id
                WHERE cm.sender = 'assistant' AND cm.status = 'completed'
                  AND cm.follow_up_questions IS NOT NULL
                  AND cm.completed_at >= CURRENT_TIMESTAMP - (%s * INTERVAL '1 hour')
                ORDER BY cm.completed_at DESC
                LIMIT %s
            """, (max(1, int(lookback_hours)), max(1, int(limit)))).fetchall()
            fomo_rows = execute(conn, """
                SELECT s.userid, s.birth_chart_id, COALESCE(b.name, ''), s.snapshot_id,
                       s.locale, s.result_payload, s.expires_at
                FROM parashari_prediction_snapshots s
                JOIN birth_charts b ON b.id = s.birth_chart_id
                WHERE s.expires_at > CURRENT_TIMESTAMP
                  AND s.updated_at >= CURRENT_TIMESTAMP - (%s * INTERVAL '1 hour')
                ORDER BY s.updated_at DESC
                LIMIT %s
            """, (max(1, int(lookback_hours)), max(1, int(limit)))).fetchall()
            timeline_rows = execute(conn, """
                SELECT j.user_id, j.birth_chart_id, COALESCE(b.name, ''), j.job_id,
                       COALESCE(j.result_data, '{}'), j.completed_at
                FROM event_timeline_jobs j
                JOIN birth_charts b ON b.id = j.birth_chart_id
                WHERE j.status = 'completed'
                  AND j.completed_at >= CURRENT_TIMESTAMP - (%s * INTERVAL '1 hour')
                ORDER BY j.completed_at DESC
                LIMIT %s
            """, (max(1, int(lookback_hours)), max(1, int(limit)))).fetchall()
        for message_id, userid, chart_id, chart_name, session_id, raw, locale, domain, model in chat_rows:
            try:
                questions = json.loads(raw) if isinstance(raw, str) else (raw or [])
                summary["chat_followups"] += self.store_chat_followups(
                    userid=int(userid), birth_chart_id=int(chart_id) if chart_id else None,
                    chart_name=str(chart_name or ""), session_id=str(session_id),
                    message_id=int(message_id), questions=questions if isinstance(questions, list) else [],
                    locale=str(locale or "en"), domain=str(domain or "other"), model_name=str(model or "") or None,
                )
            except Exception:
                logger.exception("Failed to repair chat suggestions message_id=%s", message_id)
        for userid, chart_id, chart_name, snapshot_id, locale, payload, expires_at in fomo_rows:
            try:
                data = json.loads(payload) if isinstance(payload, str) else (payload or {})
                summary["monthly_manifestations"] += self.store_monthly_manifestations(
                    userid=int(userid), birth_chart_id=int(chart_id), chart_name=str(chart_name or ""),
                    snapshot_id=str(snapshot_id), locale=str(locale or "en"), result_payload=data,
                    expires_at=expires_at,
                )
            except Exception:
                logger.exception("Failed to repair monthly suggestions snapshot_id=%s", snapshot_id)
        for userid, chart_id, chart_name, job_id, payload, _completed_at in timeline_rows:
            try:
                data = json.loads(payload) if isinstance(payload, str) else (payload or {})
                summary["event_timeline_manifestations"] += self.store_event_timeline(
                    userid=int(userid), birth_chart_id=int(chart_id), chart_name=str(chart_name or ""),
                    job_id=str(job_id), locale=str(data.get("language") or "en"), payload=data,
                )
            except Exception:
                logger.exception("Failed to repair Event Timeline suggestions job_id=%s", job_id)
        return summary

    @staticmethod
    def _load_chart(userid: int, birth_chart_id: int) -> Optional[Dict[str, Any]]:
        from birth_charts.routes import _row_to_chart

        with get_conn() as conn:
            row = execute(conn, """
                SELECT id, userid, name, date, time, latitude, longitude, timezone,
                       created_at, place, gender, relation, relation_order,
                       relation_side, relation_label, is_family_member
                FROM birth_charts
                WHERE id = %s AND userid = %s
            """, (birth_chart_id, userid)).fetchone()
        return _row_to_chart(row) if row else None

    @staticmethod
    def _load_latest_monthly_snapshot(userid: int, birth_chart_id: int) -> Optional[Dict[str, Any]]:
        with get_conn() as conn:
            row = execute(conn, """
                SELECT snapshot_id, locale, result_payload, expires_at
                FROM parashari_prediction_snapshots
                WHERE userid = %s AND birth_chart_id = %s
                  AND expires_at > CURRENT_TIMESTAMP
                ORDER BY updated_at DESC
                LIMIT 1
            """, (userid, birth_chart_id)).fetchone()
        if not row:
            return None
        payload = json.loads(row[2]) if isinstance(row[2], str) else (row[2] or {})
        return {
            "snapshot_id": str(row[0]),
            "locale": str(row[1] or "en"),
            "result_payload": payload,
            "expires_at": row[3],
        }

    async def process_due_refreshes(
        self,
        *,
        limit: int = 10,
        userid: Optional[int] = None,
        birth_chart_id: Optional[int] = None,
    ) -> Dict[str, int]:
        """Run bounded chart work. No synthesis/LLM is called by this worker."""
        jobs = await asyncio.to_thread(
            self.repository.claim_due_refreshes,
            limit=limit,
            userid=userid,
            birth_chart_id=birth_chart_id,
        )
        summary = {"claimed": len(jobs), "completed": 0, "failed": 0, "monthly": 0, "kp": 0}
        for job in jobs:
            error = None
            try:
                userid = int(job["userid"])
                chart_id = int(job["birth_chart_id"])
                chart = await asyncio.to_thread(self._load_chart, userid, chart_id)
                if not chart:
                    raise ValueError("Birth chart no longer exists or is not owned by user")
                sources = set(job.get("sources") or [])
                if "monthly_manifestation" in sources:
                    # This invokes only the deterministic PredictionService. The
                    # route-level synthesis step is deliberately not called.
                    from prediction_engine.routes import _generate_homepage_fomo

                    await asyncio.to_thread(
                        _generate_homepage_fomo,
                        userid=userid,
                        chart=chart,
                        locale="en",
                        limit=24,
                        include_ineligible=True,
                    )
                    # Cached FOMO generation returns before the repository's
                    # save hook runs. Always ingest the persisted snapshot so
                    # an explicit refresh actually refreshes engagement copy.
                    snapshot = await asyncio.to_thread(
                        self._load_latest_monthly_snapshot,
                        userid,
                        chart_id,
                    )
                    if not snapshot:
                        raise RuntimeError("Monthly prediction refresh produced no active snapshot")
                    await asyncio.to_thread(
                        self.store_monthly_manifestations,
                        userid=userid,
                        birth_chart_id=chart_id,
                        chart_name=str(chart.get("name") or ""),
                        snapshot_id=snapshot["snapshot_id"],
                        locale=snapshot["locale"],
                        result_payload=snapshot["result_payload"],
                        expires_at=snapshot["expires_at"],
                    )
                    summary["monthly"] += 1
                if "kp_daily" in sources:
                    from app.kp.services.fructification_service import compute_fructification

                    chart_now = _now_for_chart(chart)

                    kp = await compute_fructification(
                        birth_date=str(chart.get("date") or ""),
                        birth_time=str(chart.get("time") or ""),
                        latitude=float(chart.get("latitude")),
                        longitude=float(chart.get("longitude")),
                        timezone=str(chart.get("timezone") or ""),
                        as_of_date=chart_now.strftime("%Y-%m-%d"),
                        as_of_time=chart_now.strftime("%H:%M:%S"),
                        language="en",
                        synthesize=False,
                    )
                    await asyncio.to_thread(
                        self.store_kp_daily,
                        userid=userid,
                        birth_chart_id=chart_id,
                        chart_name=str(chart.get("name") or ""),
                        locale="en",
                        payload=kp,
                    )
                    summary["kp"] += 1
                summary["completed"] += 1
            except Exception as exc:
                logger.exception("Engagement refresh failed queue_id=%s", job.get("id"))
                error = str(exc)
                summary["failed"] += 1
            await asyncio.to_thread(
                self.repository.finish_refresh,
                queue_id=int(job["id"]),
                error=error,
            )
        return summary
