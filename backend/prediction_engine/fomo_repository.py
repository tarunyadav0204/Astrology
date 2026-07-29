from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from db import execute, get_conn
from psycopg2.extras import execute_values

from .contracts import FomoPresentation, Polarity, PredictionResult
from .manifestation_synthesis import build_minimal_synthesis_context, load_cached_theme_item


SNAPSHOT_RETENTION_DAYS = 14
HOMEPAGE_DISPLAY_COOLDOWN_DAYS = 7
HOMEPAGE_CHANGED_SET_QUIET_HOURS = 48
FOMO_GENERATION_LEASE_SECONDS = 600
HOMEPAGE_SELECTION_VERSION = "1.4.3"
FOMO_EVENT_TYPES = frozenset({
    "shown",
    "opened",
    "dismissed",
    "question_prefilled",
    "question_sent",
    "answer_completed",
})
_SUBJECT_DISPLAY_ORDER = {
    "self": 0,
    "spouse": 1,
    "mother": 2,
    "father": 3,
}


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def _format_cached_fomo_teaser(
    cached_theme: Mapping[str, Any],
    *,
    fallback_teaser: str,
) -> str:
    """Short intriguing hook only — never reveal the full possibilities list."""
    summary = str(cached_theme.get("summary") or "").strip()
    if not summary:
        return fallback_teaser
    # Cap at ~120 chars so the tile stays compact and curiosity-driven.
    if len(summary) > 120:
        truncated = summary[:117].rsplit(" ", 1)[0]
        return truncated + "..."
    return summary


def birth_chart_hash(chart: Mapping[str, Any]) -> str:
    payload = {
        "date": str(chart.get("date") or "").split("T", 1)[0],
        "time": str(chart.get("time") or "").split("T", 1)[-1][:8],
        "latitude": round(float(chart.get("latitude")), 6),
        "longitude": round(float(chart.get("longitude")), 6),
        "timezone": str(chart.get("timezone") or ""),
    }
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def snapshot_cache_key(
    *,
    userid: int,
    birth_chart_id: int,
    chart_hash: str,
    as_of: date,
    horizon_days: int,
    profile: str,
    profile_version: str,
    engine_version: str,
    schema_version: str,
    locale: str,
    provider_versions: Sequence[Sequence[str]] = (),
    ephemeris_settings: Optional[Mapping[str, Any]] = None,
    presentation_version: str = "",
) -> str:
    payload = {
        "userid": userid,
        "birth_chart_id": birth_chart_id,
        "chart_hash": chart_hash,
        "as_of": as_of.isoformat(),
        "horizon_days": horizon_days,
        "profile": profile,
        "profile_version": profile_version,
        "engine_version": engine_version,
        "schema_version": schema_version,
        "locale": locale,
        "provider_versions": [list(row) for row in provider_versions],
        "ephemeris_settings": dict(ephemeris_settings or {}),
        "presentation_version": presentation_version,
    }
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def homepage_fomo_auto_eligible(
    *,
    display_signature: str,
    last_display_signature: Optional[str],
    last_displayed_at: Optional[datetime],
    now: Optional[datetime] = None,
) -> bool:
    """Apply one quiet period globally and a longer repeat period per FOMO set."""
    if last_displayed_at is None:
        return True
    current_time = now or datetime.now(timezone.utc)
    previous_time = last_displayed_at
    if previous_time.tzinfo is None:
        previous_time = previous_time.replace(tzinfo=timezone.utc)
    age = current_time - previous_time
    if age < timedelta(hours=HOMEPAGE_CHANGED_SET_QUIET_HOURS):
        return False
    if (
        str(last_display_signature or "") == str(display_signature or "")
        and age < timedelta(days=HOMEPAGE_DISPLAY_COOLDOWN_DAYS)
    ):
        return False
    return True


def _presentation_from_dict(row: Mapping[str, Any]) -> FomoPresentation:
    tone = row.get("tone")
    if isinstance(tone, str):
        tone = Polarity(tone)
    elif not isinstance(tone, Polarity):
        tone = Polarity.NEUTRAL
    return FomoPresentation(
        presentation_id=str(row.get("presentation_id") or ""),
        manifestation_id=str(row.get("manifestation_id") or ""),
        locale=str(row.get("locale") or "en"),
        subject=str(row.get("subject") or "self"),
        domain=str(row.get("domain") or "other"),
        area_label=str(row.get("area_label") or ""),
        tone=tone,
        title=str(row.get("title") or ""),
        teaser=str(row.get("teaser") or ""),
        suggested_question=str(row.get("suggested_question") or ""),
        rule_id=str(row.get("rule_id") or ""),
        template_version=str(row.get("template_version") or ""),
    )


