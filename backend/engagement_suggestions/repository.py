from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from db import execute, get_conn

from .contracts import OpportunityInput
from .deterministic_copy import notification_copy, timeless_chat_question


SOURCE_PRIORITY = {"chat_followup": 300.0, "monthly_manifestation": 200.0, "kp_daily": 100.0}


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _stable_key(item: OpportunityInput) -> str:
    payload = "|".join((str(item.userid), str(item.birth_chart_id or ""), item.source_type, item.source_reference_id, item.locale))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class EngagementSuggestionRepository:
    def get_preferences(self, userid: int) -> Dict[str, Any]:
        with get_conn() as conn:
            row = execute(conn, """
                SELECT timezone, preferred_locale, astrology_alerts_enabled,
                       push_enabled, whatsapp_enabled, sms_enabled, email_enabled,
                       quiet_hours_start, quiet_hours_end, preferred_delivery_time,
                       daily_notification_limit, weekly_notification_limit,
                       suppressed_domains_json, consent_json, updated_at
                FROM user_engagement_preferences WHERE userid = %s
            """, (userid,)).fetchone()
        if not row:
            return {
                "timezone": "Asia/Kolkata", "preferred_locale": "en",
                "astrology_alerts_enabled": False, "push_enabled": False,
                "whatsapp_enabled": False, "sms_enabled": False,
                "email_enabled": False, "quiet_hours_start": None,
                "quiet_hours_end": None, "preferred_delivery_time": None,
                "daily_notification_limit": 1, "weekly_notification_limit": 5,
                "suppressed_domains": [], "consent": {}, "updated_at": None,
            }
        keys = (
            "timezone", "preferred_locale", "astrology_alerts_enabled",
            "push_enabled", "whatsapp_enabled", "sms_enabled", "email_enabled",
            "quiet_hours_start", "quiet_hours_end", "preferred_delivery_time",
            "daily_notification_limit", "weekly_notification_limit",
            "suppressed_domains", "consent", "updated_at",
        )
        value = dict(zip(keys, row))
        for key in ("quiet_hours_start", "quiet_hours_end", "preferred_delivery_time", "updated_at"):
            if value[key] is not None:
                value[key] = value[key].isoformat()
        for key in ("suppressed_domains", "consent"):
            if isinstance(value[key], str):
                try:
                    value[key] = json.loads(value[key])
                except ValueError:
                    value[key] = [] if key == "suppressed_domains" else {}
        return value

    def upsert_preferences(self, userid: int, values: Mapping[str, Any]) -> Dict[str, Any]:
        current = self.get_preferences(userid)
        current.update(values)
        with get_conn() as conn:
            execute(conn, """
                INSERT INTO user_engagement_preferences (
                    userid, timezone, preferred_locale, astrology_alerts_enabled,
                    push_enabled, whatsapp_enabled, sms_enabled, email_enabled,
                    quiet_hours_start, quiet_hours_end, preferred_delivery_time,
                    daily_notification_limit, weekly_notification_limit,
                    suppressed_domains_json, consent_json, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s::jsonb, %s::jsonb, CURRENT_TIMESTAMP
                )
                ON CONFLICT (userid) DO UPDATE SET
                    timezone = EXCLUDED.timezone,
                    preferred_locale = EXCLUDED.preferred_locale,
                    astrology_alerts_enabled = EXCLUDED.astrology_alerts_enabled,
                    push_enabled = EXCLUDED.push_enabled,
                    whatsapp_enabled = EXCLUDED.whatsapp_enabled,
                    sms_enabled = EXCLUDED.sms_enabled,
                    email_enabled = EXCLUDED.email_enabled,
                    quiet_hours_start = EXCLUDED.quiet_hours_start,
                    quiet_hours_end = EXCLUDED.quiet_hours_end,
                    preferred_delivery_time = EXCLUDED.preferred_delivery_time,
                    daily_notification_limit = EXCLUDED.daily_notification_limit,
                    weekly_notification_limit = EXCLUDED.weekly_notification_limit,
                    suppressed_domains_json = EXCLUDED.suppressed_domains_json,
                    consent_json = EXCLUDED.consent_json,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                userid, current["timezone"], current["preferred_locale"],
                bool(current["astrology_alerts_enabled"]), bool(current["push_enabled"]),
                bool(current["whatsapp_enabled"]), bool(current["sms_enabled"]),
                bool(current["email_enabled"]), current["quiet_hours_start"],
                current["quiet_hours_end"], current["preferred_delivery_time"],
                int(current["daily_notification_limit"]), int(current["weekly_notification_limit"]),
                _json(current.get("suppressed_domains") or []), _json(current.get("consent") or {}),
            ))
            conn.commit()
        return self.get_preferences(userid)

    def enqueue_refresh(self, *, userid: int, birth_chart_id: int, reason: str, sources: Sequence[str] = ("monthly_manifestation", "kp_daily")) -> None:
        allowed = [source for source in sources if source in {"monthly_manifestation", "kp_daily"}]
        if not allowed:
            return
        with get_conn() as conn:
            execute(conn, """
                INSERT INTO engagement_refresh_queue (
                    userid, birth_chart_id, reason, sources_json, scheduled_for,
                    state, attempts, lease_until, last_error, updated_at
                ) VALUES (%s, %s, %s, %s::jsonb, CURRENT_TIMESTAMP, 'pending', 0, NULL, NULL, CURRENT_TIMESTAMP)
                ON CONFLICT (userid, birth_chart_id) DO UPDATE SET
                    reason = EXCLUDED.reason,
                    sources_json = EXCLUDED.sources_json,
                    scheduled_for = LEAST(engagement_refresh_queue.scheduled_for, CURRENT_TIMESTAMP),
                    state = 'pending',
                    lease_until = NULL,
                    last_error = NULL,
                    updated_at = CURRENT_TIMESTAMP
            """, (userid, birth_chart_id, reason[:120], _json(allowed)))
            conn.commit()

    def claim_due_refreshes(
        self,
        *,
        limit: int = 10,
        lease_minutes: int = 30,
        userid: Optional[int] = None,
        birth_chart_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        with get_conn() as conn:
            rows = execute(conn, """
                WITH due AS (
                    SELECT id
                    FROM engagement_refresh_queue
                    WHERE scheduled_for <= CURRENT_TIMESTAMP
                      AND (%s IS NULL OR userid = %s)
                      AND (%s IS NULL OR birth_chart_id = %s)
                      AND (
                        state = 'pending'
                        OR (state = 'running' AND lease_until <= CURRENT_TIMESTAMP)
                        OR (state = 'failed' AND attempts < 3)
                      )
                    ORDER BY scheduled_for, id
                    FOR UPDATE SKIP LOCKED
                    LIMIT %s
                )
                UPDATE engagement_refresh_queue q
                SET state = 'running',
                    attempts = attempts + 1,
                    lease_until = CURRENT_TIMESTAMP + (%s * INTERVAL '1 minute'),
                    updated_at = CURRENT_TIMESTAMP
                FROM due
                WHERE q.id = due.id
                RETURNING q.id, q.userid, q.birth_chart_id, q.reason,
                          q.sources_json, q.attempts
            """, (
                userid, userid, birth_chart_id, birth_chart_id,
                max(1, min(int(limit), 100)), max(5, int(lease_minutes)),
            )).fetchall()
            conn.commit()
        keys = ("id", "userid", "birth_chart_id", "reason", "sources", "attempts")
        result = []
        for raw in rows:
            row = dict(zip(keys, raw))
            if isinstance(row["sources"], str):
                try:
                    row["sources"] = json.loads(row["sources"])
                except ValueError:
                    row["sources"] = []
            result.append(row)
        return result

    def finish_refresh(self, *, queue_id: int, error: Optional[str] = None) -> None:
        with get_conn() as conn:
            if error:
                execute(conn, """
                    UPDATE engagement_refresh_queue
                    SET state = 'failed', lease_until = NULL, last_error = %s,
                        scheduled_for = CURRENT_TIMESTAMP + (LEAST(attempts, 3) * INTERVAL '15 minutes'),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (str(error)[:2000], queue_id))
            else:
                execute(conn, """
                    UPDATE engagement_refresh_queue
                    SET state = 'completed', lease_until = NULL, last_error = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (queue_id,))
            conn.commit()

    def enqueue_notification_refreshes(self, *, limit: int = 500) -> int:
        """Queue opted-in charts once per UTC day; callers process in bounded batches."""
        with get_conn() as conn:
            cursor = execute(conn, """
                INSERT INTO engagement_refresh_queue (
                    userid, birth_chart_id, reason, sources_json, scheduled_for,
                    state, attempts, lease_until, last_error, updated_at
                )
                SELECT p.userid, b.id, 'daily_notification_preparation',
                       '["monthly_manifestation","kp_daily"]'::jsonb,
                       CURRENT_TIMESTAMP, 'pending', 0, NULL, NULL, CURRENT_TIMESTAMP
                FROM user_engagement_preferences p
                JOIN birth_charts b ON b.userid = p.userid
                LEFT JOIN engagement_refresh_queue q
                  ON q.userid = p.userid AND q.birth_chart_id = b.id
                WHERE p.astrology_alerts_enabled = TRUE
                  AND (p.push_enabled OR p.whatsapp_enabled OR p.sms_enabled OR p.email_enabled)
                  AND (q.id IS NULL OR q.updated_at::date < CURRENT_DATE)
                ORDER BY p.userid, b.id
                LIMIT %s
                ON CONFLICT (userid, birth_chart_id) DO UPDATE SET
                    reason = EXCLUDED.reason,
                    sources_json = EXCLUDED.sources_json,
                    scheduled_for = CURRENT_TIMESTAMP,
                    state = 'pending', attempts = 0, lease_until = NULL,
                    last_error = NULL, updated_at = CURRENT_TIMESTAMP
            """, (max(1, min(int(limit), 5000)),))
            queued = int(cursor.rowcount or 0)
            conn.commit()
        return queued

    def upsert(self, item: OpportunityInput) -> str:
        now = datetime.now(timezone.utc)
        expires_at = item.expires_at or item.event_window_end
        if expires_at is None:
            raise ValueError("expires_at or event_window_end is required")
        opportunity_id = uuid.uuid5(uuid.NAMESPACE_URL, f"astroroshni:engagement:{_stable_key(item)}").hex
        dedupe_key = _stable_key(item)
        copy = notification_copy(
            chart_name=item.chart_name,
            question=item.question,
            source_type=item.source_type,
            title=item.title,
            body=item.body,
        )
        with get_conn() as conn:
            row = execute(conn, """
                INSERT INTO engagement_opportunities (
                    id, userid, birth_chart_id, chart_name_snapshot, source_type,
                    source_reference_id, source_version, manifestation_id, domain,
                    subject, evidence_json, support_strength, relevance_score,
                    event_window_start, event_window_end, eligible_from, expires_at,
                    dedupe_key, semantic_cluster, status, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb,
                    %s, %s, %s, %s, %s, %s, %s, %s, 'active', CURRENT_TIMESTAMP
                )
                ON CONFLICT (userid, dedupe_key) DO UPDATE SET
                    chart_name_snapshot = EXCLUDED.chart_name_snapshot,
                    evidence_json = EXCLUDED.evidence_json,
                    support_strength = EXCLUDED.support_strength,
                    relevance_score = EXCLUDED.relevance_score,
                    event_window_start = EXCLUDED.event_window_start,
                    event_window_end = EXCLUDED.event_window_end,
                    eligible_from = EXCLUDED.eligible_from,
                    expires_at = EXCLUDED.expires_at,
                    semantic_cluster = EXCLUDED.semantic_cluster,
                    status = 'active',
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, (
                opportunity_id, item.userid, item.birth_chart_id, item.chart_name,
                item.source_type, item.source_reference_id, item.source_version,
                item.manifestation_id, item.domain, item.subject, _json(item.evidence),
                float(item.support_strength), float(item.relevance_score),
                item.event_window_start, item.event_window_end,
                item.eligible_from or now, expires_at, dedupe_key,
                item.semantic_cluster or item.domain,
            )).fetchone()
            persisted_id = str(row[0])
            execute(conn, """
                UPDATE engagement_presentations
                SET active = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE opportunity_id = %s AND locale = %s AND content_version <> %s
            """, (persisted_id, item.locale, item.source_version))
            execute(conn, """
                INSERT INTO engagement_presentations (
                    opportunity_id, locale, chat_question, push_title, push_body,
                    whatsapp_body, whatsapp_template_params_json, sms_body,
                    email_subject, email_body, landing_screen, prefilled_question,
                    generation_method, model_name, prompt_version, content_version,
                    active, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, '{}'::jsonb, %s, %s, %s,
                    'chat', %s, %s, %s, %s, %s, TRUE, CURRENT_TIMESTAMP
                )
                ON CONFLICT (opportunity_id, locale, content_version) DO UPDATE SET
                    chat_question = EXCLUDED.chat_question,
                    push_title = EXCLUDED.push_title,
                    push_body = EXCLUDED.push_body,
                    whatsapp_body = EXCLUDED.whatsapp_body,
                    sms_body = EXCLUDED.sms_body,
                    email_subject = EXCLUDED.email_subject,
                    email_body = EXCLUDED.email_body,
                    prefilled_question = EXCLUDED.prefilled_question,
                    generation_method = EXCLUDED.generation_method,
                    model_name = EXCLUDED.model_name,
                    prompt_version = EXCLUDED.prompt_version,
                    active = TRUE,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                persisted_id, item.locale, item.question, copy["push_title"],
                copy["push_body"], copy["whatsapp_body"], copy["sms_body"],
                copy["email_subject"], copy["email_body"], item.question,
                item.generation_method, item.model_name, item.prompt_version,
                item.source_version,
            ))
            conn.commit()
        return persisted_id

    def list_ranked(self, *, userid: int, birth_chart_id: Optional[int], locale: str, limit: int = 4) -> List[Dict[str, Any]]:
        with get_conn() as conn:
            rows = execute(conn, """
                WITH candidates AS (
                    SELECT o.id AS opportunity_id, p.id AS presentation_id,
                           o.birth_chart_id, o.chart_name_snapshot,
                           o.source_type, o.source_reference_id, o.manifestation_id,
                           o.domain, o.subject, o.support_strength, o.relevance_score,
                           o.event_window_start, o.event_window_end, o.expires_at,
                           p.chat_question, p.push_title, p.push_body,
                           p.prefilled_question, o.semantic_cluster,
                           CASE o.source_type
                             WHEN 'chat_followup' THEN 3
                             WHEN 'monthly_manifestation' THEN 2
                             WHEN 'kp_daily' THEN 1
                             ELSE 0
                           END AS source_priority,
                           ROW_NUMBER() OVER (
                               PARTITION BY o.source_type
                               ORDER BY o.relevance_score DESC,
                                        o.support_strength DESC,
                                        COALESCE(o.last_presented_at, TIMESTAMPTZ 'epoch') ASC,
                                        o.created_at DESC
                           ) AS source_rank
                    FROM engagement_opportunities o
                    JOIN engagement_presentations p ON p.opportunity_id = o.id
                    WHERE o.userid = %s
                      AND (%s IS NULL OR o.birth_chart_id = %s)
                      AND o.status = 'active'
                      AND o.eligible_from <= CURRENT_TIMESTAMP
                      AND o.expires_at > CURRENT_TIMESTAMP
                      AND (o.cooldown_until IS NULL OR o.cooldown_until <= CURRENT_TIMESTAMP)
                      AND p.active = TRUE
                      AND p.locale = %s
                      AND NOT EXISTS (
                          SELECT 1 FROM engagement_interactions i
                          WHERE i.opportunity_id = o.id
                            AND i.event_type IN ('asked', 'converted')
                      )
                )
                SELECT opportunity_id, presentation_id, birth_chart_id,
                       chart_name_snapshot, source_type, source_reference_id,
                       manifestation_id, domain, subject, support_strength,
                       relevance_score, event_window_start, event_window_end,
                       expires_at, chat_question, push_title, push_body,
                       prefilled_question, semantic_cluster
                FROM candidates
                WHERE source_rank <= %s
                ORDER BY
                  source_priority DESC,
                  relevance_score DESC,
                  support_strength DESC
            """, (userid, birth_chart_id, birth_chart_id, locale, max(8, min(int(limit) * 5, 50)))).fetchall()
        keys = (
            "opportunity_id", "presentation_id", "birth_chart_id", "chart_name",
            "source", "source_reference_id", "manifestation_id", "domain", "subject", "support_strength",
            "relevance_score", "window_start", "window_end", "expires_at",
            "question", "push_title", "push_body", "prefilled_question", "semantic_cluster",
        )
        result = []
        seen_domains = set()
        source_counts: Dict[str, int] = {}
        for raw in rows:
            row = dict(zip(keys, raw))
            # Present old stored suggestions safely too. This keeps a stale
            # presentation from making Tara interpret a topic specifically for
            # today after the generation rule has changed.
            row["question"] = timeless_chat_question(row.get("question"))
            row["prefilled_question"] = row["question"]
            domain = str(row["domain"] or "other")
            source = str(row["source"])
            if domain in seen_domains or source_counts.get(source, 0) >= 2:
                continue
            seen_domains.add(domain)
            source_counts[source] = source_counts.get(source, 0) + 1
            for key in ("window_start", "window_end", "expires_at"):
                if row[key] is not None:
                    row[key] = row[key].isoformat()
            result.append(row)
            if len(result) >= limit:
                break
        return result

    def record_interaction(self, *, userid: int, opportunity_id: str, presentation_id: Optional[int], event_id: str, event_type: str, surface: str, birth_chart_id: Optional[int] = None, session_id: Optional[str] = None, delivery_group_id: Optional[str] = None, metadata: Optional[Mapping[str, Any]] = None) -> Optional[bool]:
        with get_conn() as conn:
            owned = execute(
                conn,
                "SELECT birth_chart_id FROM engagement_opportunities WHERE id = %s AND userid = %s",
                (opportunity_id, userid),
            ).fetchone()
            if not owned:
                return None
            owned_birth_chart_id = owned[0]
            if presentation_id is not None:
                presentation = execute(
                    conn,
                    "SELECT 1 FROM engagement_presentations WHERE id = %s AND opportunity_id = %s",
                    (presentation_id, opportunity_id),
                ).fetchone()
                if not presentation:
                    return None
            cursor = execute(conn, """
                INSERT INTO engagement_interactions (
                    event_id, opportunity_id, presentation_id, userid,
                    birth_chart_id, surface, event_type, delivery_group_id,
                    session_id, metadata_json
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                ON CONFLICT (event_id) DO NOTHING
            """, (event_id, opportunity_id, presentation_id, userid, owned_birth_chart_id, surface, event_type, delivery_group_id, session_id, _json(dict(metadata or {}))))
            inserted = cursor.rowcount > 0
            if inserted and event_type == "shown":
                execute(conn, """
                    UPDATE engagement_opportunities
                    SET presentation_count = presentation_count + 1,
                        last_presented_at = CURRENT_TIMESTAMP,
                        cooldown_until = CURRENT_TIMESTAMP + (
                            CASE source_type
                              WHEN 'monthly_manifestation' THEN INTERVAL '7 days'
                              WHEN 'kp_daily' THEN INTERVAL '18 hours'
                              ELSE INTERVAL '1 day'
                            END
                        ),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (opportunity_id,))
            elif inserted and event_type == "dismissed":
                execute(conn, """
                    UPDATE engagement_opportunities
                    SET cooldown_until = CURRENT_TIMESTAMP + INTERVAL '14 days',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (opportunity_id,))
            elif inserted and event_type in {"asked", "converted"}:
                execute(conn, "UPDATE engagement_opportunities SET status = 'consumed', updated_at = CURRENT_TIMESTAMP WHERE id = %s", (opportunity_id,))
            conn.commit()
        return inserted

    def expire_stale(self) -> int:
        with get_conn() as conn:
            cursor = execute(conn, """
                UPDATE engagement_opportunities
                SET status = 'expired', updated_at = CURRENT_TIMESTAMP
                WHERE status = 'active' AND expires_at <= CURRENT_TIMESTAMP
            """)
            changed = int(cursor.rowcount or 0)
            conn.commit()
        return changed
