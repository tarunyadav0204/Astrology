"""Structured Desh-Kaal-Patra profiles for people around a chart native."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping

from db import execute


RELATIVE_SUBJECTS: Dict[str, Dict[str, Any]] = {
    "spouse": {"label": "Spouse", "reference_house": 7},
    "mother": {"label": "Mother", "reference_house": 4},
    "father": {"label": "Father", "reference_house": 9},
    "child": {"label": "Child", "reference_house": 5},
    "younger_sibling": {"label": "Younger sibling", "reference_house": 3},
    "elder_sibling": {"label": "Elder sibling", "reference_house": 11},
    "sibling": {"label": "Sibling", "reference_house": 3},
}


def ensure_relative_profiles_schema(conn: Any) -> None:
    execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS event_relative_profiles (
            id BIGSERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            birth_chart_id INTEGER NOT NULL REFERENCES birth_charts(id) ON DELETE CASCADE,
            subject_key TEXT NOT NULL,
            display_label TEXT NOT NULL,
            life_status TEXT NOT NULL DEFAULT 'unknown',
            age_years INTEGER,
            birth_year INTEGER,
            employment_state TEXT NOT NULL DEFAULT 'unknown',
            location_context TEXT NOT NULL DEFAULT 'unknown',
            relationship_status TEXT NOT NULL DEFAULT 'unknown',
            linked_birth_chart_id INTEGER REFERENCES birth_charts(id) ON DELETE SET NULL,
            enabled BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (user_id, birth_chart_id, subject_key)
        )
        """,
    )
    execute(
        conn,
        "CREATE INDEX IF NOT EXISTS idx_event_relative_profiles_chart ON event_relative_profiles (user_id, birth_chart_id)",
    )


def load_relative_profiles(conn: Any, *, user_id: int, birth_chart_id: int) -> List[Dict[str, Any]]:
    ensure_relative_profiles_schema(conn)
    cur = execute(
        conn,
        """
        SELECT p.subject_key, p.display_label, p.life_status, p.age_years, p.birth_year,
               p.employment_state, p.location_context, p.relationship_status,
               p.linked_birth_chart_id, p.enabled, p.updated_at
        FROM event_relative_profiles p
        INNER JOIN birth_charts bc ON bc.id = p.birth_chart_id AND bc.userid = %s
        WHERE p.user_id = %s AND p.birth_chart_id = %s
        ORDER BY CASE p.subject_key
            WHEN 'spouse' THEN 1 WHEN 'mother' THEN 2 WHEN 'father' THEN 3
            WHEN 'child' THEN 4 WHEN 'younger_sibling' THEN 5
            WHEN 'elder_sibling' THEN 6 ELSE 7 END
        """,
        (int(user_id), int(user_id), int(birth_chart_id)),
    )
    rows: List[Dict[str, Any]] = []
    for row in cur.fetchall() or []:
        spec = RELATIVE_SUBJECTS.get(str(row[0])) or {}
        rows.append({
            "subject_key": row[0],
            "display_label": row[1],
            "reference_house": spec.get("reference_house"),
            "life_status": row[2],
            "age_years": row[3],
            "birth_year": row[4],
            "employment_state": row[5],
            "location_context": row[6],
            "relationship_status": row[7],
            "linked_birth_chart_id": row[8],
            "enabled": bool(row[9]),
            "updated_at": row[10].isoformat() if hasattr(row[10], "isoformat") else str(row[10]),
            "profile_source": "structured_family_profile",
        })
    return rows


def upsert_relative_profile(
    conn: Any, *, user_id: int, birth_chart_id: int, subject_key: str, values: Mapping[str, Any],
) -> Dict[str, Any]:
    subject_key = str(subject_key or "").strip().lower()
    if subject_key not in RELATIVE_SUBJECTS:
        raise ValueError("Unsupported relative type")
    owned = execute(
        conn, "SELECT 1 FROM birth_charts WHERE id = %s AND userid = %s", (birth_chart_id, user_id),
    ).fetchone()
    if not owned:
        raise LookupError("Birth chart not found")
    linked = values.get("linked_birth_chart_id")
    if linked is not None:
        linked_owned = execute(
            conn, "SELECT 1 FROM birth_charts WHERE id = %s AND userid = %s", (linked, user_id),
        ).fetchone()
        if not linked_owned:
            raise ValueError("Linked birth chart does not belong to this account")
    spec = RELATIVE_SUBJECTS[subject_key]
    execute(
        conn,
        """
        INSERT INTO event_relative_profiles (
            user_id, birth_chart_id, subject_key, display_label, life_status,
            age_years, birth_year, employment_state, location_context,
            relationship_status, linked_birth_chart_id, enabled, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (user_id, birth_chart_id, subject_key) DO UPDATE SET
            display_label = EXCLUDED.display_label,
            life_status = EXCLUDED.life_status,
            age_years = EXCLUDED.age_years,
            birth_year = EXCLUDED.birth_year,
            employment_state = EXCLUDED.employment_state,
            location_context = EXCLUDED.location_context,
            relationship_status = EXCLUDED.relationship_status,
            linked_birth_chart_id = EXCLUDED.linked_birth_chart_id,
            enabled = EXCLUDED.enabled,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            user_id, birth_chart_id, subject_key,
            str(values.get("display_label") or spec["label"])[:80],
            str(values.get("life_status") or "unknown"),
            values.get("age_years"), values.get("birth_year"),
            str(values.get("employment_state") or "unknown"),
            str(values.get("location_context") or "unknown"),
            str(values.get("relationship_status") or "unknown"),
            linked, bool(values.get("enabled", True)),
        ),
    )
    conn.commit()
    return next(
        row for row in load_relative_profiles(conn, user_id=user_id, birth_chart_id=birth_chart_id)
        if row["subject_key"] == subject_key
    )