def _ready_presentations_from_engine_rows(
    *,
    presentations: Sequence[FomoPresentation],
    manifestation_rows: Sequence[Mapping[str, Any]],
    locale: str,
    limit: int,
) -> Tuple[Tuple[FomoPresentation, ...], Dict[str, Dict[str, Any]], int]:
    """
    Rank FOMO candidates, then keep only those whose LLM theme wording is cached.

    Returns (ready_presentations, theme_cache_by_presentation_id, candidate_count).
    """
    manifestation_domains = {
        str(row.get("manifestation_id") or ""): tuple(dict.fromkeys(
            str(theme.get("domain") or "").strip()
            for theme in (row.get("constituent_themes") or ())
            if str(theme.get("domain") or "").strip()
        )) or (str(row.get("domain") or "other"),)
        for row in manifestation_rows
        if row.get("manifestation_id")
    }
    homepage_presentations = rank_homepage_presentations(
        presentations,
        maximum=max(3, limit),
        manifestation_domains=manifestation_domains,
    )
    candidate_manifestation_ids = {
        str(p.manifestation_id) for p in homepage_presentations
    }
    deterministic_for_cache = [
        dict(row)
        for row in manifestation_rows
        if str(row.get("manifestation_id") or "") in candidate_manifestation_ids
    ]
    context, theme_by_manifestation_id = build_minimal_synthesis_context(
        deterministic_for_cache
    )
    cached_themes_by_key: Dict[str, Dict[str, Any]] = {}
    for theme in context.get("themes") or []:
        theme_key = str(theme.get("theme_key") or "")
        if not theme_key:
            continue
        cached_item = load_cached_theme_item(theme, locale=locale)
        if cached_item:
            cached_themes_by_key[theme_key] = cached_item

    ready: list[FomoPresentation] = []
    theme_cache_by_presentation_id: Dict[str, Dict[str, Any]] = {}
    for presentation in homepage_presentations:
        theme_key = theme_by_manifestation_id.get(str(presentation.manifestation_id))
        cached_theme = (
            cached_themes_by_key.get(str(theme_key)) if theme_key else None
        )
        if not cached_theme:
            continue
        ready.append(presentation)
        theme_cache_by_presentation_id[presentation.presentation_id] = cached_theme
    return tuple(ready), theme_cache_by_presentation_id, len(homepage_presentations)


def rank_homepage_presentations(
    presentations: Sequence[FomoPresentation],
    *,
    maximum: Optional[int] = None,
    manifestation_domains: Optional[Mapping[str, Sequence[str]]] = None,
) -> Tuple[FomoPresentation, ...]:
    # Keep every semantically distinct resolved manifestation. Different
    # signatures can produce different combined labels while repeating the same
    # dominant life area (for example Self: Finance+Relationship followed by
    # Self: Finance+Property). Preserve the first/highest-ranked theme and only
    # add later cards whose constituent domains do not overlap for that subject.
    domains_by_manifestation = manifestation_domains or {}
    distinct = []
    seen_visible_cards = set()
    for row in presentations:
        visible_key = (
            str(row.subject or "").strip().lower(),
            " ".join(str(row.title or "").split()).casefold(),
            " ".join(str(row.teaser or "").split()).casefold(),
            " ".join(str(row.suggested_question or "").split()).casefold(),
        )
        if visible_key in seen_visible_cards:
            continue
        seen_visible_cards.add(visible_key)
        distinct.append(row)
    subjects = sorted(
        {row.subject for row in distinct},
        key=lambda subject: (_SUBJECT_DISPLAY_ORDER.get(subject, 99), subject),
    )
    ordered_rows = []
    for subject in subjects:
        seen_domains = set()
        for row in distinct:
            if row.subject != subject:
                continue
            candidate_domains = {
                str(domain or "").strip().lower()
                for domain in domains_by_manifestation.get(
                    row.manifestation_id,
                    (row.domain,),
                )
                if str(domain or "").strip()
            }
            if candidate_domains.intersection(seen_domains):
                continue
            ordered_rows.append(row)
            seen_domains.update(candidate_domains)
    ordered = tuple(ordered_rows)
    if maximum is None:
        return ordered
    return ordered[:max(0, int(maximum))]


