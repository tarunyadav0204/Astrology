from typing import Any, Dict, List, Optional
from datetime import datetime

from db import get_conn, execute


class RedditService:
    """
    Lightweight service for storing Reddit questions and AstroRoshni draft answers.
    Uses the shared Postgres connection from db.py.
    """

    def __init__(self, db_path: str = "astrology.db") -> None:
        # db_path kept for backward compatibility; Postgres connection is centralized in db.py
        self.db_path = db_path
        self._init_tables()

    def _init_tables(self) -> None:
        """Create reddit_questions and reddit_answers tables if they do not exist."""
        with get_conn() as conn:
            execute(
                conn,
                """
                CREATE TABLE IF NOT EXISTS reddit_questions (
                    id SERIAL PRIMARY KEY,
                    reddit_id TEXT NOT NULL UNIQUE,
                    subreddit TEXT NOT NULL,
                    title TEXT,
                    body TEXT,
                    url TEXT,
                    author TEXT,
                    created_utc DOUBLE PRECISION,
                    has_birth_data BOOLEAN DEFAULT FALSE,
                    extracted_birth_data TEXT,
                    status TEXT DEFAULT 'collected',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
            )

            execute(
                conn,
                """
                CREATE TABLE IF NOT EXISTS reddit_answers (
                    id SERIAL PRIMARY KEY,
                    question_id INTEGER NOT NULL,
                    draft_markdown TEXT,
                    safety_flags TEXT,
                    status TEXT DEFAULT 'draft',
                    reviewed_by TEXT,
                    reviewed_at TIMESTAMP,
                    posted_at TIMESTAMP,
                    reddit_comment_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (question_id) REFERENCES reddit_questions (id)
                )
                """,
            )
            conn.commit()

    # Question helpers

    def upsert_question(self, data: Dict[str, Any]) -> int:
        """
        Insert or update a Reddit question.

        Required keys in data:
          - reddit_id, subreddit
        Optional:
          - title, body, url, author, created_utc, has_birth_data (bool),
            extracted_birth_data (JSON string), status, notes
        """
        reddit_id = data["reddit_id"]
        now = datetime.utcnow().isoformat(sep=" ", timespec="seconds")

        with get_conn() as conn:
            cur = execute(
                conn,
                "SELECT id FROM reddit_questions WHERE reddit_id = %s",
                (reddit_id,),
            )
            row = cur.fetchone()

            if row:
                question_id = row[0]
                execute(
                    conn,
                    """
                    UPDATE reddit_questions
                    SET subreddit = %s,
                        title = %s,
                        body = %s,
                        url = %s,
                        author = %s,
                        created_utc = %s,
                        has_birth_data = %s,
                        extracted_birth_data = %s,
                        status = COALESCE(%s, status),
                        notes = COALESCE(%s, notes),
                        updated_at = %s
                    WHERE id = %s
                    """,
                    (
                        data.get("subreddit"),
                        data.get("title"),
                        data.get("body"),
                        data.get("url"),
                        data.get("author"),
                        data.get("created_utc"),
                        bool(data.get("has_birth_data")),
                        data.get("extracted_birth_data"),
                        data.get("status"),
                        data.get("notes"),
                        now,
                        question_id,
                    ),
                )
            else:
                cur = execute(
                    conn,
                    """
                    INSERT INTO reddit_questions (
                        reddit_id, subreddit, title, body, url, author,
                        created_utc, has_birth_data, extracted_birth_data,
                        status, notes, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        reddit_id,
                        data.get("subreddit"),
                        data.get("title"),
                        data.get("body"),
                        data.get("url"),
                        data.get("author"),
                        data.get("created_utc"),
                        bool(data.get("has_birth_data")),
                        data.get("extracted_birth_data"),
                        data.get("status", "collected"),
                        data.get("notes"),
                        now,
                        now,
                    ),
                )
                question_id = cur.fetchone()[0]

            conn.commit()

        return question_id

    def list_questions(
        self,
        status: Optional[str] = None,
        has_birth_data: Optional[bool] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List questions for admin review / debugging."""
        where_clauses = []
        params: List[Any] = []

        if status:
            where_clauses.append("status = %s")
            params.append(status)
        if has_birth_data is not None:
            where_clauses.append("has_birth_data = %s")
            params.append(bool(has_birth_data))

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        with get_conn() as conn:
            cur = execute(
                conn,
                f"""
                SELECT *
                FROM reddit_questions
                {where_sql}
                ORDER BY COALESCE(created_utc, 0) DESC, id DESC
                LIMIT %s
                """,
                (*params, limit),
            )
            rows = cur.fetchall() or []
        return [dict(row) for row in rows]

    def update_question_status(self, question_id: int, status: str) -> None:
        now = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
        with get_conn() as conn:
            execute(
                conn,
                "UPDATE reddit_questions SET status = %s, updated_at = %s WHERE id = %s",
                (status, now, question_id),
            )
            conn.commit()

    # Answer helpers

    def create_draft_answer(
        self,
        question_id: int,
        draft_markdown: str,
        safety_flags: Optional[List[str]] = None,
    ) -> int:
        now = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
        flags_str = ",".join(safety_flags or [])

        with get_conn() as conn:
            cur = execute(
                conn,
                """
                INSERT INTO reddit_answers (
                    question_id, draft_markdown, safety_flags, status,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, 'draft', %s, %s)
                RETURNING id
                """,
                (question_id, draft_markdown, flags_str, now, now),
            )
            answer_id = cur.fetchone()[0]

            conn.commit()

        return answer_id

    def list_draft_answers(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List draft answers with their corresponding question metadata
        for admin review.
        """
        with get_conn() as conn:
            cur = execute(
                conn,
                """
                SELECT
                    a.id AS answer_id,
                    a.draft_markdown,
                    a.safety_flags,
                    a.status,
                    a.created_at,
                    q.id AS question_id,
                    q.reddit_id,
                    q.subreddit,
                    q.title,
                    q.body,
                    q.url,
                    q.author,
                    q.created_utc
                FROM reddit_answers a
                JOIN reddit_questions q ON a.question_id = q.id
                WHERE a.status = 'draft'
                ORDER BY a.created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall() or []
        return [dict(row) for row in rows]

    def update_answer_status(
        self,
        answer_id: int,
        status: str,
        reviewed_by: Optional[str] = None,
        draft_markdown: Optional[str] = None,
        reddit_comment_id: Optional[str] = None,
    ) -> None:
        """
        Update answer status. Optionally update edited markdown and
        record who reviewed it. Posting integration can set reddit_comment_id.
        """
        now = datetime.utcnow().isoformat(sep=" ", timespec="seconds")

        sets = ["status = %s", "updated_at = %s"]
        params: List[Any] = [status, now]

        if reviewed_by is not None:
            sets.append("reviewed_by = %s")
            sets.append("reviewed_at = %s")
            params.extend([reviewed_by, now])

        if draft_markdown is not None:
            sets.append("draft_markdown = %s")
            params.append(draft_markdown)

        if reddit_comment_id is not None:
            sets.append("reddit_comment_id = %s")
            sets.append("posted_at = %s")
            params.extend([reddit_comment_id, now])

        set_sql = ", ".join(sets)
        params.append(answer_id)

        with get_conn() as conn:
            execute(
                conn,
                f"UPDATE reddit_answers SET {set_sql} WHERE id = %s",
                tuple(params),
            )
            conn.commit()

