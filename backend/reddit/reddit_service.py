import sqlite3
from typing import Any, Dict, List, Optional
from datetime import datetime


class RedditService:
    """
    Lightweight service for storing Reddit questions and AstroRoshni draft answers.
    Uses the existing SQLite astrology.db database.
    """

    def __init__(self, db_path: str = "astrology.db") -> None:
        self.db_path = db_path
        self._init_tables()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self) -> None:
        """Create reddit_questions and reddit_answers tables if they do not exist."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS reddit_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reddit_id TEXT NOT NULL UNIQUE,
                subreddit TEXT NOT NULL,
                title TEXT,
                body TEXT,
                url TEXT,
                author TEXT,
                created_utc REAL,
                has_birth_data INTEGER DEFAULT 0,
                extracted_birth_data TEXT,
                status TEXT DEFAULT 'collected',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS reddit_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            """
        )

        conn.commit()
        conn.close()

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
        conn = self._get_conn()
        cursor = conn.cursor()

        reddit_id = data["reddit_id"]
        cursor.execute(
            "SELECT id FROM reddit_questions WHERE reddit_id = ?",
            (reddit_id,),
        )
        row = cursor.fetchone()

        now = datetime.utcnow().isoformat(sep=" ", timespec="seconds")

        if row:
            question_id = row["id"]
            cursor.execute(
                """
                UPDATE reddit_questions
                SET subreddit = ?, title = ?, body = ?, url = ?, author = ?,
                    created_utc = ?, has_birth_data = ?, extracted_birth_data = ?,
                    status = COALESCE(?, status),
                    notes = COALESCE(?, notes),
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    data.get("subreddit"),
                    data.get("title"),
                    data.get("body"),
                    data.get("url"),
                    data.get("author"),
                    data.get("created_utc"),
                    1 if data.get("has_birth_data") else 0,
                    data.get("extracted_birth_data"),
                    data.get("status"),
                    data.get("notes"),
                    now,
                    question_id,
                ),
            )
        else:
            cursor.execute(
                """
                INSERT INTO reddit_questions (
                    reddit_id, subreddit, title, body, url, author,
                    created_utc, has_birth_data, extracted_birth_data,
                    status, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    reddit_id,
                    data.get("subreddit"),
                    data.get("title"),
                    data.get("body"),
                    data.get("url"),
                    data.get("author"),
                    data.get("created_utc"),
                    1 if data.get("has_birth_data") else 0,
                    data.get("extracted_birth_data"),
                    data.get("status", "collected"),
                    data.get("notes"),
                    now,
                    now,
                ),
            )
            question_id = cursor.lastrowid

        conn.commit()
        conn.close()
        return question_id

    def list_questions(
        self,
        status: Optional[str] = None,
        has_birth_data: Optional[bool] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List questions for admin review / debugging."""
        conn = self._get_conn()
        cursor = conn.cursor()

        where_clauses = []
        params: List[Any] = []

        if status:
            where_clauses.append("status = ?")
            params.append(status)
        if has_birth_data is not None:
            where_clauses.append("has_birth_data = ?")
            params.append(1 if has_birth_data else 0)

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        cursor.execute(
            f"""
            SELECT *
            FROM reddit_questions
            {where_sql}
            ORDER BY COALESCE(created_utc, 0) DESC, id DESC
            LIMIT ?
            """,
            (*params, limit),
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def update_question_status(self, question_id: int, status: str) -> None:
        conn = self._get_conn()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
        cursor.execute(
            "UPDATE reddit_questions SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, question_id),
        )
        conn.commit()
        conn.close()

    # Answer helpers

    def create_draft_answer(
        self,
        question_id: int,
        draft_markdown: str,
        safety_flags: Optional[List[str]] = None,
    ) -> int:
        conn = self._get_conn()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
        flags_str = ",".join(safety_flags or [])

        cursor.execute(
            """
            INSERT INTO reddit_answers (
                question_id, draft_markdown, safety_flags, status,
                created_at, updated_at
            ) VALUES (?, ?, ?, 'draft', ?, ?)
            """,
            (question_id, draft_markdown, flags_str, now, now),
        )
        answer_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return answer_id

    def list_draft_answers(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List draft answers with their corresponding question metadata
        for admin review.
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
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
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        conn.close()
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
        conn = self._get_conn()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat(sep=" ", timespec="seconds")

        sets = ["status = ?", "updated_at = ?"]
        params: List[Any] = [status, now]

        if reviewed_by is not None:
            sets.append("reviewed_by = ?")
            sets.append("reviewed_at = ?")
            params.extend([reviewed_by, now])

        if draft_markdown is not None:
            sets.append("draft_markdown = ?")
            params.append(draft_markdown)

        if reddit_comment_id is not None:
            sets.append("reddit_comment_id = ?")
            sets.append("posted_at = ?")
            params.extend([reddit_comment_id, now])

        set_sql = ", ".join(sets)
        params.append(answer_id)

        cursor.execute(
            f"UPDATE reddit_answers SET {set_sql} WHERE id = ?",
            tuple(params),
        )
        conn.commit()
        conn.close()