@dataclass(frozen=True)
class StoredHomepageFomo:
    snapshot_id: str
    birth_chart_id: int
    chart_name: str
    evidence_signature: str
    display_signature: str
    expires_at: str
    teasers: Tuple[Dict[str, Any], ...]

    def to_public_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "birth_chart_id": self.birth_chart_id,
            "chart_name": self.chart_name,
            "evidence_signature": self.evidence_signature,
            "expires_at": self.expires_at,
            "teasers": [dict(row) for row in self.teasers],
        }


class FomoSnapshotRepository:
    def delete_expired(self) -> int:
        with get_conn() as conn:
            cursor = execute(
                conn,
                """
                DELETE FROM parashari_prediction_snapshots
                WHERE expires_at <= CURRENT_TIMESTAMP
                """,
            )
            deleted = cursor.rowcount
            execute(
                conn,
                """
                DELETE FROM parashari_prediction_generation_claims
                WHERE lease_until <= CURRENT_TIMESTAMP
                """,
            )
            conn.commit()
        return deleted

    def try_claim_generation(
        self,
        *,
        cache_key: str,
        owner_token: str,
        lease_seconds: int = FOMO_GENERATION_LEASE_SECONDS,
    ) -> bool:
        with get_conn() as conn:
            row = execute(
                conn,
                """
                INSERT INTO parashari_prediction_generation_claims (
                    cache_key, owner_token, lease_until, created_at, updated_at
                )
                VALUES (
                    %s, %s, CURRENT_TIMESTAMP + (%s * INTERVAL '1 second'),
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                ON CONFLICT (cache_key) DO UPDATE SET
                    owner_token = EXCLUDED.owner_token,
                    lease_until = EXCLUDED.lease_until,
                    updated_at = CURRENT_TIMESTAMP
                WHERE parashari_prediction_generation_claims.lease_until
                      <= CURRENT_TIMESTAMP
                RETURNING owner_token
                """,
                (cache_key, owner_token, max(30, int(lease_seconds))),
            ).fetchone()
            conn.commit()
        return bool(row and str(row[0]) == owner_token)

    def release_generation_claim(
        self,
        *,
        cache_key: str,
        owner_token: str,
    ) -> None:
        with get_conn() as conn:
            execute(
                conn,
                """
                DELETE FROM parashari_prediction_generation_claims
                WHERE cache_key = %s
                  AND owner_token = %s
                """,
                (cache_key, owner_token),
            )
            conn.commit()

    def homepage_disabled(self, userid: int) -> bool:
        with get_conn() as conn:
            row = execute(
                conn,
                """
                SELECT homepage_disabled
                FROM parashari_prediction_preferences
                WHERE userid = %s
                """,
                (userid,),
            ).fetchone()
        return bool(row and row[0])

    def eligible_for_display(
        self,
        *,
        userid: int,
        display_signature: str,
    ) -> bool:
        with get_conn() as conn:
            row = execute(
                conn,
                """
                SELECT s.display_signature, e.created_at
                FROM parashari_prediction_funnel_events e
                JOIN parashari_prediction_snapshots s
                  ON s.snapshot_id = e.snapshot_id
                WHERE e.userid = %s
                  AND e.event_type IN ('shown', 'dismissed')
                ORDER BY e.created_at DESC
                LIMIT 1
                """,
                (userid,),
            ).fetchone()
        if not row:
            return True
        return homepage_fomo_auto_eligible(
            display_signature=display_signature,
            last_display_signature=str(row[0] or ""),
            last_displayed_at=row[1],
        )

    def set_homepage_disabled(self, userid: int, disabled: bool) -> None:
        with get_conn() as conn:
            execute(
                conn,
                """
                INSERT INTO parashari_prediction_preferences (
                    userid, homepage_disabled, updated_at
                )
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (userid) DO UPDATE
                SET homepage_disabled = EXCLUDED.homepage_disabled,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (userid, bool(disabled)),
            )
            conn.commit()

    def load_cached(
        self,
        *,
        userid: int,
        cache_key: str,
        chart_name: str,
        limit: int,
    ) -> Optional[StoredHomepageFomo]:
        with get_conn() as conn:
            snapshot = execute(
                conn,
                """
                SELECT snapshot_id, birth_chart_id, evidence_signature,
                       display_signature, expires_at
                FROM parashari_prediction_snapshots
                WHERE userid = %s
                  AND cache_key = %s
                  AND expires_at > CURRENT_TIMESTAMP
                """,
                (userid, cache_key),
            ).fetchone()
            if not snapshot:
                return None
            rows = execute(
                conn,
                """
                SELECT presentation_id, manifestation_id, locale, subject,
                       domain, area_label, tone, title, teaser, suggested_question
                FROM parashari_prediction_teasers
                WHERE snapshot_id = %s
                ORDER BY display_rank
                LIMIT %s
                """,
                (snapshot[0], limit),
            ).fetchall()
        return self._stored(snapshot, rows, chart_name)

    def save(
        self,
        *,
        userid: int,
        birth_chart_id: int,
        chart_name: str,
        cache_key: str,
        chart_hash: str,
        as_of: date,
        horizon_days: int,
        locale: str,
        result: PredictionResult,
        limit: int,
    ) -> tuple[StoredHomepageFomo, bool]:
        snapshot_id = uuid.uuid4().hex
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=SNAPSHOT_RETENTION_DAYS
        )
        payload = _canonical_json(result.to_dict(include_evidence=True))
        homepage_presentations_ready, theme_cache_by_presentation_id, candidate_count = (
            _ready_presentations_from_engine_rows(
                presentations=result.fomo_presentations,
                manifestation_rows=[m.to_dict() for m in result.chart_manifestations],
                locale=locale,
                limit=limit,
            )
        )
        # Pending when any ranked candidate still lacks LLM wording — including
        # partial hits (1 of N). Otherwise prod locks a one-card snapshot and
        # never refreshes after the remaining themes are synthesized.
        llm_wording_pending = candidate_count > 0 and (
            len(homepage_presentations_ready) < candidate_count
        )

        display_signature = hashlib.sha256(
            "|".join(
                presentation.presentation_id
                for presentation in homepage_presentations_ready
            ).encode("utf-8")
        ).hexdigest()
        with get_conn() as conn:
            row = execute(
                conn,
                """
                INSERT INTO parashari_prediction_snapshots (
                    snapshot_id, userid, birth_chart_id, cache_key, chart_hash,
                    locale, as_of_date, horizon_days, profile, profile_version,
                    engine_version, schema_version, evidence_signature,
                    display_signature, result_payload, expires_at
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s::jsonb, %s
                )
                ON CONFLICT (cache_key) DO UPDATE SET
                    evidence_signature = EXCLUDED.evidence_signature,
                    display_signature = EXCLUDED.display_signature,
                    result_payload = EXCLUDED.result_payload,
                    updated_at = CURRENT_TIMESTAMP,
                    expires_at = EXCLUDED.expires_at
                RETURNING snapshot_id
                """,
                (
                    snapshot_id,
                    userid,
                    birth_chart_id,
                    cache_key,
                    chart_hash,
                    locale,
                    as_of,
                    horizon_days,
                    result.profile,
                    result.profile_version,
                    result.engine_version,
                    result.schema_version,
                    result.evidence_signature,
                    display_signature,
                    payload,
                    expires_at,
                ),
            ).fetchone()
            persisted_snapshot_id = str(row[0])
            execute(
                conn,
                "DELETE FROM parashari_prediction_teasers WHERE snapshot_id = %s",
                (persisted_snapshot_id,),
            )
            teaser_rows = [
                (
                    presentation.presentation_id,
                    persisted_snapshot_id,
                    presentation.manifestation_id,
                    rank,
                    presentation.locale,
                    presentation.subject,
                    presentation.domain,
                    str(
                        (
                            (theme_cache_by_presentation_id.get(
                                presentation.presentation_id
                            ) or {}).get("label")
                            or presentation.area_label
                        )
                    ),
                    presentation.tone.value,
                    str(
                        (
                            (theme_cache_by_presentation_id.get(
                                presentation.presentation_id
                            ) or {}).get("label")
                            or presentation.title
                        )
                    ),
                    _format_cached_fomo_teaser(
                        theme_cache_by_presentation_id.get(presentation.presentation_id)
                        or {},
                        fallback_teaser=presentation.teaser,
                    ),
                    presentation.suggested_question,
                    presentation.rule_id,
                    presentation.template_version,
                )
                for rank, presentation in enumerate(homepage_presentations_ready)
            ]
            if teaser_rows:
                cursor = conn.cursor()
                try:
                    execute_values(
                        cursor,
                        """
                        INSERT INTO parashari_prediction_teasers (
                            presentation_id, snapshot_id, manifestation_id,
                            display_rank, locale, subject, domain, area_label,
                            tone, title, teaser, suggested_question, rule_id,
                            template_version
                        )
                        VALUES %s
                        """,
                        teaser_rows,
                        template=(
                            "(%s, %s, %s, %s, %s, %s, %s, %s, "
                            "%s, %s, %s, %s, %s, %s)"
                        ),
                        page_size=50,
                    )
                finally:
                    cursor.close()
            conn.commit()
        stored = self.load_cached(
            userid=userid,
            cache_key=cache_key,
            chart_name=chart_name,
            limit=limit,
        )
        if stored is None:
            raise RuntimeError("Persisted FOMO snapshot could not be reloaded")
        return stored, llm_wording_pending

    def refresh_teasers_from_llm_cache(
        self,
        *,
        userid: int,
        cache_key: str,
        chart_name: str,
        locale: str,
        limit: int,
    ) -> Optional[StoredHomepageFomo]:
        """
        Rebuild teasers for an existing snapshot from the current LLM theme cache.

        Used after synthesis completes, and on subsequent polls when more themes
        become ready than were saved on a partial first write.
        """
        with get_conn() as conn:
            snapshot = execute(
                conn,
                """
                SELECT snapshot_id, result_payload
                FROM parashari_prediction_snapshots
                WHERE userid = %s
                  AND cache_key = %s
                  AND expires_at > CURRENT_TIMESTAMP
                """,
                (userid, cache_key),
            ).fetchone()
        if not snapshot:
            return None
        snapshot_id = str(snapshot[0])
        payload = snapshot[1]
        if isinstance(payload, str):
            payload = json.loads(payload)
        if not isinstance(payload, Mapping):
            return None

        presentation_rows = [
            _presentation_from_dict(row)
            for row in (payload.get("fomo_presentations") or [])
            if isinstance(row, Mapping)
        ]
        manifestation_rows = [
            row
            for row in (payload.get("chart_manifestations") or [])
            if isinstance(row, Mapping)
        ]
        if not presentation_rows:
            return self.load_cached(
                userid=userid,
                cache_key=cache_key,
                chart_name=chart_name,
                limit=limit,
            )

        ready, theme_cache_by_presentation_id, _candidate_count = (
            _ready_presentations_from_engine_rows(
                presentations=presentation_rows,
                manifestation_rows=manifestation_rows,
                locale=locale,
                limit=limit,
            )
        )
        display_signature = hashlib.sha256(
            "|".join(presentation.presentation_id for presentation in ready).encode(
                "utf-8"
            )
        ).hexdigest()

        with get_conn() as conn:
            execute(
                conn,
                """
                UPDATE parashari_prediction_snapshots
                SET display_signature = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE snapshot_id = %s
                """,
                (display_signature, snapshot_id),
            )
            execute(
                conn,
                "DELETE FROM parashari_prediction_teasers WHERE snapshot_id = %s",
                (snapshot_id,),
            )
            teaser_rows = [
                (
                    presentation.presentation_id,
                    snapshot_id,
                    presentation.manifestation_id,
                    rank,
                    presentation.locale,
                    presentation.subject,
                    presentation.domain,
                    str(
                        (
                            (theme_cache_by_presentation_id.get(
                                presentation.presentation_id
                            ) or {}).get("label")
                            or presentation.area_label
                        )
                    ),
                    presentation.tone.value,
                    str(
                        (
                            (theme_cache_by_presentation_id.get(
                                presentation.presentation_id
                            ) or {}).get("label")
                            or presentation.title
                        )
                    ),
                    _format_cached_fomo_teaser(
                        theme_cache_by_presentation_id.get(presentation.presentation_id)
                        or {},
                        fallback_teaser=presentation.teaser,
                    ),
                    presentation.suggested_question,
                    presentation.rule_id,
                    presentation.template_version,
                )
                for rank, presentation in enumerate(ready)
            ]
            if teaser_rows:
                cursor = conn.cursor()
                try:
                    execute_values(
                        cursor,
                        """
                        INSERT INTO parashari_prediction_teasers (
                            presentation_id, snapshot_id, manifestation_id,
                            display_rank, locale, subject, domain, area_label,
                            tone, title, teaser, suggested_question, rule_id,
                            template_version
                        )
                        VALUES %s
                        """,
                        teaser_rows,
                        template=(
                            "(%s, %s, %s, %s, %s, %s, %s, %s, "
                            "%s, %s, %s, %s, %s, %s)"
                        ),
                        page_size=50,
                    )
                finally:
                    cursor.close()
            conn.commit()

        return self.load_cached(
            userid=userid,
            cache_key=cache_key,
            chart_name=chart_name,
            limit=limit,
        )

    def load_owned_presentation(
        self,
        *,
        userid: int,
        snapshot_id: str,
        presentation_id: str,
    ) -> Optional[Dict[str, Any]]:
        with get_conn() as conn:
            row = execute(
                conn,
                """
                SELECT t.presentation_id, t.manifestation_id, t.snapshot_id,
                       t.locale, t.subject, t.domain, t.area_label, t.tone, t.title,
                       t.teaser, t.suggested_question, s.birth_chart_id,
                       s.evidence_signature, s.expires_at
                FROM parashari_prediction_teasers t
                JOIN parashari_prediction_snapshots s
                  ON s.snapshot_id = t.snapshot_id
                WHERE t.presentation_id = %s
                  AND t.snapshot_id = %s
                  AND s.userid = %s
                  AND s.expires_at > CURRENT_TIMESTAMP
                """,
                (presentation_id, snapshot_id, userid),
            ).fetchone()
        if not row:
            return None
        keys = (
            "presentation_id",
            "manifestation_id",
            "snapshot_id",
            "locale",
            "subject",
            "domain",
            "area_label",
            "tone",
            "title",
            "teaser",
            "suggested_question",
            "birth_chart_id",
            "evidence_signature",
            "expires_at",
        )
        value = dict(zip(keys, row))
        value["expires_at"] = value["expires_at"].isoformat()
        return value

    def load_owned_chat_evidence(
        self,
        *,
        userid: int,
        snapshot_id: str,
        presentation_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Load the server-owned evidence behind one FOMO presentation."""
        with get_conn() as conn:
            row = execute(
                conn,
                """
                SELECT t.presentation_id, t.manifestation_id, t.snapshot_id,
                       t.locale, t.subject, t.domain, t.area_label, t.tone, t.title,
                       t.teaser, t.suggested_question, t.rule_id,
                       t.template_version, s.birth_chart_id,
                       s.evidence_signature, s.as_of_date, s.horizon_days,
                       s.profile, s.profile_version, s.engine_version,
                       s.schema_version, s.result_payload, s.expires_at
                FROM parashari_prediction_teasers t
                JOIN parashari_prediction_snapshots s
                  ON s.snapshot_id = t.snapshot_id
                WHERE t.presentation_id = %s
                  AND t.snapshot_id = %s
                  AND s.userid = %s
                  AND s.expires_at > CURRENT_TIMESTAMP
                """,
                (presentation_id, snapshot_id, userid),
            ).fetchone()
        if not row:
            return None
        keys = (
            "presentation_id",
            "manifestation_id",
            "snapshot_id",
            "locale",
            "subject",
            "domain",
            "area_label",
            "tone",
            "title",
            "teaser",
            "suggested_question",
            "rule_id",
            "template_version",
            "birth_chart_id",
            "evidence_signature",
            "as_of_date",
            "horizon_days",
            "profile",
            "profile_version",
            "engine_version",
            "schema_version",
            "result_payload",
            "expires_at",
        )
        value = dict(zip(keys, row))
        payload = value.get("result_payload")
        if isinstance(payload, str):
            payload = json.loads(payload)
        value["result_payload"] = payload if isinstance(payload, dict) else {}
        value["as_of_date"] = value["as_of_date"].isoformat()
        value["expires_at"] = value["expires_at"].isoformat()
        return value

    def record_event(
        self,
        *,
        userid: int,
        event_id: str,
        snapshot_id: str,
        presentation_id: Optional[str],
        event_type: str,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> bool:
        if event_type not in FOMO_EVENT_TYPES:
            raise ValueError(f"Unsupported FOMO event type: {event_type}")
        with get_conn() as conn:
            owned = execute(
                conn,
                """
                SELECT 1
                FROM parashari_prediction_snapshots s
                WHERE s.snapshot_id = %s
                  AND s.userid = %s
                  AND s.expires_at > CURRENT_TIMESTAMP
                  AND (
                    %s IS NULL OR EXISTS (
                        SELECT 1
                        FROM parashari_prediction_teasers t
                        WHERE t.presentation_id = %s
                          AND t.snapshot_id = s.snapshot_id
                    )
                  )
                """,
                (snapshot_id, userid, presentation_id, presentation_id),
            ).fetchone()
            if not owned:
                return False
            cursor = execute(
                conn,
                """
                INSERT INTO parashari_prediction_funnel_events (
                    event_id, userid, snapshot_id, presentation_id,
                    event_type, metadata
                )
                VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                ON CONFLICT (event_id) DO NOTHING
                """,
                (
                    event_id,
                    userid,
                    snapshot_id,
                    presentation_id,
                    event_type,
                    _canonical_json(dict(metadata or {})),
                ),
            )
            inserted = cursor.rowcount > 0
            conn.commit()
        return inserted

    def record_events(
        self,
        *,
        userid: int,
        snapshot_id: str,
        events: Sequence[Mapping[str, Any]],
    ) -> Optional[int]:
        """Record a bounded event batch using one ownership check and connection."""
        if not events:
            return 0
        invalid_types = {
            str(row.get("event_type") or "")
            for row in events
            if str(row.get("event_type") or "") not in FOMO_EVENT_TYPES
        }
        if invalid_types:
            raise ValueError(
                f"Unsupported FOMO event types: {sorted(invalid_types)}"
            )
        presentation_ids = sorted({
            str(row.get("presentation_id") or "").strip()
            for row in events
            if str(row.get("presentation_id") or "").strip()
        })
        with get_conn() as conn:
            owned_snapshot = execute(
                conn,
                """
                SELECT 1
                FROM parashari_prediction_snapshots
                WHERE snapshot_id = %s
                  AND userid = %s
                  AND expires_at > CURRENT_TIMESTAMP
                """,
                (snapshot_id, userid),
            ).fetchone()
            if not owned_snapshot:
                return None
            if presentation_ids:
                owned_rows = execute(
                    conn,
                    """
                    SELECT presentation_id
                    FROM parashari_prediction_teasers
                    WHERE snapshot_id = %s
                      AND presentation_id = ANY(%s)
                    """,
                    (snapshot_id, presentation_ids),
                ).fetchall()
                owned_ids = {str(row[0]) for row in owned_rows}
                if owned_ids != set(presentation_ids):
                    return None

            from psycopg2.extras import execute_values

            rows = [
                (
                    str(row.get("event_id") or ""),
                    userid,
                    snapshot_id,
                    str(row.get("presentation_id") or "").strip() or None,
                    str(row.get("event_type") or ""),
                    _canonical_json(dict(row.get("metadata") or {})),
                )
                for row in events
            ]
            cursor = conn.cursor()
            try:
                execute_values(
                    cursor,
                    """
                    INSERT INTO parashari_prediction_funnel_events (
                        event_id, userid, snapshot_id, presentation_id,
                        event_type, metadata
                    )
                    VALUES %s
                    ON CONFLICT (event_id) DO NOTHING
                    """,
                    rows,
                    template="(%s, %s, %s, %s, %s, %s::jsonb)",
                    page_size=50,
                )
                inserted = max(0, int(cursor.rowcount or 0))
            finally:
                cursor.close()
            conn.commit()
        return inserted

    @staticmethod
    def _stored(
        snapshot: Sequence[Any],
        rows: Sequence[Sequence[Any]],
        chart_name: str,
    ) -> StoredHomepageFomo:
        teaser_keys = (
            "presentation_id",
            "manifestation_id",
            "locale",
            "subject",
            "domain",
            "area_label",
            "tone",
            "title",
            "teaser",
            "suggested_question",
        )
        return StoredHomepageFomo(
            snapshot_id=str(snapshot[0]),
            birth_chart_id=int(snapshot[1]),
            chart_name=chart_name,
            evidence_signature=str(snapshot[2]),
            display_signature=str(snapshot[3]),
            expires_at=snapshot[4].isoformat(),
            teasers=tuple(dict(zip(teaser_keys, row)) for row in rows),
        )
