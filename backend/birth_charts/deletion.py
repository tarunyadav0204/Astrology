"""Cascade delete rows that reference birth_charts before removing the chart row."""
from __future__ import annotations

from typing import Optional

from db import execute


def delete_birth_chart_dependencies(conn, chart_id: int, userid: Optional[int] = None) -> None:
    """
    Remove or detach all data tied to a birth chart.
    Call inside an open transaction before DELETE FROM birth_charts.
    """
    chart_id = int(chart_id)

    execute(conn, "DELETE FROM event_timeline_jobs WHERE birth_chart_id = %s", (chart_id,))
    execute(conn, "DELETE FROM user_facts WHERE birth_chart_id = %s", (chart_id,))
    execute(conn, "DELETE FROM physical_traits_cache WHERE birth_chart_id = %s", (chart_id,))

    if userid is not None:
        execute(
            conn,
            """
            UPDATE chat_sessions
            SET birth_chart_id = NULL
            WHERE birth_chart_id = %s AND user_id = %s
            """,
            (chart_id, userid),
        )
    else:
        execute(
            conn,
            "UPDATE chat_sessions SET birth_chart_id = NULL WHERE birth_chart_id = %s",
            (chart_id,),
        )
