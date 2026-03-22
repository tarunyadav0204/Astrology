import json
from typing import Dict, List, Optional

from db import execute, get_conn


class PhysicalTraitsCache:
    """
    Cache physical-trait analysis per birth chart (Postgres).
    `db_path` is accepted for backward compatibility and ignored.
    """

    def __init__(self, db_path: str = "astrology.db"):
        self._db_path = db_path  # unused; kept for call-site compatibility

    def _ensure_table(self, conn) -> None:
        execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS physical_traits_cache (
                id SERIAL PRIMARY KEY,
                birth_chart_id BIGINT NOT NULL,
                traits_data TEXT NOT NULL,
                user_feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
        )

    def get_cached_traits(self, birth_chart_id: int) -> Optional[List[Dict]]:
        """Retrieve cached traits for this birth chart."""
        with get_conn() as conn:
            self._ensure_table(conn)
            cur = execute(
                conn,
                """
                SELECT traits_data FROM physical_traits_cache
                WHERE birth_chart_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (birth_chart_id,),
            )
            result = cur.fetchone()

            if result:
                return json.loads(result[0])
        return None

    def cache_traits(self, birth_chart_id: int, traits: List[Dict]):
        """Cache traits for this birth chart."""
        traits_json = json.dumps(traits)
        with get_conn() as conn:
            self._ensure_table(conn)
            cur = execute(
                conn,
                """
                UPDATE physical_traits_cache
                SET traits_data = ?, created_at = CURRENT_TIMESTAMP
                WHERE birth_chart_id = ?
                """,
                (traits_json, birth_chart_id),
            )
            if cur.rowcount == 0:
                execute(
                    conn,
                    """
                    INSERT INTO physical_traits_cache (birth_chart_id, traits_data)
                    VALUES (?, ?)
                    """,
                    (birth_chart_id, traits_json),
                )
            conn.commit()

    def has_feedback(self, birth_chart_id: int) -> bool:
        """Check if feedback already exists for this chart."""
        if not birth_chart_id:
            return False

        with get_conn() as conn:
            self._ensure_table(conn)
            cur = execute(
                conn,
                """
                SELECT 1 FROM physical_traits_cache
                WHERE birth_chart_id = ? AND user_feedback IS NOT NULL AND user_feedback != ''
                LIMIT 1
                """,
                (birth_chart_id,),
            )
            return cur.fetchone() is not None

    def update_feedback(self, birth_chart_id: int, feedback: str):
        """Update user feedback for cached traits."""
        if not birth_chart_id:
            return

        with get_conn() as conn:
            self._ensure_table(conn)
            cur = execute(
                conn,
                """
                UPDATE physical_traits_cache
                SET user_feedback = ?
                WHERE birth_chart_id = ?
                """,
                (feedback, birth_chart_id),
            )
            if cur.rowcount == 0:
                execute(
                    conn,
                    """
                    INSERT INTO physical_traits_cache (birth_chart_id, traits_data, user_feedback)
                    VALUES (?, '[]', ?)
                    """,
                    (birth_chart_id, feedback),
                )
            conn.commit()
