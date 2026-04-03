"""
PostgreSQL: add UNIQUE (chart_id, user_id) on karma_insights.

Required for INSERT ... ON CONFLICT (chart_id, user_id) in karma_analysis/routes.py.
SQLite migration create_karma_insights_table.py already had UNIQUE; schema_postgres.sql did not.

Run from the backend directory with POSTGRES_DSN or DATABASE_URL set:
  python migrations/add_karma_insights_unique_constraint_postgres.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import execute, get_conn  # noqa: E402


def migrate() -> None:
    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT 1 FROM information_schema.table_constraints
            WHERE table_schema = 'public'
              AND table_name = 'karma_insights'
              AND constraint_name = 'karma_insights_chart_user_key'
            """,
        )
        if cur.fetchone():
            print("✅ karma_insights: constraint karma_insights_chart_user_key already exists")
            return

        # Remove duplicate (chart_id, user_id) rows; keep the newest id
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
        print("✅ karma_insights: added UNIQUE (chart_id, user_id)")


if __name__ == "__main__":
    migrate()
