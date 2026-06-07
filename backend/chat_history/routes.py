"""
Chat History API Routes
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query, Header
from datetime import datetime, timedelta
import uuid
import json
import logging
import os
from auth import get_current_user
from db import get_conn, execute

logger = logging.getLogger(__name__)

def sanitize_text(text):
    """Remove invalid Unicode characters and surrogates to prevent encoding attacks"""
    if not isinstance(text, str):
        return str(text) if text is not None else ""
    text = text.encode('utf-8', 'surrogatepass').decode('utf-8', 'ignore')
    text = text.replace('\0', '')
    return text.strip()


def coerce_chat_birth_details(bd):
    """
    Normalize date/time like mobile ChatScreen (YYYY-MM-DD + HH:MM).
    ISO datetimes in `time` break ChartCalculator, which does time.split(':') for hours/minutes.
    """
    if not bd or not isinstance(bd, dict):
        return bd
    out = dict(bd)
    d = out.get("date")
    if isinstance(d, str) and "T" in d:
        out["date"] = d.split("T", 1)[0]
    t = out.get("time")
    if isinstance(t, str) and "T" in t:
        after = t.split("T", 1)[1]
        out["time"] = after[:5] if len(after) >= 5 else t
    return out


def _birth_chart_id_from_birth_details(bd) -> int | None:
    """Integer birth chart id from client birth_details, if present (mobile sends `id`)."""
    if not bd or not isinstance(bd, dict):
        return None
    for key in ("id", "birth_chart_id", "chart_id", "birthChartId"):
        v = bd.get(key)
        if v is None or v == "":
            continue
        try:
            n = int(v)
            if n > 0:
                return n
        except (TypeError, ValueError):
            continue
    return None


def _merge_with_original_question_if_present(
    original_question: str | None,
    followup_text: str,
    *,
    max_len: int = 600,
    original_truncate_len: int = 260,
) -> str:
    """Preserve original event/topic context by prepending original question when present."""
    base = (followup_text or "").strip()
    orig = (original_question or "").strip()
    if not orig:
        return base
    merged = f"{orig} {base}".strip()
    if len(merged) > max_len:
        merged = f"{orig[:original_truncate_len]}... {base}".strip()
    return merged


def _merge_clarification_chain_parts(
    parts: list[str],
    latest_text: str,
    *,
    max_len: int = 600,
) -> str:
    """Combine the active user clarification chain so narrow replies keep prior topic context."""
    clean_parts = [str(part or "").strip() for part in (parts or []) if str(part or "").strip()]
    latest = str(latest_text or "").strip()
    if latest and (not clean_parts or clean_parts[-1].lower() != latest.lower()):
        clean_parts.append(latest)
    if not clean_parts:
        return latest
    merged = " ".join(clean_parts)
    if len(merged) <= max_len:
        return merged
    # Keep the start topic anchor and the most recent narrowing replies.
    head = clean_parts[0]
    tail = " ".join(clean_parts[1:])
    if len(head) > 260:
        head = f"{head[:260].rstrip()}..."
    remaining = max_len - len(head) - 1
    if remaining <= 0:
        return head[:max_len]
    if len(tail) > remaining:
        tail = tail[-remaining:].lstrip()
    return f"{head} {tail}".strip()


def _coerce_int_or_none(value):
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _requested_period_from_intent(intent: dict | None) -> dict | None:
    if not isinstance(intent, dict) or not intent.get("needs_transits"):
        return None
    tr = intent.get("transit_request")
    if not isinstance(tr, dict):
        return None
    start_year = _coerce_int_or_none(tr.get("startYear") or tr.get("start_year"))
    end_year = _coerce_int_or_none(tr.get("endYear") or tr.get("end_year"))
    if start_year is None or end_year is None:
        logger.warning(
            "chat intent transit_request missing usable years; dropping transit period: %s",
            tr,
        )
        return None
    if end_year < start_year:
        start_year, end_year = end_year, start_year
    return {
        "start_year": start_year,
        "end_year": end_year,
        "yearMonthMap": tr.get("yearMonthMap") or {},
    }


def get_user_question_chain_for_clarification(session_id, current_message_id, conn):
    """
    Return user-question fragments for the active clarification chain.
    This preserves narrowing context across multi-step clarifications like:
    "lagna chart" -> "career" -> "potential".
    """
    boundary_cursor = execute(
        conn,
        """
        SELECT COALESCE(MAX(message_id), 0)
        FROM chat_messages
        WHERE session_id = %s
          AND sender = 'assistant'
          AND COALESCE(message_type, '') != 'clarification'
          AND message_id < %s
        """,
        (session_id, current_message_id),
    )
    boundary_row = boundary_cursor.fetchone()
    boundary_id = int(boundary_row[0] or 0) if boundary_row else 0

    cursor = execute(
        conn,
        """
        SELECT content
        FROM chat_messages
        WHERE session_id = %s
          AND sender = 'user'
          AND message_id > %s
          AND message_id < %s
        ORDER BY message_id ASC
        """,
        (session_id, boundary_id, current_message_id),
    )
    rows = cursor.fetchall() or []
    return [row[0] for row in rows if row and row[0]]


def _compact_stage_totals(stages):
    rows = [s for s in (stages or []) if isinstance(s, dict)]
    return {
        "input_chars": sum(int(s.get("input_chars") or 0) for s in rows),
        "output_chars": sum(int(s.get("output_chars") or 0) for s in rows),
        "input_tokens": sum(int(s.get("input_tokens") or 0) for s in rows),
        "output_tokens": sum(int(s.get("output_tokens") or 0) for s in rows),
        "cached_tokens": sum(int(s.get("cached_tokens") or 0) for s in rows),
        "non_cached_input_tokens": sum(int(s.get("non_cached_input_tokens") or 0) for s in rows),
        "elapsed_ms_sum": round(sum(float(s.get("elapsed_ms") or 0) for s in rows), 1),
    }


router = APIRouter(prefix="/chat-v2", tags=["chat_history"])

STANDARD_MAX_CLARIFICATIONS = 1
INSTANT_MAX_CLARIFICATIONS = 3

# Cap user turns per session so threads do not grow without bound in DB/UI. Clients must POST /session
# and retry when they receive SESSION_TURN_LIMIT_PREFIX (HTTP 409). Model context already uses ~last 3 Q&A.
MAX_USER_MESSAGES_PER_CHAT_SESSION = 40
SESSION_TURN_LIMIT_PREFIX = "session_turn_limit"


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)) or default)
    except (TypeError, ValueError):
        return default


CHAT_PROCESSING_STALE_MINUTES = _env_int("CHAT_PROCESSING_STALE_MINUTES", 12)
CHAT_QUEUED_STALE_MINUTES = _env_int("CHAT_QUEUED_STALE_MINUTES", 90)
CHAT_PROCESSING_STALE_MESSAGE = (
    "This reading was interrupted before it could finish. Please ask again; no credits were charged."
)


def _processing_started_at_age_minutes(started_at) -> float | None:
    if not started_at:
        return None
    if isinstance(started_at, str):
        try:
            started_at = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        except ValueError:
            return None
    if not hasattr(started_at, "tzinfo"):
        return None
    now = datetime.now(started_at.tzinfo) if started_at.tzinfo else datetime.now()
    try:
        return max(0.0, (now - started_at).total_seconds() / 60.0)
    except TypeError:
        return None


def _timestamp_is_future(value) -> bool:
    if not value:
        return False
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return False
    if not hasattr(value, "tzinfo"):
        return False
    now = datetime.now(value.tzinfo) if value.tzinfo else datetime.now()
    try:
        return value > now
    except TypeError:
        return False


def _claim_chat_processing_message(message_id: int, claim_id: str, *, claim_minutes: int = 35) -> str:
    """
    Atomically claim a processing message for one queue worker.

    Returns: claimed, completed, failed, missing, or busy.
    """
    with get_conn() as conn:
        _ensure_chat_messages_task_claim_cols(conn)
        conn.commit()
        cur = execute(
            conn,
            "SELECT status FROM chat_messages WHERE message_id = %s",
            (message_id,),
        )
        row = cur.fetchone()
        if not row:
            conn.commit()
            return "missing"
        status = str(row[0] or "").strip().lower()
        if status in {"completed", "failed", "cancelled"}:
            conn.commit()
            return status

        cur = execute(
            conn,
            """
                UPDATE chat_messages
                SET task_claim_id = %s,
                    task_claimed_until = CURRENT_TIMESTAMP + (%s * INTERVAL '1 minute'),
                    started_at = COALESCE(started_at, CURRENT_TIMESTAMP)
                WHERE message_id = %s
                  AND status = 'processing'
                  AND (
                    task_claimed_until IS NULL
                    OR task_claimed_until < CURRENT_TIMESTAMP
                    OR task_claim_id = %s
                  )
                RETURNING message_id
            """,
            (claim_id, int(claim_minutes), message_id, claim_id),
        )
        claimed = cur.fetchone()
        conn.commit()
        return "claimed" if claimed else "busy"


def _clear_chat_processing_claim(message_id: int, claim_id: str) -> None:
    try:
        with get_conn() as conn:
            _ensure_chat_messages_task_claim_cols(conn)
            execute(
                conn,
                """
                    UPDATE chat_messages
                    SET task_claim_id = NULL, task_claimed_until = NULL
                    WHERE message_id = %s AND task_claim_id = %s
                """,
                (message_id, claim_id),
            )
            conn.commit()
    except Exception:
        logger.exception("failed to clear chat task claim message_id=%s", message_id)


def _ensure_chat_messages_gate_metadata(conn):
    """Idempotent DDL — older DBs or skipped startup init may lack this column."""
    execute(conn, "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS gate_metadata TEXT")


def _ensure_chat_messages_parallel_llm_usage(conn):
    """JSON blob: per-branch + merge LLM metrics (parallel chat)."""
    execute(conn, "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS parallel_llm_usage TEXT")


def _ensure_chat_messages_engagement_updates(conn):
    """JSON array of non-final wait-time engagement snippets."""
    execute(conn, "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS engagement_updates TEXT")


def _ensure_chat_messages_task_claim_cols(conn):
    """Durable queue claim metadata for chat workers."""
    execute(conn, "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS task_claim_id TEXT")
    execute(conn, "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS task_claimed_until TIMESTAMP")
    execute(conn, "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS task_enqueued_at TIMESTAMP")


def _ensure_wait_side_conversation_tables(conn):
    """Side conversation shown while the main answer is still processing."""
    execute(conn, """
        CREATE TABLE IF NOT EXISTS chat_wait_conversations (
            conversation_id SERIAL PRIMARY KEY,
            main_message_id INTEGER UNIQUE NOT NULL,
            session_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            status TEXT DEFAULT 'active',
            gemini_cache_name TEXT,
            gemini_cache_model TEXT,
            gemini_cache_expires_at TIMESTAMP,
            cached_context_json TEXT,
            cached_context_version TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            closed_at TIMESTAMP
        )
    """)
    execute(conn, """
        CREATE TABLE IF NOT EXISTS chat_wait_conversation_messages (
            id SERIAL PRIMARY KEY,
            conversation_id INTEGER NOT NULL,
            main_message_id INTEGER NOT NULL,
            sender TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        )
    """)

    sp_num = [0]

    def _try_create_index(sql: str):
        # Never call conn.rollback() here: it would undo earlier DDL in the same transaction
        # (e.g. task_claimed_until added by _ensure_chat_messages_task_claim_cols in check_message_status).
        sp_num[0] += 1
        sp = f"wsidx_{sp_num[0]}"
        execute(conn, f"SAVEPOINT {sp}")
        try:
            execute(conn, sql)
        except Exception as exc:
            execute(conn, f"ROLLBACK TO SAVEPOINT {sp}")
            msg = str(exc or "")
            # Some production DB roles can read/write these tables but are not their owner,
            # so Postgres rejects CREATE INDEX IF NOT EXISTS during request handling.
            # If the table is already deployed, we should continue instead of failing chat polling.
            if "must be owner of table chat_wait_conversations" in msg or "must be owner of table chat_wait_conversation_messages" in msg:
                logger.warning("Skipping wait-side index ensure due to table ownership: %s", msg)
                return
            raise
        execute(conn, f"RELEASE SAVEPOINT {sp}")

    _try_create_index("CREATE INDEX IF NOT EXISTS idx_wait_conv_main_message ON chat_wait_conversations (main_message_id)")
    _try_create_index("CREATE INDEX IF NOT EXISTS idx_wait_conv_user ON chat_wait_conversations (user_id)")
    _try_create_index("CREATE INDEX IF NOT EXISTS idx_wait_msgs_conv ON chat_wait_conversation_messages (conversation_id, id)")


def _ensure_chat_messages_cache_token_cols(conn):
    """Token split columns for cache-aware billing visibility."""
    execute(conn, "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS llm_cached_input_tokens INTEGER")
    execute(conn, "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS llm_non_cached_input_tokens INTEGER")


def _attach_completed_status_payload(
    response: dict,
    *,
    content,
    completed_at,
    terms,
    glossary,
    summary_image,
    follow_up_questions,
    gate_metadata,
):
    """Hydrate the status payload for a completed response."""
    response["status"] = "completed"
    response["content"] = content
    response["completed_at"] = completed_at

    if terms:
        try:
            response["terms"] = json.loads(terms)
        except Exception:
            response["terms"] = []
    else:
        response["terms"] = []

    if glossary:
        try:
            response["glossary"] = json.loads(glossary)
        except Exception:
            response["glossary"] = {}
    else:
        response["glossary"] = {}

    response["summary_image"] = summary_image or None

    if follow_up_questions:
        try:
            response["follow_up_questions"] = json.loads(follow_up_questions)
        except Exception:
            response["follow_up_questions"] = []
    else:
        response["follow_up_questions"] = []

    if gate_metadata:
        try:
            meta = json.loads(gate_metadata)
            response["gate_metadata"] = meta
            if isinstance(meta, dict) and meta.get("intent_gate"):
                response["intent_gate"] = meta["intent_gate"]
            if isinstance(meta, dict) and isinstance(meta.get("first_purchase_bonus"), dict):
                response["first_purchase_bonus"] = meta["first_purchase_bonus"]
        except Exception:
            pass

    return response


def _should_preserve_completed_message(existing_status, existing_content) -> bool:
    """Never downgrade a saved completed answer because later side-effects failed."""
    if existing_status != "completed":
        return False
    return bool((existing_content or "").strip())


def init_chat_tables():
    """Initialize chat history tables with polling support"""
    with get_conn() as conn:
        # Sessions
        execute(conn, """
            CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                birth_chart_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Messages
        execute(conn, """
            CREATE TABLE IF NOT EXISTS chat_messages (
                message_id SERIAL PRIMARY KEY,
                session_id TEXT NOT NULL,
                sender TEXT NOT NULL CHECK (sender IN ('user', 'assistant')),
                content TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'completed' CHECK (status IN ('processing', 'completed', 'failed', 'cancelled')),
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT,
                follow_up_questions TEXT,
                category TEXT,
                canonical_question TEXT,
                categorized_at TIMESTAMP,
                language TEXT,
                intent_router_ms REAL,
                llm_input_tokens INTEGER,
                llm_output_tokens INTEGER,
                llm_prompt_chars INTEGER,
                llm_response_chars INTEGER,
                client_request_id TEXT
            )
        """)

        # Add columns for older deployments (safe idempotent)
        execute(conn, "ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS birth_chart_id INTEGER")
        execute(conn, "ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS chat_llm_provider TEXT")
        execute(conn, "ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS chat_llm_model TEXT")
        execute(conn, "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS follow_up_questions TEXT")
        execute(conn, "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS category TEXT")
        execute(conn, "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS canonical_question TEXT")
        execute(conn, "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS categorized_at TIMESTAMP")
        execute(conn, "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS language TEXT")
        execute(conn, "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS intent_router_ms REAL")
        execute(conn, "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS llm_input_tokens INTEGER")
        execute(conn, "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS llm_output_tokens INTEGER")
        _ensure_chat_messages_cache_token_cols(conn)
        execute(conn, "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS llm_prompt_chars INTEGER")
        execute(conn, "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS llm_response_chars INTEGER")
        execute(conn, "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS client_request_id TEXT")
        execute(conn, "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS message_type TEXT")
        _ensure_chat_messages_gate_metadata(conn)
        _ensure_chat_messages_parallel_llm_usage(conn)
        _ensure_chat_messages_engagement_updates(conn)
        _ensure_chat_messages_task_claim_cols(conn)
        _ensure_wait_side_conversation_tables(conn)

        # Indexes
        execute(conn, "CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON chat_sessions (user_id)")
        execute(conn, "CREATE INDEX IF NOT EXISTS idx_sessions_birth_chart ON chat_sessions (birth_chart_id)")
        execute(conn, "CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON chat_sessions (created_at)")
        execute(conn, "CREATE INDEX IF NOT EXISTS idx_messages_session_id ON chat_messages (session_id)")
        execute(conn, "CREATE INDEX IF NOT EXISTS idx_messages_status ON chat_messages (status)")
        execute(conn, "CREATE INDEX IF NOT EXISTS idx_messages_task_claimed_until ON chat_messages (task_claimed_until)")
        execute(conn, "CREATE INDEX IF NOT EXISTS idx_messages_task_enqueued_at ON chat_messages (task_enqueued_at)")

        # Glossary terms table for centralized term/definition management
        execute(conn, """
            CREATE TABLE IF NOT EXISTS glossary_terms (
                term_id TEXT PRIMARY KEY,
                display_text TEXT NOT NULL,
                definition TEXT NOT NULL,
                language TEXT DEFAULT 'english',
                aliases TEXT
            )
        """)

        conn.commit()

@router.post("/session")
async def create_chat_session(request: dict, current_user = Depends(get_current_user)):
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    birth_chart_id = request.get("birth_chart_id")

    with get_conn() as conn:
        execute(
            conn,
            "INSERT INTO chat_sessions (session_id, user_id, birth_chart_id) VALUES (%s, %s, %s)",
            (session_id, current_user.userid, birth_chart_id),
        )
        conn.commit()
    
    return {"session_id": session_id}

@router.post("/message")
async def save_chat_message(request: dict, current_user = Depends(get_current_user)):
    """Save a chat message"""
    session_id = request.get("session_id")
    sender = request.get("sender")  # 'user' or 'assistant'
    content = request.get("content")
    
    if not all([session_id, sender, content]):
        raise HTTPException(status_code=400, detail="Missing required fields")

    with get_conn() as conn:
        cur = execute(
            conn,
            "SELECT user_id FROM chat_sessions WHERE session_id = %s",
            (session_id,),
        )
        session = cur.fetchone()
        if not session or session[0] != current_user.userid:
            raise HTTPException(status_code=404, detail="Session not found")

        execute(
            conn,
            "INSERT INTO chat_messages (session_id, sender, content) VALUES (%s, %s, %s)",
            (session_id, sender, sanitize_text(content)),
        )
        conn.commit()
    
    return {"message": "Message saved"}

@router.get("/history")
async def get_chat_history(
    page: int = 1,
    limit: int = 20,
    list_mode: str = Query(
        "sessions",
        description="sessions: one row per chat thread (default). messages: one row per message, newest first. dates: one row per date bucket.",
    ),
    current_user=Depends(get_current_user),
):
    """Get user's chat history with pagination (sessions or individual messages)."""
    offset = (page - 1) * limit
    mode = (list_mode or "sessions").strip().lower()
    if mode not in ("sessions", "messages", "dates"):
        mode = "sessions"

    if mode == "dates":
        # Date pagination is usually consumed by mobile as 5 dates per page.
        effective_limit = 5 if limit == 20 else max(1, min(int(limit), 50))
        offset = (page - 1) * effective_limit
        with get_conn() as conn:
            cur = execute(
                conn,
                """
                    SELECT COUNT(*)
                    FROM (
                        SELECT DATE(cm.timestamp) AS day_key
                        FROM chat_messages cm
                        INNER JOIN chat_sessions cs ON cm.session_id = cs.session_id
                        WHERE cs.user_id = %s
                          AND EXISTS (
                              SELECT 1 FROM chat_messages mu
                              WHERE mu.session_id = cs.session_id AND mu.sender = 'user'
                          )
                        GROUP BY DATE(cm.timestamp)
                    ) t
                """,
                (current_user.userid,),
            )
            total_count_row = cur.fetchone()
            total_count = total_count_row[0] if total_count_row else 0

            cur = execute(
                conn,
                """
                    SELECT
                        DATE(cm.timestamp) AS day_key,
                        MAX(cm.timestamp) AS last_activity_at,
                        COUNT(*) AS message_count,
                        ARRAY_AGG(DISTINCT cm.session_id) AS session_ids
                    FROM chat_messages cm
                    INNER JOIN chat_sessions cs ON cm.session_id = cs.session_id
                    WHERE cs.user_id = %s
                      AND EXISTS (
                          SELECT 1 FROM chat_messages mu
                          WHERE mu.session_id = cs.session_id AND mu.sender = 'user'
                      )
                    GROUP BY DATE(cm.timestamp)
                    ORDER BY day_key DESC
                    LIMIT %s OFFSET %s
                """,
                (current_user.userid, effective_limit, offset),
            )
            day_rows = cur.fetchall() or []

            date_items = []
            for row in day_rows:
                day_key = str(row[0]) if row and row[0] is not None else None
                date_items.append(
                    {
                        "date_key": day_key,
                        "date_label": day_key,
                        "last_activity_at": row[1],
                        "message_count": int(row[2] or 0),
                        "session_ids": row[3] or [],
                    }
                )

        return {
            "list_mode": "dates",
            "dates": date_items,
            "pagination": {
                "page": page,
                "limit": effective_limit,
                "total": total_count,
                "has_more": offset + effective_limit < total_count,
            },
        }

    if mode == "messages":
        with get_conn() as conn:
            cur = execute(
                conn,
                """
                    SELECT COUNT(*)
                    FROM chat_messages cm
                    INNER JOIN chat_sessions cs ON cm.session_id = cs.session_id
                    WHERE cs.user_id = %s
                      AND EXISTS (
                          SELECT 1 FROM chat_messages mu
                          WHERE mu.session_id = cs.session_id AND mu.sender = 'user'
                      )
                """,
                (current_user.userid,),
            )
            total_count_row = cur.fetchone()
            total_count = total_count_row[0] if total_count_row else 0

            cur = execute(
                conn,
                """
                    SELECT
                        cm.message_id,
                        cm.session_id,
                        cm.sender,
                        cm.content,
                        cm.timestamp,
                        cs.created_at,
                        bc.name AS native_name_raw,
                        (
                            SELECT MAX(m2.timestamp)
                            FROM chat_messages m2
                            WHERE m2.session_id = cs.session_id
                        ) AS session_last_activity_at
                    FROM chat_messages cm
                    INNER JOIN chat_sessions cs ON cm.session_id = cs.session_id
                    LEFT JOIN birth_charts bc ON cs.birth_chart_id = bc.id
                    WHERE cs.user_id = %s
                      AND EXISTS (
                          SELECT 1 FROM chat_messages mu
                          WHERE mu.session_id = cs.session_id AND mu.sender = 'user'
                      )
                    ORDER BY cm.timestamp DESC NULLS LAST, cm.message_id DESC
                    LIMIT %s OFFSET %s
                """,
                (current_user.userid, limit, offset),
            )
            rows = cur.fetchall() or []

        from encryption_utils import EncryptionManager

        encryptor = EncryptionManager()
        message_items = []
        for row in rows:
            raw_name = row[6] if len(row) > 6 else None
            native_name = None
            if raw_name:
                try:
                    native_name = encryptor.decrypt(raw_name)
                except Exception:
                    native_name = raw_name
            raw_content = row[3] or ""
            preview = raw_content[:100] + "..." if len(raw_content) > 100 else raw_content
            session_last = row[7] if len(row) > 7 else None
            message_items.append(
                {
                    "message_id": row[0],
                    "session_id": row[1],
                    "sender": row[2],
                    "preview": preview,
                    "timestamp": row[4],
                    "session_created_at": row[5],
                    "session_last_activity_at": session_last,
                    "native_name": native_name,
                }
            )

        return {
            "list_mode": "messages",
            "messages": message_items,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "has_more": offset + limit < total_count,
            },
        }

    with get_conn() as conn:
        cur = execute(
            conn,
            """
                SELECT COUNT(*)
                FROM chat_sessions cs
                WHERE cs.user_id = %s
                  AND EXISTS (
                      SELECT 1 FROM chat_messages mu
                      WHERE mu.session_id = cs.session_id AND mu.sender = 'user'
                  )
            """,
            (current_user.userid,),
        )
        total_count_row = cur.fetchone()
        total_count = total_count_row[0] if total_count_row else 0

        cur = execute(
            conn,
            """
                SELECT
                    cs.session_id,
                    cs.created_at,
                    cm.content as first_message,
                    cs.birth_chart_id,
                    bc.name as native_name,
                    (
                        SELECT MAX(m2.timestamp)
                        FROM chat_messages m2
                        WHERE m2.session_id = cs.session_id
                    ) AS last_activity_at
                FROM chat_sessions cs
                LEFT JOIN chat_messages cm ON cs.session_id = cm.session_id
                    AND cm.sender = 'user'
                    AND cm.message_id = (
                        SELECT MIN(message_id)
                        FROM chat_messages
                        WHERE session_id = cs.session_id AND sender = 'user'
                    )
                LEFT JOIN birth_charts bc ON cs.birth_chart_id = bc.id
                WHERE cs.user_id = %s
                  AND EXISTS (
                      SELECT 1 FROM chat_messages mu
                      WHERE mu.session_id = cs.session_id AND mu.sender = 'user'
                  )
                ORDER BY last_activity_at DESC NULLS LAST, cs.created_at DESC
                LIMIT %s OFFSET %s
            """,
            (current_user.userid, limit, offset),
        )
        sessions = cur.fetchall() or []

    from encryption_utils import EncryptionManager

    encryptor = EncryptionManager()

    history = []
    for session in sessions:
        native_name = None
        if session[4]:  # If native_name exists
            try:
                native_name = encryptor.decrypt(session[4])
            except Exception:
                native_name = session[4]  # Use as-is if decryption fails

        last_act = session[5] if len(session) > 5 else None
        history.append(
            {
                "session_id": session[0],
                "created_at": session[1],
                "last_activity_at": last_act,
                "preview": session[2][:100] + "..." if session[2] and len(session[2]) > 100 else session[2],
                "birth_chart_id": session[3],
                "native_name": native_name,
            }
        )

    return {
        "list_mode": "sessions",
        "sessions": history,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_count,
            "has_more": offset + limit < total_count,
        },
    }

@router.get("/session/{session_id}")
async def get_chat_session(session_id: str, current_user = Depends(get_current_user)):
    """Get full conversation for a session. Includes native_name (birth chart name) from DB for the session."""
    with get_conn() as conn:
        cur = execute(
            conn,
            """
                SELECT cs.user_id, cs.birth_chart_id, cs.chat_llm_provider, cs.chat_llm_model,
                       bc.name as native_name_raw
                FROM chat_sessions cs
                LEFT JOIN birth_charts bc ON bc.id = cs.birth_chart_id
                WHERE cs.session_id = %s
            """,
            (session_id,),
        )
        session_row = cur.fetchone()

        if not session_row or session_row[0] != current_user.userid:
            raise HTTPException(status_code=404, detail="Session not found")

        raw_name = session_row[4] if len(session_row) > 4 else None
        sess_llm_provider = session_row[2] if len(session_row) > 2 else None
        sess_llm_model = session_row[3] if len(session_row) > 3 else None

        _ensure_chat_messages_gate_metadata(conn)
        conn.commit()

        cur = execute(
            conn,
            """
                SELECT message_id, sender, content, timestamp, completed_at, terms, glossary, images,
                       message_type, gate_metadata, parallel_llm_usage, status, started_at, follow_up_questions
                FROM chat_messages
                WHERE session_id = %s
                ORDER BY timestamp ASC
            """,
            (session_id,),
        )
        messages = cur.fetchall() or []

    native_name = None
    if raw_name:
        try:
            from encryption_utils import EncryptionManager
            enc = EncryptionManager()
            native_name = enc.decrypt(raw_name)
        except Exception:
            native_name = raw_name

    conversation = []
    for msg in messages:
        message_data = {
            "message_id": msg[0],
            "sender": msg[1],
            "content": msg[2],
            "timestamp": msg[3],
            "completed_at": msg[4],
            "native_name": native_name,
        }
        if msg[5]:  # terms
            try:
                message_data["terms"] = json.loads(msg[5])
            except:
                message_data["terms"] = []
        else:
            message_data["terms"] = []
        if msg[6]:  # glossary
            try:
                message_data["glossary"] = json.loads(msg[6])
            except:
                message_data["glossary"] = []
        else:
            message_data["glossary"] = []
        if len(msg) > 7 and msg[7]:  # images
            try:
                message_data["images"] = json.loads(msg[7])
            except:
                message_data["images"] = []
        else:
            message_data["images"] = []
        mt = msg[8] if len(msg) > 8 else None
        gm = msg[9] if len(msg) > 9 else None
        plu = msg[10] if len(msg) > 10 else None
        status = msg[11] if len(msg) > 11 else None
        started_at = msg[12] if len(msg) > 12 else None
        follow_up_questions = msg[13] if len(msg) > 13 else None
        message_data["message_type"] = mt
        message_data["status"] = status
        message_data["started_at"] = started_at
        if gm:
            try:
                meta = json.loads(gm)
                message_data["gate_metadata"] = meta
                if isinstance(meta, dict) and meta.get("intent_gate"):
                    message_data["intent_gate"] = meta.get("intent_gate")
            except Exception:
                message_data["gate_metadata"] = None
        else:
            message_data["gate_metadata"] = None
        if follow_up_questions:
            try:
                message_data["follow_up_questions"] = json.loads(follow_up_questions)
            except Exception:
                message_data["follow_up_questions"] = []
        else:
            message_data["follow_up_questions"] = []
        if status == "processing":
            with get_conn() as wait_conn:
                wait_side_payload = _fetch_wait_side_payload(wait_conn, msg[0])
                wait_conn.commit()
            if wait_side_payload:
                message_data["wait_conversation"] = {
                    "enabled": True,
                    "status": wait_side_payload.get("status"),
                    "messages": wait_side_payload.get("messages") or [],
                }
        conversation.append(message_data)

    return {
        "session_id": session_id,
        "birth_chart_id": session_row[1] if len(session_row) > 1 else None,
        "native_name": native_name,
        "chat_llm_provider": sess_llm_provider,
        "chat_llm_model": sess_llm_model,
        "messages": conversation,
    }

@router.post("/ask")
async def ask_question_async(request: dict, background_tasks: BackgroundTasks, current_user = Depends(get_current_user)):
    """Start async chat processing - returns immediately with message_id for polling"""
    from credits.credit_service import CreditService
    from ai.intent_router import IntentRouter
    from chat.fact_extractor import FactExtractor
    
    # Validate required fields
    session_id = request.get("session_id")
    question = request.get("question")
    birth_details = request.get("birth_details")
    client_request_id = request.get("client_request_id")
    mode = request.get("mode")  # e.g. "lab" for Chart Lab (educational) mode
    delivery_channel = str(request.get("delivery_channel") or request.get("deliveryChannel") or "").strip().lower()
    render_target = str(request.get("render_target") or request.get("renderTarget") or "").strip().lower()
    subject_gate_override = str(
        request.get("subject_gate_override") or request.get("subjectGateOverride") or ""
    ).strip().lower()
    subject_gate_memory = request.get("subject_gate_memory") or request.get("subjectGateMemory") or []
    if not isinstance(subject_gate_memory, list):
        subject_gate_memory = []
    
    if not session_id or not question or not birth_details:
        raise HTTPException(status_code=422, detail="Missing required fields: session_id, question, and birth_details")

    birth_details = coerce_chat_birth_details(birth_details)
    
    # Optional fields with defaults
    language = request.get("language", "english")
    response_style = request.get("response_style", "detailed")
    premium_analysis = request.get("premium_analysis", False)
    requested_chat_tier = str(request.get("chat_tier") or request.get("chatTier") or "standard").strip().lower()
    partnership_mode = request.get("partnership_mode", False) or request.get("partnershipMode", False)
    partner_birth_details = request.get("partner_birth_details") or {
        'name': request.get('partner_name') or request.get('partnerName'),
        'date': request.get('partner_date') or request.get('partnerDate'),
        'time': request.get('partner_time') or request.get('partnerTime'),
        'place': request.get('partner_place') or request.get('partnerPlace'),
        'latitude': request.get('partner_latitude') or request.get('partnerLatitude'),
        'longitude': request.get('partner_longitude') or request.get('partnerLongitude'),
        'timezone': request.get('partner_timezone') or request.get('partnerTimezone'),
        'gender': request.get('partner_gender') or request.get('partnerGender'),
        'partnership_relationship': (
            request.get('partnership_relationship')
            or request.get('partnershipRelationship')
            or request.get('relationship')
            or request.get('relationshipType')
        )
    } if partnership_mode else None

    if partnership_mode and partner_birth_details:
        partner_birth_details = coerce_chat_birth_details(partner_birth_details)
        partner_birth_details['partnership_relationship'] = (
            request.get('partnership_relationship')
            or request.get('partnershipRelationship')
            or partner_birth_details.get('partnership_relationship')
            or partner_birth_details.get('relationship')
            or partner_birth_details.get('relationshipType')
        )
    
    from utils.admin_settings import (
        chat_subject_gate_enabled_for_user,
        instant_chat_enabled_for_user,
        speech_chat_enabled_for_user,
    )

    instant_chat_requested = requested_chat_tier == "instant"
    speech_chat_requested = bool(request.get("speech_chat") or request.get("speechChat"))
    if speech_chat_requested and requested_chat_tier != "instant":
        raise HTTPException(status_code=400, detail="speech_chat requires chat_tier instant")
    instant_chat_active = (
        instant_chat_requested
        and not premium_analysis
        and not partnership_mode
        and instant_chat_enabled_for_user(current_user.userid)
    )
    if speech_chat_requested and not instant_chat_active:
        raise HTTPException(
            status_code=403,
            detail="Speech chat requires instant chat to be available for your account.",
        )
    if speech_chat_requested and not speech_chat_enabled_for_user(current_user.userid):
        raise HTTPException(status_code=403, detail="Speech chat is not enabled for your account.")
    speech_chat_billing = bool(speech_chat_requested and instant_chat_active)
    effective_chat_tier = "instant" if instant_chat_active else "standard"

    with get_conn() as conn:
        # Verify the session before any no-charge gates or credit checks.
        cur = execute(
            conn,
            "SELECT user_id, birth_chart_id FROM chat_sessions WHERE session_id = %s",
            (session_id,),
        )
        session = cur.fetchone()
        if not session or session[0] != current_user.userid:
            raise HTTPException(status_code=404, detail="Session not found")
        session_birth_chart_id = session[1] if len(session) > 1 else None

        if session_birth_chart_id is not None:
            requested_chart_id = _birth_chart_id_from_birth_details(birth_details)
            if requested_chart_id is not None and int(session_birth_chart_id) != int(requested_chart_id):
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "CHART_SESSION_MISMATCH: birth_details chart id does not match this chat session. "
                        "Create a new session for the selected chart."
                    ),
                )

        if client_request_id:
            cur = execute(
                conn,
                """
                    SELECT message_id, status, content, message_type, gate_metadata
                    FROM chat_messages
                    WHERE session_id = %s AND sender = 'assistant' AND client_request_id = %s
                    ORDER BY message_id DESC
                    LIMIT 1
                """,
                (session_id, client_request_id),
            )
            existing = cur.fetchone()
            if existing:
                assistant_message_id, existing_status, existing_content, existing_type, existing_gate_metadata = existing
                cur = execute(
                    conn,
                    """
                        SELECT message_id
                        FROM chat_messages
                        WHERE session_id = %s AND sender = 'user' AND message_id < %s
                        ORDER BY message_id DESC
                        LIMIT 1
                    """,
                    (session_id, assistant_message_id),
                )
                user_row = cur.fetchone()
                response = {
                    "user_message_id": user_row[0] if user_row else None,
                    "message_id": assistant_message_id,
                    "status": existing_status or "processing",
                    "message_type": existing_type or "answer",
                    "chat_tier": effective_chat_tier,
                    "content": existing_content or "",
                    "chart_insights": [],
                    "loading_messages": [],
                }
                if existing_gate_metadata:
                    try:
                        meta = json.loads(existing_gate_metadata)
                        response["gate_metadata"] = meta
                        if isinstance(meta, dict) and meta.get("intent_gate"):
                            response["intent_gate"] = meta.get("intent_gate")
                    except Exception:
                        pass
                return response

        cur = execute(
            conn,
            "SELECT COUNT(*) FROM chat_messages WHERE session_id = %s AND sender = 'user'",
            (session_id,),
        )
        user_turn_count = (cur.fetchone() or [0])[0] or 0
        if user_turn_count >= MAX_USER_MESSAGES_PER_CHAT_SESSION:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"{SESSION_TURN_LIMIT_PREFIX}: This conversation has reached the maximum length "
                    f"({MAX_USER_MESSAGES_PER_CHAT_SESSION} questions). Please start a new chat to continue."
                ),
            )

    is_plain_text_channel = delivery_channel == "whatsapp" or render_target == "plain_text"
    if (
        chat_subject_gate_enabled_for_user(current_user.userid)
        and not is_plain_text_channel
        and not partnership_mode
        and subject_gate_override not in {
            "selected_chart_only",
            "single_chart_only",
            "relationship_context_provided",
        }
    ):
        try:
            from ai.chat_subject_gate import ChatSubjectGate, build_subject_gate_message

            subject_gate = await ChatSubjectGate().classify(
                question=sanitize_text(question),
                birth_details=birth_details,
                language=language,
                subject_gate_memory=subject_gate_memory,
            )
            if subject_gate.get("gate_required"):
                assistant_content = build_subject_gate_message(
                    subject_gate,
                    selected_name=(birth_details or {}).get("name"),
                )
                if not assistant_content:
                    logger.warning("chat subject gate returned no user_message; continuing normal chat")
                    raise RuntimeError("subject gate missing user_message")
                gate_metadata = {
                    **subject_gate,
                    "no_charge": True,
                    "source": "chat_subject_gate",
                }
                with get_conn() as conn:
                    _ensure_chat_messages_gate_metadata(conn)
                    cur = execute(
                        conn,
                        """
                            INSERT INTO chat_messages (session_id, sender, content, status, completed_at)
                            VALUES (%s, %s, %s, %s, %s)
                            RETURNING message_id
                        """,
                        (session_id, "user", sanitize_text(question), "completed", datetime.now()),
                    )
                    user_message_id = cur.fetchone()[0]
                    cur = execute(
                        conn,
                        """
                            INSERT INTO chat_messages
                                (session_id, sender, content, status, message_type, gate_metadata, completed_at, client_request_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING message_id
                        """,
                        (
                            session_id,
                            "assistant",
                            sanitize_text(assistant_content),
                            "completed",
                            "native_gate",
                            json.dumps(gate_metadata, ensure_ascii=False),
                            datetime.now(),
                            client_request_id,
                        ),
                    )
                    assistant_message_id = cur.fetchone()[0]
                    conn.commit()
                return {
                    "user_message_id": user_message_id,
                    "message_id": assistant_message_id,
                    "status": "completed",
                    "message_type": "native_gate",
                    "intent_gate": gate_metadata.get("intent_gate"),
                    "gate_metadata": gate_metadata,
                    "chat_tier": effective_chat_tier,
                    "content": assistant_content,
                    "chart_insights": [],
                    "loading_messages": [],
                }
        except Exception as gate_exc:
            logger.warning("chat subject gate skipped after error: %s", gate_exc)

    # Check credit cost and user balance (first question free for standard chat)
    credit_service = CreditService()
    if partnership_mode:
        chat_cost = credit_service.get_credit_setting('partnership_analysis_cost')
    elif premium_analysis:
        chat_cost = credit_service.get_credit_setting('premium_chat_cost')
    elif instant_chat_active:
        chat_cost = (
            credit_service.get_credit_setting('speech_chat_cost')
            if speech_chat_billing
            else credit_service.get_credit_setting('instant_chat_cost')
        )
    else:
        chat_cost = credit_service.get_credit_setting('chat_question_cost')
    user_balance = credit_service.get_user_credits(current_user.userid)
    is_standard_chat = not partnership_mode and not premium_analysis and not instant_chat_active
    free_birth_hash = credit_service.create_free_question_birth_hash(birth_details)
    free_available = credit_service.is_free_standard_chat_question_available_for_birth_hash(
        current_user.userid,
        free_birth_hash,
    )
    using_free_question = is_standard_chat and free_available
    chat_key = (
        'partnership_analysis_cost'
        if partnership_mode
        else (
            'premium_chat_cost' if premium_analysis
            else (
                'speech_chat_cost' if instant_chat_active and speech_chat_billing
                else 'instant_chat_cost' if instant_chat_active
                else 'chat_question_cost'
            )
        )
    )
    effective_cost = 0 if using_free_question else credit_service.get_effective_cost(current_user.userid, chat_cost, chat_key)

    print(f"💳 CREDIT CHECK (chat-v2):")
    print(f"   User ID: {current_user.userid}")
    print(f"   Requested chat tier: {requested_chat_tier}")
    print(f"   Effective chat tier: {effective_chat_tier}")
    print(f"   Partnership Mode: {partnership_mode}")
    print(f"   Premium Analysis: {premium_analysis}")
    print(f"   Speech chat billing: {speech_chat_billing}")
    print(f"   Chat cost: {chat_cost} credits, effective: {effective_cost} (free_question: {using_free_question})")
    print(f"   User balance: {user_balance} credits")

    if user_balance < effective_cost:
        if partnership_mode:
            analysis_type = "Partnership Analysis"
        elif premium_analysis:
            analysis_type = "Premium Deep Analysis"
        elif instant_chat_active:
            analysis_type = "Speech chat" if speech_chat_billing else "Instant Chat"
        else:
            analysis_type = "Standard Analysis"
        print(f"❌ INSUFFICIENT CREDITS: Need {effective_cost}, have {user_balance}")
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits for {analysis_type}. You need {effective_cost} credits but have {user_balance}."
        )

    with get_conn() as conn:
        # Verify session belongs to user and load chart binding for transcript vs chart hardening.
        cur = execute(
            conn,
            "SELECT user_id, birth_chart_id FROM chat_sessions WHERE session_id = %s",
            (session_id,),
        )
        session = cur.fetchone()
        if not session or session[0] != current_user.userid:
            raise HTTPException(status_code=404, detail="Session not found")
        session_birth_chart_id = session[1] if len(session) > 1 else None

        # Reject stale client: session thread is for one chart; birth_details must not claim another.
        if session_birth_chart_id is not None:
            requested_chart_id = _birth_chart_id_from_birth_details(birth_details)
            if requested_chart_id is not None and int(session_birth_chart_id) != int(requested_chart_id):
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "CHART_SESSION_MISMATCH: birth_details chart id does not match this chat session. "
                        "Create a new session for the selected chart."
                    ),
                )

        # Idempotency: if this client_request_id was already processed for this session,
        # return the existing assistant/user message IDs instead of creating duplicates.
        if client_request_id:
            cur = execute(
                conn,
                """
                    SELECT message_id
                    FROM chat_messages
                    WHERE session_id = %s AND sender = 'assistant' AND client_request_id = %s
                    ORDER BY message_id DESC
                    LIMIT 1
                """,
                (session_id, client_request_id),
            )
            existing = cur.fetchone()
            if existing:
                assistant_message_id = existing[0]
                cur = execute(
                    conn,
                    """
                        SELECT message_id
                        FROM chat_messages
                        WHERE session_id = %s AND sender = 'user' AND message_id < %s
                        ORDER BY message_id DESC
                        LIMIT 1
                    """,
                    (session_id, assistant_message_id),
                )
                user_row = cur.fetchone()
                user_message_id = user_row[0] if user_row else None
                return {
                    "user_message_id": user_message_id,
                    "message_id": assistant_message_id,
                    "status": "processing",
                    "message_type": "answer",
                    "chat_tier": effective_chat_tier,
                    "chart_insights": [],
                    "loading_messages": [],
                }

        # Per-session size cap (new turns only; idempotent retries return above).
        cur = execute(
            conn,
            "SELECT COUNT(*) FROM chat_messages WHERE session_id = %s AND sender = 'user'",
            (session_id,),
        )
        user_turn_count = (cur.fetchone() or [0])[0] or 0
        if user_turn_count >= MAX_USER_MESSAGES_PER_CHAT_SESSION:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"{SESSION_TURN_LIMIT_PREFIX}: This conversation has reached the maximum length "
                    f"({MAX_USER_MESSAGES_PER_CHAT_SESSION} questions). Please start a new chat to continue."
                ),
            )

        # Save user question (sanitized)
        cur = execute(
            conn,
            """
                INSERT INTO chat_messages (session_id, sender, content, status, completed_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING message_id
            """,
            (session_id, "user", sanitize_text(question), "completed", datetime.now()),
        )
        user_message_id = cur.fetchone()[0]
        print(f"💾 User message saved with ID: {user_message_id}")

        # Create processing assistant message (track client_request_id for idempotency)
        cur = execute(
            conn,
            """
                INSERT INTO chat_messages (session_id, sender, content, status, started_at, client_request_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING message_id
            """,
            (session_id, "assistant", "", "processing", datetime.now(), client_request_id),
        )
        assistant_message_id = cur.fetchone()[0]
        print(f"💾 Assistant message saved with ID: {assistant_message_id}")

        conn.commit()
    
    # Refuse death-related questions without calling Gemini
    from ai.death_query_guard import is_death_related, REFUSAL_MESSAGE
    if is_death_related(sanitize_text(question)):
        print(f"🚫 Death-related question detected - returning refusal without analysis")
        with get_conn() as conn:
            execute(
                conn,
                """
                    UPDATE chat_messages
                    SET content = %s, status = %s, message_type = %s, completed_at = %s
                    WHERE message_id = %s
                """,
                (sanitize_text(REFUSAL_MESSAGE), "completed", "answer", datetime.now(), assistant_message_id),
            )
            conn.commit()
        return {
                "user_message_id": user_message_id,
                "message_id": assistant_message_id,
                "status": "completed",
                "message_type": "answer",
                "chat_tier": effective_chat_tier,
                "content": REFUSAL_MESSAGE,
                "chart_insights": [],
        }

    # Fetal / unborn sex determination: LLM classifier (multilingual), no keyword heuristics
    from ai.fetal_sex_query_classifier import FETAL_SEX_REFUSAL_MESSAGE, should_refuse_fetal_sex_determination
    try:
        if await should_refuse_fetal_sex_determination(
            question=sanitize_text(question),
            language=str(language or "english"),
        ):
            print("🚫 Fetal sex determination question detected (LLM gate) - returning refusal without analysis")
            with get_conn() as conn:
                execute(
                    conn,
                    """
                        UPDATE chat_messages
                        SET content = %s, status = %s, message_type = %s, completed_at = %s
                        WHERE message_id = %s
                    """,
                    (
                        sanitize_text(FETAL_SEX_REFUSAL_MESSAGE),
                        "completed",
                        "answer",
                        datetime.now(),
                        assistant_message_id,
                    ),
                )
                conn.commit()
            return {
                "user_message_id": user_message_id,
                "message_id": assistant_message_id,
                "status": "completed",
                "message_type": "answer",
                "chat_tier": effective_chat_tier,
                "content": FETAL_SEX_REFUSAL_MESSAGE,
                "chart_insights": [],
            }
    except Exception as exc:
        logger.warning("fetal sex gate skipped after error: %s", exc)

    # Get chart insights from intent router BEFORE starting background task
    chart_insights = []
    try:
        user_facts = {}
        d1_chart = None
        if not instant_chat_active:
            with get_conn() as conn:
                cur = execute(conn, "SELECT birth_chart_id FROM chat_sessions WHERE session_id = %s", (session_id,))
                session_data = cur.fetchone()
                birth_chart_id = session_data[0] if session_data else None
                
                if birth_chart_id:
                    fact_extractor = FactExtractor()
                    user_facts = fact_extractor.get_facts(birth_chart_id)
            
            # Build minimal D1 chart for intent router
            from calculators.chart_calculator import ChartCalculator
            from types import SimpleNamespace
            birth_obj = SimpleNamespace(**birth_details)
            chart_calc = ChartCalculator({})
            chart_data = chart_calc.calculate_chart(birth_obj)
            
            # Extract D1 chart with houses and planets
            d1_chart = {
                'ascendant': chart_data.get('ascendant', 0),
                'houses': [],
                'planets': {}
            }
            
            # Add houses with signs
            asc_sign = int(chart_data['ascendant'] / 30)
            sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
            for i in range(12):
                house_sign = (asc_sign + i) % 12
                d1_chart['houses'].append({
                    'house_number': i + 1,
                    'sign': sign_names[house_sign],
                    'planets': []
                })
            
            # Add planets to houses
            for planet_name, planet_data in chart_data.get('planets', {}).items():
                house_num = planet_data.get('house', 1)
                sign_num = planet_data.get('sign', 0)
                d1_chart['planets'][planet_name] = {
                    'house': house_num,
                    'sign': sign_names[sign_num]
                }
                d1_chart['houses'][house_num - 1]['planets'].append(planet_name)
        
        # Get clarification count from conversation state
        clarification_count = 0
        history = []
        with get_conn() as conn:
            cur = execute(conn, "SELECT clarification_count FROM conversation_state WHERE session_id = %s", (session_id,))
            state_row = cur.fetchone()
            clarification_count = state_row[0] if state_row else 0

            # Build last answered exchanges so instant router can understand follow-ups.
            cur = execute(
                conn,
                """
                    SELECT sender, content, message_type
                    FROM chat_messages
                    WHERE session_id = %s AND status = 'completed' AND content IS NOT NULL
                      AND content != ''
                    ORDER BY timestamp ASC
                """,
                (session_id,),
            )
            history_rows = cur.fetchall() or []
            i = 0
            while i < len(history_rows) - 1:
                if history_rows[i][0] == 'user' and history_rows[i+1][0] == 'assistant':
                    if history_rows[i+1][2] == 'answer':
                        history.append({
                            "question": history_rows[i][1],
                            "response": history_rows[i+1][1],
                        })
                    i += 2
                else:
                    i += 1
            history = history[-3:] if len(history) > 3 else history
        
        # Detect notification-originated questions to avoid clarification loops
        q_lower = (question or "").strip().lower()
        is_notification_question = False
        if q_lower:
            # Planet transit nudges (e.g. "How will Mars's transit into Aquarius on 2026-03-15 affect me...")
            if "transit into" in q_lower and "affect me" in q_lower:
                is_notification_question = True
            # Planet retrograde / direct nudges
            if "retrograde" in q_lower and "affect me" in q_lower:
                is_notification_question = True
            if "turning direct" in q_lower and "affect me" in q_lower:
                is_notification_question = True
            # Lunar phase nudges
            if "new moon" in q_lower and "affect me" in q_lower:
                is_notification_question = True
            if "full moon" in q_lower and "affect me" in q_lower:
                is_notification_question = True
            # Festival nudges
            if "festival" in q_lower and "remedies" in q_lower:
                is_notification_question = True
        
        is_whatsapp_plain_text = delivery_channel == "whatsapp" or render_target == "plain_text"
        max_clarifications = 0 if is_whatsapp_plain_text else (
            INSTANT_MAX_CLARIFICATIONS if instant_chat_active else STANDARD_MAX_CLARIFICATIONS
        )

        # If user is replying to a prior clarification, merge with original question so topic survives
        # (e.g., "car battery failure" + "last week of April").
        combined_question = question
        if clarification_count > 0:
            with get_conn() as conn:
                chain_parts = get_user_question_chain_for_clarification(session_id, assistant_message_id, conn)
                original_question = get_original_question_for_clarification(session_id, assistant_message_id, conn)
            combined_question = _merge_clarification_chain_parts(
                chain_parts or ([original_question] if original_question else []),
                question,
                max_len=600,
            )

        # Force READY if clarification limit reached, partnership mode, or notification-originated question
        force_ready_for_limit = (
            partnership_mode
            or clarification_count >= max_clarifications
            or is_notification_question
            or is_whatsapp_plain_text
        )
        
        intent_router = IntentRouter()
        query_context = request.get("query_context") or request.get("queryContext")
        if instant_chat_active:
            intent = await intent_router.classify_instant_intent(
                combined_question,
                history,
                clarification_count=clarification_count,
                max_clarifications=max_clarifications,
                language=language,
                force_ready=force_ready_for_limit,
                query_context=query_context,
            )
        else:
            intent = await intent_router.classify_intent(
                combined_question,
                [],
                user_facts,
                clarification_count=clarification_count,
                language=language,
                force_ready=force_ready_for_limit,
                d1_chart=d1_chart,
                query_context=query_context,
            )
        chart_insights = intent.get('chart_insights', [])
        print(f"📊 Got {len(chart_insights)} chart insights from intent router")
        
        # Mark Lab / educational mode explicitly on intent so downstream
        # prompt builder can switch to teaching-focused instructions.
        if mode == 'lab':
            intent['lab_mode'] = True
        if delivery_channel:
            intent['delivery_channel'] = delivery_channel
        if render_target:
            intent['render_target'] = render_target
        if delivery_channel == "whatsapp" or render_target == "plain_text":
            intent['plain_text_output'] = True
        
        # Handle clarification immediately - do NOT start background task
        if intent.get('status') == 'CLARIFY' and clarification_count < max_clarifications:
            print(f"❓ CLARIFICATION NEEDED - Returning immediately without background task")
            clarification_question = intent.get('clarification_question', 'Could you provide more details?')
            
            # Update assistant message with clarification
            with get_conn() as conn:
                execute(
                    conn,
                    """
                        UPDATE chat_messages
                        SET content = %s, status = %s, message_type = %s, completed_at = %s
                        WHERE message_id = %s
                    """,
                    (sanitize_text(clarification_question), "completed", "clarification", datetime.now(), assistant_message_id),
                )

                execute(
                    conn,
                    """
                        INSERT INTO conversation_state (session_id, clarification_count, extracted_context)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (session_id) DO UPDATE SET
                            clarification_count = conversation_state.clarification_count + 1,
                            extracted_context = EXCLUDED.extracted_context,
                            last_updated = CURRENT_TIMESTAMP
                    """,
                    (session_id, 1, json.dumps(intent.get('extracted_context', {}))),
                )

                conn.commit()
            print(f"✅ CLARIFICATION SAVED - Returning to user")
            return {
                "user_message_id": user_message_id,
                "message_id": assistant_message_id,
                "status": "completed",
                "message_type": "clarification",
                "chat_tier": effective_chat_tier,
                "content": clarification_question,
                "chart_insights": chart_insights
            }
        elif intent.get('status') == 'CLARIFY':
            print("⚠️ Clarification requested but limit reached - falling back to READY handling")
            
    except Exception as e:
        print(f"⚠️ Failed to get chart insights: {e}")
        import traceback
        traceback.print_exc()
        intent = None
        chart_insights = []
    
    # Normalize: ensure chart_insights is a list of valid objects only; no placeholders
    if not isinstance(chart_insights, list):
        chart_insights = []
    else:
        chart_insights = [x for x in chart_insights if isinstance(x, dict) and x.get("house_number") and x.get("message")]
    
    # Start processing. Cloud Tasks gives us durable retry across VM restarts; BackgroundTasks remains
    # the local/dev fallback and keeps the rollout safe until queue env is enabled.
    task_payload = {
        "message_id": assistant_message_id,
        "session_id": session_id,
        "question": sanitize_text(question),
        "user_id": current_user.userid,
        "language": language,
        "response_style": response_style,
        "premium_analysis": premium_analysis,
        "birth_details": birth_details,
        "chat_cost": chat_cost,
        "partnership_mode": partnership_mode,
        "partner_birth_details": partner_birth_details,
        "cached_intent": intent,
        "user_message_id": user_message_id,
        "using_free_question": using_free_question,
        "effective_cost": effective_cost,
        "chat_tier": effective_chat_tier,
        "speech_chat_billing": speech_chat_billing,
        "claim_id": str(uuid.uuid4()),
    }
    queued = False
    try:
        from chat_history.task_queue import enqueue_chat_processing_task
        queued = enqueue_chat_processing_task(message_id=assistant_message_id, payload=task_payload)
    except Exception as exc:
        logger.exception("chat queue enqueue failed before fallback message_id=%s: %s", assistant_message_id, exc)

    if queued:
        try:
            with get_conn() as conn:
                _ensure_chat_messages_task_claim_cols(conn)
                execute(
                    conn,
                    "UPDATE chat_messages SET task_enqueued_at = %s WHERE message_id = %s",
                    (datetime.now(), assistant_message_id),
                )
                conn.commit()
        except Exception as exc:
            logger.exception("failed to mark chat task enqueued message_id=%s: %s", assistant_message_id, exc)
    else:
        background_tasks.add_task(
            process_gemini_response,
            assistant_message_id, session_id, sanitize_text(question), current_user.userid, language, response_style, premium_analysis, birth_details, chat_cost, partnership_mode, partner_birth_details, intent, user_message_id, using_free_question, effective_cost, effective_chat_tier, speech_chat_billing
        )
    
    print(f"🚀 Returning IDs - User: {user_message_id}, Assistant: {assistant_message_id}")
    print(f"🚀 Returning {len(chart_insights)} chart insights: {chart_insights[:2] if chart_insights else 'EMPTY'}")
    return {
        "user_message_id": user_message_id,
        "message_id": assistant_message_id,
        "status": "processing",
        "message": "Analyzing your chart...",
        "chat_tier": effective_chat_tier,
        "chart_insights": chart_insights,
        "d1_chart": d1_chart
    }


@router.post("/internal/process")
async def process_chat_task(request: dict, x_chat_task_secret: str | None = Header(None, alias="X-Chat-Task-Secret")):
    """Internal Cloud Tasks worker endpoint for durable chat-v2 processing."""
    from chat_history.task_queue import chat_task_secret

    def optional_int(value):
        if value is None or value == "":
            return None
        return int(value)

    expected_secret = chat_task_secret()
    if not expected_secret or x_chat_task_secret != expected_secret:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        message_id = int(request.get("message_id"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="message_id is required")

    claim_id = str(request.get("claim_id") or uuid.uuid4())
    claim_minutes = int(os.getenv("CHAT_TASK_CLAIM_MINUTES", "35") or "35")
    claim_state = _claim_chat_processing_message(message_id, claim_id, claim_minutes=claim_minutes)
    if claim_state in {"completed", "failed", "cancelled"}:
        return {"ok": True, "state": claim_state, "message_id": message_id}
    if claim_state == "missing":
        raise HTTPException(status_code=404, detail="Message not found")
    if claim_state == "busy":
        logger.info("chat Cloud Task skipped busy message_id=%s claim_id=%s", message_id, claim_id)
        raise HTTPException(status_code=409, detail="Message is already being processed")

    try:
        await process_gemini_response(
            message_id=message_id,
            session_id=request.get("session_id"),
            question=sanitize_text(request.get("question")),
            user_id=int(request.get("user_id")),
            language=request.get("language", "english"),
            response_style=request.get("response_style", "detailed"),
            premium_analysis=bool(request.get("premium_analysis")),
            birth_details=request.get("birth_details"),
            chat_cost=int(request.get("chat_cost", 1) or 1),
            partnership_mode=bool(request.get("partnership_mode")),
            partner_birth_details=request.get("partner_birth_details"),
            cached_intent=request.get("cached_intent"),
            user_message_id=optional_int(request.get("user_message_id")),
            using_free_question=bool(request.get("using_free_question")),
            effective_cost=optional_int(request.get("effective_cost")),
            chat_tier=request.get("chat_tier", "standard"),
            speech_chat_billing=bool(request.get("speech_chat_billing")),
        )
        return {"ok": True, "state": "processed", "message_id": message_id}
    finally:
        _clear_chat_processing_claim(message_id, claim_id)


@router.get("/status/{message_id}")
async def check_message_status(message_id: int, current_user = Depends(get_current_user)):
    """Poll message status for async processing"""
    import time
    start_time = time.time()
    
    # print(f"🔍 [STATUS CHECK] messageId: {message_id}, user: {current_user.userid}, time: {time.time()}")
    
    try:
        db_start = time.time()
        with get_conn() as conn:
            _ensure_chat_messages_gate_metadata(conn)
            _ensure_chat_messages_parallel_llm_usage(conn)
            _ensure_chat_messages_engagement_updates(conn)
            _ensure_chat_messages_task_claim_cols(conn)
            _ensure_wait_side_conversation_tables(conn)
            conn.commit()
            cur = execute(
                conn,
                """
                    SELECT cm.status, cm.content, cm.error_message, cm.started_at, cm.completed_at,
                           cs.user_id, cm.message_type, cm.terms, cm.glossary, cm.images, cm.follow_up_questions,
                           cm.gate_metadata, cm.parallel_llm_usage, cm.engagement_updates,
                           cm.task_claimed_until, cm.task_enqueued_at
                    FROM chat_messages cm
                    JOIN chat_sessions cs ON cm.session_id = cs.session_id
                    WHERE cm.message_id = %s
                """,
                (message_id,),
            )
            result = cur.fetchone()
        db_time = time.time() - db_start
        # print(f"📊 [DB QUERY] took {db_time:.3f}s for messageId: {message_id}")
        
        if not result:
            print(f"❌ [STATUS] Message {message_id} not found")
            raise HTTPException(status_code=404, detail="Message not found")
        
        status, content, error_message, started_at, completed_at, user_id, message_type, terms, glossary, summary_image, follow_up_questions, gate_metadata, parallel_llm_usage, engagement_updates, task_claimed_until, task_enqueued_at = result
        
        # Verify message belongs to user
        if user_id != current_user.userid:
            print(f"❌ [STATUS] Access denied for messageId: {message_id}, user: {current_user.userid}")
            raise HTTPException(status_code=403, detail="Access denied")
        
        response = {"status": status, "message_type": message_type or "answer"}
        wait_side_payload = None
        with get_conn() as conn:
            wait_side_payload = _fetch_wait_side_payload(conn, message_id)
            conn.commit()
        if wait_side_payload:
            response["wait_conversation"] = {
                "enabled": True,
                "status": wait_side_payload.get("status"),
                "messages": wait_side_payload.get("messages") or [],
            }
        
        if status == "completed":
            _attach_completed_status_payload(
                response,
                content=content,
                completed_at=completed_at,
                terms=terms,
                glossary=glossary,
                summary_image=summary_image,
                follow_up_questions=follow_up_questions,
                gate_metadata=gate_metadata,
            )
        elif status == "failed" and (content or "").strip():
            _attach_completed_status_payload(
                response,
                content=content,
                completed_at=completed_at,
                terms=terms,
                glossary=glossary,
                summary_image=summary_image,
                follow_up_questions=follow_up_questions,
                gate_metadata=gate_metadata,
            )
            response["recovered_after_failure"] = True
            response["postprocess_error_message"] = error_message or None
        elif status == "failed":
            response["error_message"] = error_message or "An error occurred while processing your request"
        elif status == "processing":
            active_claim = _timestamp_is_future(task_claimed_until)
            stale_reference = task_enqueued_at or started_at
            stale_threshold_minutes = CHAT_QUEUED_STALE_MINUTES if task_enqueued_at else CHAT_PROCESSING_STALE_MINUTES
            age_minutes = _processing_started_at_age_minutes(stale_reference)
            if (
                not active_claim
                and age_minutes is not None
                and age_minutes >= stale_threshold_minutes
            ):
                with get_conn() as stale_conn:
                    execute(
                        stale_conn,
                        """
                            UPDATE chat_messages
                            SET status = %s, error_message = %s, completed_at = %s
                            WHERE message_id = %s AND status = %s
                        """,
                        (
                            "failed",
                            CHAT_PROCESSING_STALE_MESSAGE,
                            datetime.now(),
                            message_id,
                            "processing",
                        ),
                    )
                    stale_conn.commit()
                logger.warning(
                    "Marked stale processing chat message as failed: message_id=%s age_minutes=%.1f",
                    message_id,
                    age_minutes,
                )
                return {
                    "status": "failed",
                    "message_type": message_type or "answer",
                    "error_message": CHAT_PROCESSING_STALE_MESSAGE,
                }
            response["started_at"] = started_at
            response["message"] = "Still analyzing your chart..."
            if engagement_updates:
                try:
                    parsed_updates = json.loads(engagement_updates)
                    if isinstance(parsed_updates, list):
                        response["engagement_updates"] = parsed_updates
                except Exception:
                    response["engagement_updates"] = []
        
        total_time = time.time() - start_time
        # print(f"✅ [STATUS COMPLETE] messageId: {message_id}, status: {status}, total_time: {total_time:.3f}s")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        total_time = time.time() - start_time
        print(f"❌ [STATUS ERROR] messageId: {message_id}, error: {str(e)}, total_time: {total_time:.3f}s")
        import traceback
        traceback.print_exc()
        # Log to admin so status-check failures (DB/500) are visible
        try:
            from utils.error_logger import log_chat_error
            with get_conn() as conn2:
                cur = execute(
                    conn2,
                    """
                        SELECT cs.user_id, cm.session_id
                        FROM chat_messages cm
                        JOIN chat_sessions cs ON cs.session_id = cm.session_id
                        WHERE cm.message_id = %s
                    """,
                    (message_id,),
                )
                row = cur.fetchone()
            if row:
                user_id, sid = row[0], row[1]
                with get_conn() as conn3:
                    curq = execute(
                        conn3,
                        """
                            SELECT content
                            FROM chat_messages
                            WHERE session_id = %s AND sender = %s
                            ORDER BY message_id DESC
                            LIMIT 1
                        """,
                        (sid, 'user'),
                    )
                    qrow = curq.fetchone()
                question = (qrow[0][:500] if qrow else None) or f"(message_id: {message_id})"
                log_chat_error(user_id, 'Unknown', '', e, question, None, 'backend')
            else:
                err = Exception(f"Status check failed for message_id {message_id}: {e}")
                log_chat_error(None, 'Unknown', '', err, f"message_id: {message_id}", None, 'backend')
        except Exception as log_err:
            print(f"⚠️ Failed to log status error: {log_err}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/wait-conversation/{message_id}/reply")
async def reply_wait_conversation(message_id: int, request: dict, current_user = Depends(get_current_user)):
    """User reply in the temporary side conversation while the main answer is processing."""
    text = sanitize_text(request.get("content") or request.get("text") or "")
    if not text:
        raise HTTPException(status_code=422, detail="Missing reply content")
    try:
        from chat.wait_conversation_agent import chat_wait_side_conversation_enabled, generate_wait_side_reply

        if not chat_wait_side_conversation_enabled():
            raise HTTPException(status_code=404, detail="Wait conversation is not enabled")

        with get_conn() as conn:
            _ensure_wait_side_conversation_tables(conn)
            cur = execute(
                conn,
                """
                    SELECT c.conversation_id, c.status, c.gemini_cache_name, c.cached_context_json,
                           cm.status, cs.user_id
                    FROM chat_wait_conversations c
                    JOIN chat_messages cm ON cm.message_id = c.main_message_id
                    JOIN chat_sessions cs ON cs.session_id = c.session_id
                    WHERE c.main_message_id = %s
                """,
                (message_id,),
            )
            row = cur.fetchone()
            if not row or row[5] != current_user.userid:
                raise HTTPException(status_code=404, detail="Wait conversation not found")
            conversation_id, conv_status, cache_name, cached_context_json, main_status, _user_id = row
            if conv_status != "active" or main_status != "processing":
                raise HTTPException(status_code=409, detail="Wait conversation is no longer active")
            execute(
                conn,
                """
                    INSERT INTO chat_wait_conversation_messages
                    (conversation_id, main_message_id, sender, content, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                """,
                (conversation_id, message_id, "user", text, json.dumps({"kind": "user_reply"}, ensure_ascii=False)),
            )
            conn.commit()

        with get_conn() as conn:
            payload = _fetch_wait_side_payload(conn, message_id)
            conn.commit()
        if not payload:
            raise HTTPException(status_code=404, detail="Wait conversation not found")
        cache_payload = None
        if cached_context_json:
            try:
                cache_payload = json.loads(cached_context_json)
            except Exception:
                cache_payload = None
        assistant_text = await generate_wait_side_reply(
            user_text=text,
            conversation_history=payload.get("messages") or [],
            cache_name=payload.get("gemini_cache_name") or cache_name,
            cache_payload=cache_payload,
        )
        if not assistant_text:
            assistant_text = "That helps. I’m checking how this fits with the active dasha and house themes while the full reading finishes."
        with get_conn() as conn:
            execute(
                conn,
                """
                    INSERT INTO chat_wait_conversation_messages
                    (conversation_id, main_message_id, sender, content, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    conversation_id,
                    message_id,
                    "assistant",
                    sanitize_text(assistant_text),
                    json.dumps({"kind": "assistant_reply"}, ensure_ascii=False),
                ),
            )
            messages = _fetch_wait_side_messages(conn, message_id)
            conn.commit()
        return {"wait_conversation": {"enabled": True, "status": "active", "messages": messages}}
    except HTTPException:
        raise
    except Exception as exc:
        logger.info("wait conversation reply failed message_id=%s: %s", message_id, str(exc)[:200])
        raise HTTPException(status_code=500, detail="Failed to send wait conversation reply")


def get_original_question_for_clarification(session_id, current_message_id, conn):
    """
    Get the original user question that triggered the clarification chain.
    Returns None if not found or not applicable.
    """
    cursor = conn.cursor()
    
    print(f"\n🔍 ORIGINAL QUESTION LOOKUP:")
    print(f"   Session: {session_id}")
    print(f"   Current message ID: {current_message_id}")
    
    # Find the last assistant message with message_type='clarification' before current
    cursor = execute(
        conn,
        """
        SELECT message_id FROM chat_messages
        WHERE session_id = %s
          AND sender = 'assistant'
          AND message_type = 'clarification'
          AND message_id < %s
        ORDER BY timestamp DESC
        LIMIT 1
        """,
        (session_id, current_message_id),
    )
    
    clarification_msg = cursor.fetchone()
    if not clarification_msg:
        print(f"   ❌ No clarification message found before ID {current_message_id}")
        return None
    
    print(f"   ✅ Found clarification message ID: {clarification_msg[0]}")
    
    # Find the user message immediately before that clarification
    cursor = execute(
        conn,
        """
        SELECT content FROM chat_messages
        WHERE session_id = %s
          AND sender = 'user'
          AND message_id < %s
        ORDER BY timestamp DESC
        LIMIT 1
        """,
        (session_id, clarification_msg[0]),
    )
    
    result = cursor.fetchone()
    if result:
        print(f"   ✅ Found original question: {result[0][:100]}...")
    else:
        print(f"   ❌ No user message found before clarification")
    
    return result[0] if result else None


def get_original_user_message_id_for_faq(session_id: str, assistant_message_id: int, conn):
    """
    When the current turn is a user's answer to a clarification, return the message_id of the
    original user question (so we save category/canonical_question on that, not on the follow-up).
    Returns None if there was no clarification before this assistant message (i.e. first question).
    """
    cursor = execute(
        conn,
        """
        SELECT message_id FROM chat_messages
        WHERE session_id = %s
          AND sender = 'assistant'
          AND message_type = 'clarification'
          AND message_id < %s
        ORDER BY message_id DESC
        LIMIT 1
        """,
        (session_id, assistant_message_id),
    )
    row = cursor.fetchone()
    if not row:
        return None
    clarification_msg_id = row[0]
    cursor = execute(
        conn,
        """
        SELECT message_id FROM chat_messages
        WHERE session_id = %s
          AND sender = 'user'
          AND message_id < %s
        ORDER BY message_id DESC
        LIMIT 1
        """,
        (session_id, clarification_msg_id),
    )
    row = cursor.fetchone()
    return row[0] if row else None


async def _generate_and_store_engagement_updates(
    message_id: int,
    question: str,
    context: dict,
    intent: dict,
    language: str,
    user_facts: dict,
):
    """Best-effort interim snippets while the final answer is still processing."""
    try:
        from chat.engagement_agent import generate_wait_engagement_updates

        updates = await generate_wait_engagement_updates(
            question=question,
            context=context or {},
            intent=intent or {},
            language=language or "english",
            user_facts=user_facts or {},
        )
        if not updates:
            return
        with get_conn() as conn:
            _ensure_chat_messages_engagement_updates(conn)
            execute(
                conn,
                """
                    UPDATE chat_messages
                    SET engagement_updates = %s
                    WHERE message_id = %s AND status = %s
                """,
                (json.dumps(updates, ensure_ascii=False), message_id, "processing"),
            )
            conn.commit()
        logger.info("stored %s wait engagement update(s) for message_id=%s", len(updates), message_id)
    except Exception as exc:
        logger.info("wait engagement store skipped for message_id=%s: %s", message_id, str(exc)[:200])


def _store_engagement_updates_now(message_id: int, updates: list[dict]):
    """Persist immediate deterministic wait snippets before async generation starts."""
    if not updates:
        return
    try:
        with get_conn() as conn:
            _ensure_chat_messages_engagement_updates(conn)
            execute(
                conn,
                """
                    UPDATE chat_messages
                    SET engagement_updates = %s
                    WHERE message_id = %s AND status = %s
                """,
                (json.dumps(updates, ensure_ascii=False), message_id, "processing"),
            )
            conn.commit()
    except Exception as exc:
        logger.info("initial wait engagement store skipped for message_id=%s: %s", message_id, str(exc)[:200])


def _fetch_wait_side_messages(conn, main_message_id: int) -> list[dict]:
    _ensure_wait_side_conversation_tables(conn)
    try:
        cur = execute(
            conn,
            """
                SELECT c.conversation_id, c.status, m.id, m.sender, m.content, m.created_at
                FROM chat_wait_conversations c
                LEFT JOIN chat_wait_conversation_messages m ON m.conversation_id = c.conversation_id
                WHERE c.main_message_id = %s
                ORDER BY m.id ASC
            """,
            (main_message_id,),
        )
    except Exception as exc:
        msg = str(exc or "")
        if "permission denied for table chat_wait_conversations" in msg or "permission denied for table chat_wait_conversation_messages" in msg:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.warning("Skipping wait-side message fetch due to table permissions: %s", msg)
            return []
        raise
    rows = cur.fetchall() or []
    if not rows:
        return []
    messages = []
    for row in rows:
        if row[2] is None:
            continue
        messages.append({
            "id": row[2],
            "sender": row[3],
            "content": row[4],
            "created_at": row[5].isoformat() if hasattr(row[5], "isoformat") else row[5],
        })
    return messages


def _fetch_wait_side_payload(conn, main_message_id: int) -> dict | None:
    _ensure_wait_side_conversation_tables(conn)
    try:
        cur = execute(
            conn,
            """
                SELECT conversation_id, status, gemini_cache_name, gemini_cache_model, cached_context_json
                FROM chat_wait_conversations
                WHERE main_message_id = %s
            """,
            (main_message_id,),
        )
    except Exception as exc:
        msg = str(exc or "")
        if "permission denied for table chat_wait_conversations" in msg:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.warning("Skipping wait-side payload fetch due to table permissions: %s", msg)
            return None
        raise
    row = cur.fetchone()
    if not row:
        return None
    return {
        "conversation_id": row[0],
        "status": row[1],
        "gemini_cache_name": row[2],
        "gemini_cache_model": row[3],
        "cached_context_json": row[4],
        "messages": _fetch_wait_side_messages(conn, main_message_id),
    }


async def _start_wait_side_conversation(
    *,
    message_id: int,
    session_id: str,
    user_id: int,
    question: str,
    context: dict,
    intent: dict,
    language: str,
    user_facts: dict,
):
    try:
        from chat.wait_conversation_agent import (
            build_wait_side_cache_payload,
            chat_wait_side_conversation_enabled,
            create_wait_side_cache,
            generate_wait_side_reply,
        )

        if not chat_wait_side_conversation_enabled():
            return
        cache_payload = build_wait_side_cache_payload(
            question=question,
            context=context or {},
            intent=intent or {},
            language=language or "english",
            user_facts=user_facts or {},
        )
        cache_name, model_name, expires_at, _cached_model = await create_wait_side_cache(cache_payload=cache_payload)
        opening = await generate_wait_side_reply(
            user_text=None,
            conversation_history=[],
            cache_name=cache_name,
            cache_payload=cache_payload,
        )
        if not opening:
            opening = "I’m looking at the active dasha and transit themes while the full answer is prepared. Which part of this question feels most urgent to you right now?"
        with get_conn() as conn:
            _ensure_wait_side_conversation_tables(conn)
            cur = execute(
                conn,
                """
                    INSERT INTO chat_wait_conversations
                    (main_message_id, session_id, user_id, status, gemini_cache_name, gemini_cache_model,
                     gemini_cache_expires_at, cached_context_json, cached_context_version)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (main_message_id) DO UPDATE SET
                        status = chat_wait_conversations.status
                    RETURNING conversation_id
                """,
                (
                    message_id,
                    session_id,
                    user_id,
                    "active",
                    cache_name,
                    model_name,
                    expires_at,
                    json.dumps(cache_payload, ensure_ascii=False, default=str),
                    "v1",
                ),
            )
            conversation_id = cur.fetchone()[0]
            existing = _fetch_wait_side_messages(conn, message_id)
            if not existing:
                execute(
                    conn,
                    """
                        INSERT INTO chat_wait_conversation_messages
                        (conversation_id, main_message_id, sender, content, metadata)
                        VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        conversation_id,
                        message_id,
                        "assistant",
                        sanitize_text(opening),
                        json.dumps({"kind": "opening"}, ensure_ascii=False),
                    ),
                )
            conn.commit()
    except Exception as exc:
        logger.info("wait side conversation start skipped for message_id=%s: %s", message_id, str(exc)[:200])


async def _close_wait_side_conversation(message_id: int):
    try:
        from chat.wait_conversation_agent import delete_wait_side_cache, generate_wait_side_reply

        with get_conn() as conn:
            payload = _fetch_wait_side_payload(conn, message_id)
            if not payload or payload.get("status") != "active":
                conn.commit()
                return
            conn.commit()
        history = payload.get("messages") or []
        cache_payload = None
        if payload.get("cached_context_json"):
            try:
                cache_payload = json.loads(payload["cached_context_json"])
            except Exception:
                cache_payload = None
        closing = await generate_wait_side_reply(
            user_text=None,
            conversation_history=history,
            cache_name=payload.get("gemini_cache_name"),
            cache_payload=cache_payload,
            closing=True,
        )
        if not closing:
            closing = "I have the full reading ready now. I’ll bring the detailed answer below."
        with get_conn() as conn:
            execute(
                conn,
                """
                    INSERT INTO chat_wait_conversation_messages
                    (conversation_id, main_message_id, sender, content, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    payload["conversation_id"],
                    message_id,
                    "assistant",
                    sanitize_text(closing),
                    json.dumps({"kind": "closing"}, ensure_ascii=False),
                ),
            )
            execute(
                conn,
                """
                    UPDATE chat_wait_conversations
                    SET status = %s, closed_at = %s
                    WHERE main_message_id = %s
                """,
                ("closed", datetime.now(), message_id),
            )
            conn.commit()
        await delete_wait_side_cache(payload.get("gemini_cache_name"))
    except Exception as exc:
        logger.info("wait side conversation close skipped for message_id=%s: %s", message_id, str(exc)[:200])


async def process_gemini_response(message_id: int, session_id: str, question: str, user_id: int, language: str, response_style: str, premium_analysis: bool, birth_details: dict = None, chat_cost: int = 1, partnership_mode: bool = False, partner_birth_details: dict = None, cached_intent: dict = None, user_message_id: int = None, using_free_question: bool = False, effective_cost: int = None, chat_tier: str = "standard", speech_chat_billing: bool = False):
    """Background task to process Gemini response. user_message_id: ID of the user message to update with category/canonical_question."""
    import sys
    import os
    import json
    import asyncio
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from ai.gemini_chat_analyzer import GeminiChatAnalyzer
    from chat.chat_context_builder import ChatContextBuilder
    from credits.credit_service import CreditService
    from ai.intent_router import IntentRouter
    from chat.fact_extractor import FactExtractor
    from ai.death_query_guard import is_death_override_unlocked, is_death_related, REFUSAL_MESSAGE
    from chat.instant_chat_pipeline import generate_instant_chat_response

    try:
        effective_chat_tier = str(chat_tier or "standard").strip().lower()
        is_instant_chat = effective_chat_tier == "instant"
        death_analysis_unlocked = is_death_override_unlocked(question)
        # Refuse death-related questions without calling the model
        if is_death_related(question):
            print(f"🚫 Death-related question detected in background task - saving refusal")
            with get_conn() as conn:
                execute(
                    conn,
                    """
                        UPDATE chat_messages
                        SET content = %s, status = %s, message_type = %s, completed_at = %s
                        WHERE message_id = %s
                    """,
                    (sanitize_text(REFUSAL_MESSAGE), "completed", "answer", datetime.now(), message_id),
                )
                conn.commit()
            return
        
        # Get birth_chart_id from session
        with get_conn() as conn:
            cur = execute(conn, "SELECT birth_chart_id FROM chat_sessions WHERE session_id = %s", (session_id,))
            session_data = cur.fetchone()
            birth_chart_id = session_data[0] if session_data else None
        
        # Get user facts for intent routing
        user_facts = {}
        if birth_chart_id and not is_instant_chat:
            fact_extractor = FactExtractor()
            user_facts = fact_extractor.get_facts(birth_chart_id)
            if user_facts:
                print(f"📚 Retrieved {len(user_facts)} fact categories for intent routing")
        
        # Use birth data from request (required)
        if not birth_details:
            raise Exception("Birth details are required for chat analysis")
        
        # Format birth data same as mobile app to ensure consistent calculations
        # Use BirthData validator to get proper timezone calculation from lat/lon
        from main import BirthData
        
        # Create BirthData object to get auto-calculated timezone
        birth_data_obj = BirthData(
            name=birth_details.get('name', 'User'),
            date=birth_details['date'].split('T')[0] if 'T' in birth_details['date'] else birth_details['date'],
            time=birth_details['time'].split('T')[1][:5] if 'T' in birth_details['time'] else birth_details['time'],
            latitude=float(birth_details['latitude']),
            longitude=float(birth_details['longitude']),
            place=birth_details.get('place', 'Unknown')
        )
        
        # Extract data with auto-calculated timezone
        birth_data = {
            'name': birth_data_obj.name,
            'date': birth_data_obj.date,
            'time': birth_data_obj.time,
            'latitude': birth_data_obj.latitude,
            'longitude': birth_data_obj.longitude,
            'place': birth_data_obj.place,
            'timezone': birth_data_obj.timezone  # This is auto-calculated from lat/lon
        }
        
        # DEBUG: Log birth data being used in chat
        print(f"🔍 CHAT BIRTH DATA DEBUG:")
        print(f"   Raw birth_details: {birth_details}")
        print(f"   Formatted birth_data: {birth_data}")
        
        # Validate partnership mode data
        if partnership_mode and partner_birth_details:
            required_fields = ['name', 'date', 'time', 'latitude', 'longitude']
            for field in required_fields:
                if not partner_birth_details.get(field):
                    raise Exception(f"Partner {field} is required for partnership analysis")
            
            # Ensure time is not None
            if partner_birth_details.get('time') is None:
                raise Exception("Partner birth time cannot be empty for partnership analysis")
        
        # Build context
        context_builder = ChatContextBuilder()
        
        # Get conversation history for intent routing
        with get_conn() as conn:
            cur = execute(
                conn,
                """
                    SELECT sender, content, message_type
                    FROM chat_messages
                    WHERE session_id = %s AND status = 'completed' AND content IS NOT NULL
                      AND content != ''
                    ORDER BY timestamp ASC
                """,
                (session_id,),
            )
            history_rows = cur.fetchall() or []
            history = []
            
            # Pair up user questions with assistant responses
            i = 0
            while i < len(history_rows) - 1:
                if history_rows[i][0] == 'user' and history_rows[i+1][0] == 'assistant':
                    # Only include full answers, not clarifications
                    if history_rows[i+1][2] == 'answer':
                        history.append({
                            "question": history_rows[i][1],
                            "response": history_rows[i+1][1]
                        })
                    i += 2
                else:
                    i += 1
            
            # Keep only last 3 exchanges
            history = history[-3:] if len(history) > 3 else history
            
            # Get conversation state
            cur = execute(
                conn,
                "SELECT clarification_count, extracted_context FROM conversation_state WHERE session_id = %s",
                (session_id,),
            )
            state_row = cur.fetchone()
            clarification_count = state_row[0] if state_row else 0
            extracted_context = json.loads(state_row[1]) if state_row and state_row[1] else {}
        
        # === INTENT ROUTING ===
        import time
        routing_start = time.time()
        intent_router_ms = None  # set after intent when not partnership_mode
        
        intent = {'status': 'READY', 'mode': 'birth', 'category': 'general', 'extracted_context': {}}  # Default
        # Merged clarification chain (e.g. "eating habits" + "in general"); used for all generation below.
        combined_question = question

        if not partnership_mode:
            # Use AI to classify (Fast)
            print(f"\n{'='*80}")
            print(f"🛣️ ROUTING DECISION STARTED")
            print(f"{'='*80}")
            
            # Get conversation history
            with get_conn() as conn:
                cur = execute(
                    conn,
                    """
                        SELECT sender, content, message_type
                        FROM chat_messages
                        WHERE session_id = %s AND status = 'completed' AND content IS NOT NULL
                          AND content != ''
                        ORDER BY timestamp ASC
                    """,
                    (session_id,),
                )
                history_rows = cur.fetchall() or []
                history = []
                
                # Pair up user questions with assistant responses
                i = 0
                while i < len(history_rows) - 1:
                    if history_rows[i][0] == 'user' and history_rows[i+1][0] == 'assistant':
                        # Only include full answers, not clarifications
                        if history_rows[i+1][2] == 'answer':
                            history.append({
                                "question": history_rows[i][1],
                                "response": history_rows[i+1][1]
                            })
                        i += 2
                    else:
                        i += 1
                
                # Keep only last 3 exchanges
                history = history[-3:] if len(history) > 3 else history
                
                # Get conversation state
                cur = execute(
                    conn,
                    "SELECT clarification_count FROM conversation_state WHERE session_id = %s",
                    (session_id,),
                )
                state_row = cur.fetchone()
                clarification_count = state_row[0] if state_row else 0
            
            intent_router = IntentRouter()
            cached_delivery_channel = (
                str(cached_intent.get("delivery_channel") or "").strip().lower()
                if isinstance(cached_intent, dict)
                else ""
            )
            cached_render_target = (
                str(cached_intent.get("render_target") or "").strip().lower()
                if isinstance(cached_intent, dict)
                else ""
            )
            cached_plain_text_output = (
                bool(cached_intent.get("plain_text_output"))
                if isinstance(cached_intent, dict)
                else False
            )
            is_whatsapp_plain_text = (
                cached_delivery_channel == "whatsapp"
                or cached_render_target == "plain_text"
                or cached_plain_text_output
            )
            force_ready = question.startswith('@All_Events') or is_whatsapp_plain_text
            
            print(f"\n{'='*80}")
            print(f"🔗 CLARIFICATION CONTEXT CHECK")
            print(f"{'='*80}")
            print(f"Current question: {question}")
            print(f"Clarification count: {clarification_count}")
            
            # Check if this is a clarification response and combine with original question
            combined_question = question
            if clarification_count > 0:
                print(f"🔍 Clarification detected, looking for original question...")
                with get_conn() as conn:
                    chain_parts = get_user_question_chain_for_clarification(session_id, message_id, conn)
                    original_question = get_original_question_for_clarification(session_id, message_id, conn)
                    if chain_parts or original_question:
                        combined_question = _merge_clarification_chain_parts(
                            chain_parts or ([original_question] if original_question else []),
                            question,
                            max_len=500,
                        )
                        print(f"🔗 COMBINED QUESTION:")
                        print(f"   Chain parts: {chain_parts}")
                        print(f"   Clarification: {question}")
                        print(f"   Combined: {combined_question}")
                    else:
                        print(f"   ⚠️ No original question found, using current question only")
            else:
                print(f"✅ First question in session, no combination needed")
            
            print(f"{'='*80}\n")
            
            query_context = (
                cached_intent.get("query_context")
                if isinstance(cached_intent, dict) and isinstance(cached_intent.get("query_context"), dict)
                else None
            )
            max_clarifications = 0 if is_whatsapp_plain_text else (
                INSTANT_MAX_CLARIFICATIONS if is_instant_chat else STANDARD_MAX_CLARIFICATIONS
            )
            if is_instant_chat:
                intent = await intent_router.classify_instant_intent(
                    combined_question,
                    history,
                    clarification_count=clarification_count,
                    max_clarifications=max_clarifications,
                    language=language,
                    force_ready=force_ready,
                    query_context=query_context,
                )
            else:
                intent = await intent_router.classify_intent(
                    combined_question,
                    history,
                    user_facts,
                    language=language,
                    force_ready=force_ready,
                    query_context=query_context,
                )
            intent_router_ms = round((time.time() - routing_start) * 1000, 1)
            MAX_CLARIFICATIONS = max_clarifications
            
            # FAIL-SAFE: Force LIFESPAN_EVENT_TIMING for "When/Year" questions to avoid clarification trap.
            timing_keywords = ['when', 'year', 'which year', 'what year', 'kab', 'saal', 'samay']
            if (
                any(kw in question.lower() for kw in timing_keywords)
                and intent.get('status') == 'CLARIFY'
            ):
                print(f"🛡️ FAIL-SAFE TRIGGERED: Forcing LIFESPAN_EVENT_TIMING for timing question")
                intent['status'] = 'READY'
                intent['mode'] = 'LIFESPAN_EVENT_TIMING'
                intent['needs_transits'] = True

            if isinstance(cached_intent, dict):
                for channel_key in ("delivery_channel", "render_target", "plain_text_output"):
                    if cached_intent.get(channel_key) is not None:
                        intent[channel_key] = cached_intent.get(channel_key)

            # Special handling for LIFESPAN_EVENT_TIMING transit range (full answer only, not clarification turn)
            if intent.get('mode') == 'LIFESPAN_EVENT_TIMING' and intent.get('status') == 'READY':
                print(f"🎯 LIFESPAN_EVENT_TIMING detected - Setting wide transit range")
                # Calculate age 18 to +25 years
                birth_year = int(birth_data['date'].split('-')[0])
                start_year = birth_year + 18
                current_year = datetime.now().year
                end_year = current_year + 25
                
                intent['needs_transits'] = True
                intent['transit_request'] = {
                    "startYear": start_year,
                    "endYear": end_year,
                    "yearMonthMap": None # No sparse map - get all major transits for lifespan
                }
                print(f"🎯 Range set: {start_year} to {end_year}")

            print(f"🔍 CLARIFICATION CHECK:")
            print(f"   Intent status: {intent.get('status')}")
            print(f"   Clarification count: {clarification_count}")
            print(f"   Max allowed: {MAX_CLARIFICATIONS}")
            print(f"   Will clarify: {intent.get('status') == 'CLARIFY' and clarification_count < MAX_CLARIFICATIONS}")
            
            # Check if clarification needed and under limit
            if intent.get('status') == 'CLARIFY' and clarification_count < MAX_CLARIFICATIONS:
                print(f"✅ RETURNING CLARIFICATION QUESTION")
                # Return clarification question
                with get_conn() as conn:
                    execute(
                        conn,
                        """
                            UPDATE chat_messages
                            SET content = %s, status = %s, message_type = %s, completed_at = %s,
                                language = %s, intent_router_ms = %s
                            WHERE message_id = %s
                        """,
                        (
                            sanitize_text(intent.get('clarification_question', 'Could you provide more details?')),
                            "completed",
                            "clarification",
                            datetime.now(),
                            language,
                            intent_router_ms,
                            message_id,
                        ),
                    )
                    execute(
                        conn,
                        """
                            INSERT INTO conversation_state (session_id, clarification_count, extracted_context)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (session_id) DO UPDATE SET
                                clarification_count = conversation_state.clarification_count + 1,
                                extracted_context = EXCLUDED.extracted_context,
                                last_updated = CURRENT_TIMESTAMP
                        """,
                        (session_id, 1, json.dumps(intent.get('extracted_context', {}))),
                    )
                    conn.commit()
                print(f"✅ CLARIFICATION SAVED TO DATABASE, EXITING EARLY")
                return  # Exit early, no chart calculation needed
            elif intent.get('status') == 'READY':
                # Reset clarification count when ready to answer
                with get_conn() as conn:
                    execute(
                        conn,
                        """
                            INSERT INTO conversation_state (session_id, clarification_count, extracted_context)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (session_id) DO UPDATE SET
                                clarification_count = 0,
                                extracted_context = EXCLUDED.extracted_context,
                                last_updated = CURRENT_TIMESTAMP
                        """,
                        (session_id, 0, json.dumps(intent.get('extracted_context', {}))),
                    )
                    conn.commit()
                print(f"✅ RESET CLARIFICATION COUNT TO 0 (READY status)")
            
            routing_time = time.time() - routing_start
            print(f"✅ ROUTING DECISION COMPLETE: {(intent.get('mode') or 'birth').upper()} mode")
            print(f"Category: {intent.get('category', 'general')}")
            print(f"Routing time: {routing_time:.3f}s")
            print(f"{'='*80}\n")
        
        # Build context based on intent
        context_start = time.time()
        
        if is_instant_chat:
            print(f"\n{'='*80}")
            print(f"⚡ INSTANT CHAT MODE - Skipping deep context build")
            print(f"{'='*80}")
            context = {
                "analysis_type": "instant_chat",
                "instant_chat": True,
                "intent": intent,
                "birth_details": {
                    "name": birth_data.get("name"),
                    "date": birth_data.get("date"),
                    "time": birth_data.get("time"),
                    "place": birth_data.get("place"),
                },
            }
            context_time = time.time() - context_start
            print(f"✅ Instant chat pseudo-context prepared in {context_time:.3f}s")
            print(f"{'='*80}\n")
        elif partnership_mode and partner_birth_details:
            print(f"\n{'='*80}")
            print(f"👥 PARTNERSHIP MODE - Building synastry context")
            print(f"{'='*80}")
            print(f"Native: {birth_data.get('name')}")
            print(f"Partner: {partner_birth_details.get('name')}")
            context = context_builder.build_synastry_context(birth_data, partner_birth_details, combined_question, intent)
            context_time = time.time() - context_start
            print(f"✅ Synastry context built in {context_time:.3f}s")
            print(f"{'='*80}\n")
            
        elif intent['mode'] == 'annual':
            # === ANNUAL MODE ===
            print(f"\n{'='*80}")
            print(f"📅 ANNUAL MODE ACTIVATED")
            print(f"{'='*80}")
            target_year = intent.get('year', datetime.now().year)
            print(f"Target year: {target_year}")
            
            # Convert intent router transit request to old format if needed
            requested_period = _requested_period_from_intent(intent)
            if requested_period:
                print(f"Transit period: {requested_period['start_year']}-{requested_period['end_year']}")
            
            # Use build_complete_context with intent_result to get transit data
            context = context_builder.build_complete_context(
                birth_data, combined_question, None, requested_period, intent
            )
            
            # Add annual-specific data
            context['analysis_type'] = 'annual_forecast'
            context['focus_year'] = target_year
            
            context_time = time.time() - context_start
            print(f"✅ Annual context built in {context_time:.3f}s")
            print(f"{'='*80}\n")
            
        elif intent['mode'] == 'prashna':
            # === PRASHNA MODE ===
            print(f"\n{'='*80}")
            print(f"🔮 PRASHNA MODE ACTIVATED")
            print(f"{'='*80}")
            print(f"Question: {combined_question}")
            print(f"Category: {intent.get('category', 'general')}")
            
            user_location = {
                'latitude': birth_data.get('latitude'),
                'longitude': birth_data.get('longitude'),
                'place': birth_data.get('place', 'Query Location')
            }
            
            context = context_builder.build_prashna_context(
                user_location,
                combined_question,
                intent.get('category', 'general')
            )
            
            context_time = time.time() - context_start
            print(f"✅ PRASHNA CONTEXT READY in {context_time:.3f}s")
            print(f"{'='*80}\n")
            
        else:
            # === BIRTH CHART MODE (Standard) ===
            print(f"\n{'='*80}")
            print(f"🔮 BIRTH CHART MODE (Standard)")
            print(f"{'='*80}")
            
            # Convert intent router transit request to old format if needed
            requested_period = _requested_period_from_intent(intent)
            if requested_period:
                print(f"Transit period: {requested_period['start_year']}-{requested_period['end_year']}")
            
            # Log divisional charts being requested
            if intent.get('divisional_charts'):
                print(f"Divisional charts requested: {intent['divisional_charts']}")
            
            context = context_builder.build_complete_context(
                birth_data, combined_question, None, requested_period, intent
            )
            context_time = time.time() - context_start
            print(f"✅ Birth chart context built in {context_time:.3f}s")
            print(f"{'='*80}\n")
        
        # Get conversation history
        with get_conn() as conn:
            cur = execute(
                conn,
                """
                    SELECT sender, content
                    FROM chat_messages
                    WHERE session_id = %s AND status = 'completed' AND content IS NOT NULL
                      AND (sender = 'user' OR message_type = 'answer')
                    ORDER BY timestamp DESC
                    LIMIT 6
                """,
                (session_id,),
            )
            history_rows = cur.fetchall() or []
            history = []
            for i in range(0, len(history_rows), 2):
                if i + 1 < len(history_rows):
                    history.append({
                        "question": history_rows[i+1][1],
                        "response": history_rows[i][1]
                    })
            
            # Get user facts if birth_chart_id exists
            user_facts = {}
            if birth_chart_id:
                fact_extractor = FactExtractor()
                all_facts = fact_extractor.get_facts(birth_chart_id)
                
                # Filter facts based on intent category for relevance
                intent_category = intent.get('category', 'general')
                relevant_categories = {
                    'career': ['career', 'education', 'major_events'],
                    'job': ['career', 'education', 'major_events'],
                    'promotion': ['career', 'major_events'],
                    'business': ['career', 'wealth', 'major_events'],
                    'wealth': ['career', 'wealth', 'major_events'],
                    'money': ['career', 'wealth', 'major_events'],
                    'finance': ['career', 'wealth', 'major_events'],
                    'love': ['family', 'relationships', 'major_events'],
                    'relationship': ['family', 'relationships', 'major_events'],
                    'marriage': ['family', 'relationships', 'major_events', 'marriage'],
                    'partner': ['family', 'relationships', 'major_events'],
                    'spouse': ['family', 'relationships', 'major_events'],
                    'health': ['health', 'temporary_events', 'major_events'],
                    'disease': ['health', 'temporary_events', 'major_events'],
                    'child': ['family', 'major_events'],
                    'children': ['family', 'major_events'],
                    'pregnancy': ['family', 'health', 'major_events'],
                    'son': ['family', 'major_events'],
                    'daughter': ['family', 'major_events'],
                    'mother': ['family', 'major_events'],
                    'father': ['family', 'major_events'],
                    'siblings': ['family', 'major_events'],
                    'education': ['education', 'career', 'major_events'],
                    'property': ['wealth', 'major_events'],
                    'home': ['family', 'major_events'],
                    'travel': ['location', 'temporary_events', 'major_events'],
                    'visa': ['location', 'temporary_events', 'major_events'],
                    'foreign': ['location', 'temporary_events', 'major_events']
                }
                
                allowed_cats = relevant_categories.get(intent_category, ['career', 'family', 'health', 'location', 'preferences', 'education', 'relationships', 'major_events', 'temporary_events'])
                user_facts = {cat: items for cat, items in all_facts.items() if cat in allowed_cats}
                
                if user_facts:
                    print(f"📚 Filtered user facts for category '{intent_category}': {list(user_facts.keys())}")
        
        # Inject user facts into context
        if user_facts and not is_instant_chat:
            context['user_facts'] = user_facts

        if death_analysis_unlocked:
            context['death_analysis_unlocked'] = True
        
        # Inject extracted context from clarifications
        if intent.get('extracted_context') and not is_instant_chat:
            context['extracted_context'] = intent['extracted_context']
        
        # Override intent mode for @All_Events to force event prediction
        is_all_events_question = question.startswith('@All_Events')
        if is_all_events_question:
            print(f"🎯 @All_Events DETECTED - Overriding intent mode to PREDICT_EVENTS_FOR_PERIOD")
            intent['mode'] = 'PREDICT_EVENTS_FOR_PERIOD'
            context['intent']['mode'] = 'PREDICT_EVENTS_FOR_PERIOD'
            question = question.replace('@All_Events', '').strip()

        # Fire-and-forget wait-time engagement snippets. This must never delay or affect final answers.
        try:
            from chat.engagement_agent import (
                build_initial_wait_engagement_updates,
                chat_wait_engagement_enabled,
            )

            if (
                chat_wait_engagement_enabled()
                and not is_instant_chat
                and not partnership_mode
                and not partner_birth_details
                and not is_all_events_question
            ):
                _store_engagement_updates_now(
                    message_id,
                    build_initial_wait_engagement_updates(
                        question=question,
                        intent=intent,
                        language=language,
                    ),
                )
                asyncio.create_task(
                    _generate_and_store_engagement_updates(
                        message_id,
                        question,
                        context,
                        intent,
                        language,
                        user_facts,
                    )
                )
        except Exception as engagement_start_err:
            logger.info("wait engagement task not started for message_id=%s: %s", message_id, str(engagement_start_err)[:200])

        # V2 side conversation: starts only after clarification/native gates are resolved and context is ready.
        try:
            from chat.wait_conversation_agent import chat_wait_side_conversation_enabled

            if (
                chat_wait_side_conversation_enabled()
                and not is_instant_chat
                and not partnership_mode
                and not partner_birth_details
                and not is_all_events_question
            ):
                asyncio.create_task(
                    _start_wait_side_conversation(
                        message_id=message_id,
                        session_id=session_id,
                        user_id=user_id,
                        question=question,
                        context=context,
                        intent=intent,
                        language=language,
                        user_facts=user_facts,
                    )
                )
        except Exception as wait_side_start_err:
            logger.info("wait side conversation task not started for message_id=%s: %s", message_id, str(wait_side_start_err)[:200])
        
        # Generate response
        try:
            analyzer = GeminiChatAnalyzer()
        except Exception as init_error:
            from utils.error_logger import log_chat_error
            log_chat_error(user_id, birth_data.get('name', 'Unknown'), '', init_error, question, birth_data, 'backend')
            raise init_error

        if is_instant_chat:
            result = await generate_instant_chat_response(
                analyzer,
                question=combined_question,
                birth_data=birth_data,
                intent=intent,
                history=history,
                language=language,
                speech_mode=bool(speech_chat_billing),
            )
        else:
            result = await analyzer.generate_chat_response(
                user_question=combined_question,
                astrological_context=context,
                conversation_history=history,
                language=language,
                response_style=response_style,
                premium_analysis=premium_analysis,
                mode=intent.get('mode', 'default'),
                use_thinking_level_high=False,
                user_id=user_id,
            )
        
        # Update database with result
        with get_conn() as conn:
            _ensure_chat_messages_parallel_llm_usage(conn)
            _ensure_chat_messages_cache_token_cols(conn)
            if result.get('success'):
                # Use already parsed terms and glossary from GeminiChatAnalyzer
                terms = result.get('terms', [])
                glossary = result.get('glossary', {})

                # Deduct credits on successful response (or mark first question free as used)
                credit_service = CreditService()
                answer_gate_metadata = None
                first_purchase_bonus_payload = None
                skip_instant_charge = bool(is_instant_chat and result.get("skip_instant_credit_charge"))
                if skip_instant_charge:
                    success = True
                    print(f"⏭️ Instant conversational ack for user {user_id} — no credits charged")
                elif using_free_question:
                    free_birth_hash = credit_service.create_free_question_birth_hash(birth_details)
                    credit_service.mark_free_chat_question_used(user_id, birth_hash=free_birth_hash)
                    if is_instant_chat:
                        analysis_type = "Speech chat" if speech_chat_billing else "Instant Chat"
                    else:
                        analysis_type = "Premium Deep Analysis" if premium_analysis else "Standard Chat"
                    credit_service.record_zero_cost_feature_usage(
                        user_id,
                        "chat_question",
                        f"{analysis_type} (Free): {question[:50]}...",
                    )
                    try:
                        bonus_status = credit_service.get_first_purchase_bonus_status(user_id)
                        first_purchase_bonus_payload = bonus_status
                        logger.info(
                            "first_purchase_bonus_after_free_question userid=%s eligible=%s reason=%s bonus_credits=%s window_minutes=%s",
                            user_id,
                            bool(bonus_status.get("eligible")) if isinstance(bonus_status, dict) else None,
                            bonus_status.get("reason") if isinstance(bonus_status, dict) else None,
                            bonus_status.get("bonus_credits") if isinstance(bonus_status, dict) else None,
                            bonus_status.get("window_minutes") if isinstance(bonus_status, dict) else None,
                        )
                    except Exception:
                        logger.exception("first_purchase_bonus_after_free_question failed userid=%s", user_id)
                        first_purchase_bonus_payload = None
                    answer_gate_metadata = {
                        "free_question_completed": True,
                        "first_purchase_bonus": first_purchase_bonus_payload,
                    }
                    print(f"🆓 FREE QUESTION USED for user {user_id} (no credits deducted)")
                    success = True
                else:
                    amount_to_deduct = effective_cost if effective_cost is not None else chat_cost
                    if is_instant_chat:
                        analysis_type = "Speech chat" if speech_chat_billing else "Instant Chat"
                        spend_feature = "speech_chat" if speech_chat_billing else "instant_chat"
                    else:
                        analysis_type = "Premium Deep Analysis" if premium_analysis else "Standard Chat"
                        spend_feature = "chat_question"
                    success = credit_service.spend_credits(
                        user_id,
                        amount_to_deduct,
                        spend_feature,
                        f"{analysis_type}: {question[:50]}..."
                    )
                    if success:
                        print(f"✅ CREDITS DEDUCTED: {amount_to_deduct} credits for user {user_id}")

                if success:
                    
                    # Save category + canonical_question on the *original* user question only (not on clarification answers)
                    faq_metadata = result.get('faq_metadata')
                    if faq_metadata and user_message_id:
                        # If this turn was after a clarification, save FAQ on the original question, not the follow-up
                        original_user_msg_id = get_original_user_message_id_for_faq(session_id, message_id, conn)
                        target_message_id = original_user_msg_id if original_user_msg_id else user_message_id
                        if original_user_msg_id:
                            print(f"   📋 Clarification flow: saving FAQ on original user message {target_message_id} (not follow-up {user_message_id})")
                        execute(
                            conn,
                            """
                                UPDATE chat_messages
                                SET category = %s, canonical_question = %s, categorized_at = %s
                                WHERE message_id = %s
                            """,
                            (
                                faq_metadata.get('category') or None,
                                faq_metadata.get('canonical_question') or None,
                                datetime.now(),
                                target_message_id,
                            ),
                        )
                        print(f"   📋 FAQ saved on user message {target_message_id}: {faq_metadata.get('category')} / {faq_metadata.get('canonical_question', '')[:40]}...")
                    
                    # Get summary image from result if available (store as string, not JSON)
                    summary_image = result.get('summary_image', None)

                    # Normalize follow-up questions to a simple list of plain strings.
                    # The model may sometimes return objects like {"icon": "💡", "question": "Ask about ..."}.
                    # We strip any icon metadata here so the mobile client always receives clean text.
                    raw_follow_ups = result.get('follow_up_questions') or []
                    follow_up_questions: list[str] = []
                    if isinstance(raw_follow_ups, list):
                        for item in raw_follow_ups:
                            if isinstance(item, str):
                                follow_up_questions.append(sanitize_text(item))
                            elif isinstance(item, dict):
                                # Prefer explicit question/text field; ignore icon or other extras
                                q = item.get('question') or item.get('text') or ''
                                if q:
                                    follow_up_questions.append(sanitize_text(q))
                    else:
                        # Fallback: single string or unexpected type
                        if isinstance(raw_follow_ups, str):
                            follow_up_questions.append(sanitize_text(raw_follow_ups))
                    
                    timing_save = result.get("timing") or {}
                    parallel_usage_blob = timing_save.get("parallel_llm_usage")
                    if is_instant_chat:
                        instant_stages = []
                        if isinstance(cached_intent, dict) and isinstance(cached_intent.get("_llm_usage_stage"), dict):
                            first_stage = dict(cached_intent.get("_llm_usage_stage") or {})
                            first_stage["stage"] = "instant_intent_entry"
                            instant_stages.append(first_stage)
                        if isinstance(intent, dict) and isinstance(intent.get("_llm_usage_stage"), dict):
                            second_stage = dict(intent.get("_llm_usage_stage") or {})
                            second_stage["stage"] = "instant_intent_background"
                            instant_stages.append(second_stage)
                        if isinstance(result.get("instant_llm_usage_stage"), dict):
                            instant_stages.append(dict(result.get("instant_llm_usage_stage") or {}))
                        if instant_stages:
                            parallel_usage_blob = {
                                "kind": "instant_chat_usage",
                                "stages": instant_stages,
                                "totals": _compact_stage_totals(instant_stages),
                            }
                    specialist_branch_outputs = None
                    if isinstance(parallel_usage_blob, dict):
                        specialist_branch_outputs = parallel_usage_blob.get("specialist_branch_outputs")
                        if "specialist_branch_outputs" in parallel_usage_blob:
                            # Keep DB row lean: large specialist blobs are written to BigQuery.
                            parallel_usage_blob = {
                                k: v for k, v in parallel_usage_blob.items() if k != "specialist_branch_outputs"
                            }
                    parallel_usage_json = (
                        json.dumps(parallel_usage_blob) if parallel_usage_blob else None
                    )
                    token_usage_to_store = result.get("token_usage") or {}
                    prompt_chars_to_store = result.get("llm_prompt_chars")
                    response_chars_to_store = result.get("llm_response_chars")
                    if is_instant_chat and isinstance(parallel_usage_blob, dict):
                        totals = parallel_usage_blob.get("totals") if isinstance(parallel_usage_blob.get("totals"), dict) else {}
                        token_usage_to_store = {
                            "input_tokens": int(totals.get("input_tokens") or 0),
                            "output_tokens": int(totals.get("output_tokens") or 0),
                            "cached_tokens": int(totals.get("cached_tokens") or 0),
                            "non_cached_input_tokens": int(totals.get("non_cached_input_tokens") or 0),
                        }
                        prompt_chars_to_store = int(totals.get("input_chars") or 0)
                        response_chars_to_store = int(totals.get("output_chars") or 0)

                    if isinstance(specialist_branch_outputs, dict) and specialist_branch_outputs:
                        try:
                            from activity.publisher import publish_activity
                            published = publish_activity(
                                "chat_branch_outputs",
                                user_id=int(user_id),
                                resource_type="chat_message",
                                resource_id=str(message_id),
                                metadata={
                                    "message_id": int(message_id),
                                    "session_id": str(session_id),
                                    "language": str(language or "english"),
                                    "chat_llm_model": str(
                                        result.get("chat_llm_model")
                                        or (timing_save.get("chat_llm_model") or "")
                                    ),
                                    "question_preview": str(question or "")[:1000],
                                    "specialist_branch_outputs": specialist_branch_outputs,
                                },
                            )
                            if not published:
                                logger.warning(
                                    "chat_branch_outputs publish returned False: message_id=%s session_id=%s user_id=%s",
                                    message_id,
                                    session_id,
                                    user_id,
                                )
                            else:
                                logger.info(
                                    "chat_branch_outputs published to Pub/Sub: message_id=%s session_id=%s user_id=%s",
                                    message_id,
                                    session_id,
                                    user_id,
                                )
                        except Exception as e:
                            # Never fail chat persistence because of debug telemetry sink.
                            logger.exception(
                                "chat_branch_outputs publish failed: message_id=%s session_id=%s user_id=%s error=%s",
                                message_id,
                                session_id,
                                user_id,
                                str(e),
                            )

                    execute(
                        conn,
                        """
                            UPDATE chat_messages
                            SET content = %s, terms = %s, glossary = %s, images = %s,
                                follow_up_questions = %s, status = %s, message_type = %s,
                                completed_at = %s, language = %s, intent_router_ms = %s,
                                llm_input_tokens = %s, llm_output_tokens = %s,
                                llm_cached_input_tokens = %s, llm_non_cached_input_tokens = %s,
                                llm_prompt_chars = %s, llm_response_chars = %s,
                                parallel_llm_usage = %s, gate_metadata = %s
                            WHERE message_id = %s
                        """,
                        (
                            sanitize_text(result['response']),
                            json.dumps(terms),
                            json.dumps(glossary),
                            summary_image,  # Store as string URL, not JSON
                            json.dumps(follow_up_questions),
                            "completed",
                            "answer",
                            datetime.now(),
                            language,
                            intent_router_ms,
                            int((token_usage_to_store or {}).get("input_tokens") or 0) or None,
                            int((token_usage_to_store or {}).get("output_tokens") or 0) or None,
                            int((token_usage_to_store or {}).get("cached_tokens") or 0) or None,
                            int((token_usage_to_store or {}).get("non_cached_input_tokens") or 0) or None,
                            int(prompt_chars_to_store) if prompt_chars_to_store is not None else None,
                            int(response_chars_to_store) if response_chars_to_store is not None else None,
                            parallel_usage_json,
                            json.dumps(answer_gate_metadata) if answer_gate_metadata else None,
                            message_id,
                        ),
                    )
                    timing = result.get("timing") or {}
                    llm_prov = timing.get("chat_llm_provider")
                    llm_mod = (result.get("chat_llm_model") or timing.get("chat_llm_model") or "").strip()
                    if llm_mod:
                        prov = (str(llm_prov).strip()[:32] if llm_prov else None) or "unknown"
                        mod = llm_mod[:200]
                        execute(
                            conn,
                            """
                            UPDATE chat_sessions
                            SET chat_llm_provider = %s, chat_llm_model = %s
                            WHERE session_id = %s
                            """,
                            (prov, mod, session_id),
                        )
                else:
                    print(f"❌ CREDIT DEDUCTION FAILED for user {user_id}")
                    try:
                        from utils.error_logger import log_chat_error
                        credit_err = Exception("Credit deduction failed")
                        username = (birth_details or {}).get('name', 'Unknown')
                        log_chat_error(user_id, username, '', credit_err, question, birth_details, 'backend')
                    except Exception:
                        pass
                    execute(
                        conn,
                        """
                            UPDATE chat_messages
                            SET status = %s, error_message = %s, completed_at = %s
                            WHERE message_id = %s
                        """,
                        ("failed", "Credit deduction failed. Please try again.", datetime.now(), message_id),
                    )
            else:
                # Prefer user-facing text from analyzer; never persist raw provider errors to clients.
                error_msg = result.get('response') or result.get(
                    'error', 'Unable to process your request at this time. Please try again.'
                )
                error_msg = sanitize_text(error_msg)
                try:
                    from utils.error_logger import log_chat_error
                    err = Exception(result.get('error') or error_msg)
                    username = (birth_details or {}).get('name', 'Unknown')
                    log_chat_error(user_id, username, '', err, question, birth_details, 'backend')
                except Exception:
                    pass
                execute(
                    conn,
                    """
                        UPDATE chat_messages
                        SET status = %s, error_message = %s, completed_at = %s
                        WHERE message_id = %s
                    """,
                    ("failed", error_msg, datetime.now(), message_id),
                )
            
            conn.commit()

        if result.get('success'):
            await _close_wait_side_conversation(message_id)
        
        # Extract facts AFTER transaction commits to avoid database lock
        if result.get('success') and birth_chart_id:
            try:
                fact_extractor = FactExtractor()
                await fact_extractor.extract_facts(question, result['response'], birth_chart_id)
            except Exception as e:
                print(f"❌ Fact extraction error: {e}")

        # Push notification when response is ready (user may have left the app)
        if result.get('success'):
            try:
                from nudge_engine import db as nudge_db
                from nudge_engine import push as push_module
                with nudge_db.get_conn() as conn_nudge:
                    nudge_db.init_nudge_tables(conn_nudge)
                    tokens = nudge_db.get_device_tokens_for_user(conn_nudge, user_id)
                    for token, _platform in tokens:
                        push_module.send_expo_push(
                            token,
                            "Your AstroRoshni response is ready",
                            "Tap to view your analysis.",
                            data={"cta": "astroroshni://chat", "session_id": session_id},
                        )
            except Exception as push_err:
                print(f"Push (response ready) failed: {push_err}")
        
    except Exception as e:
        # Handle any errors with user-friendly message and log to admin error list
        user_friendly_error = "I'm having trouble analyzing your chart right now. Please try again in a moment."
        try:
            from utils.error_logger import log_chat_error
            username = (birth_details or {}).get('name', 'Unknown')
            log_chat_error(user_id, username, '', e, question, birth_details, 'backend')
        except Exception as log_err:
            print(f"⚠️ Failed to log error to chat_error_logs: {log_err}")
        with get_conn() as conn:
            cur = execute(
                conn,
                """
                    SELECT status, content
                    FROM chat_messages
                    WHERE message_id = %s
                """,
                (message_id,),
            )
            existing_row = cur.fetchone()
            if existing_row and _should_preserve_completed_message(existing_row[0], existing_row[1]):
                conn.commit()
                logger.warning(
                    "Preserved completed chat message after post-processing error for message_id=%s: %s",
                    message_id,
                    str(e)[:240],
                )
                return
            execute(
                conn,
                """
                    UPDATE chat_messages
                    SET status = %s, error_message = %s, completed_at = %s
                    WHERE message_id = %s
                """,
                ("failed", user_friendly_error, datetime.now(), message_id),
            )
            conn.commit()
        print(f"Error processing message {message_id}: {e}")
        import traceback
        traceback.print_exc()

@router.delete("/message/{message_id}")
async def delete_message(message_id: int, current_user = Depends(get_current_user)):
    """Hard delete a specific message"""
    print(f"🗑️ DELETE STEP 1: Request received for message ID: {message_id} by user: {current_user.userid}")
    
    try:
        with get_conn() as conn:
            print(f"🗑️ DELETE STEP 2: Database connection established")

            # First, let's see what messages exist for this user
            cur = execute(
                conn,
                """
                    SELECT cm.message_id, cm.sender, cm.message_type, SUBSTRING(cm.content, 1, 50)
                    FROM chat_messages cm
                    JOIN chat_sessions cs ON cm.session_id = cs.session_id
                    WHERE cs.user_id = %s
                    ORDER BY cm.message_id DESC
                    LIMIT 10
                """,
                (current_user.userid,),
            )
            user_messages = cur.fetchall() or []
            print(f"🔍 Recent messages for user {current_user.userid}:")
            for msg in user_messages:
                print(f"   ID: {msg[0]}, Sender: {msg[1]}, Type: {msg[2]}, Content: {msg[3]}...")

            print(f"🗑️ DELETE STEP 3: Verifying message ownership")
            cur = execute(
                conn,
                """
                    SELECT cm.session_id, cs.user_id, cm.message_type, cm.sender
                    FROM chat_messages cm
                    JOIN chat_sessions cs ON cm.session_id = cs.session_id
                    WHERE cm.message_id = %s
                """,
                (message_id,),
            )
            result = cur.fetchone()
            print(f"🔍 Database lookup result for ID {message_id}: {result}")

            if not result:
                print(f"❌ Message {message_id} not found in database")
                raise HTTPException(status_code=404, detail=f"Message {message_id} not found in database")

            session_id, user_id, message_type, sender = result
            print(f"🔍 Message details - User: {user_id}, Type: {message_type}, Sender: {sender}")
            print(f"🔍 Requesting user: {current_user.userid}")

            if user_id != current_user.userid:
                print(f"❌ Access denied: message belongs to user {user_id}, not {current_user.userid}")
                raise HTTPException(status_code=403, detail="Access denied")

            print(f"🗑️ DELETE STEP 4: Getting message details for audit")
            cur = execute(
                conn,
                "SELECT content, message_type, sender FROM chat_messages WHERE message_id = %s",
                (message_id,),
            )
            msg_details = cur.fetchone()
            print(f"🗑️ DELETE STEP 5: Message details retrieved: {msg_details is not None}")

            if msg_details:
                content, msg_type, sender = msg_details
                print(f"🗑️ DELETE STEP 6: Inserting audit record")
                # SAVEPOINT: if audit INSERT fails (e.g. audit_id not serial on DB), Postgres marks the
                # transaction aborted; ROLLBACK TO SAVEPOINT clears that so DELETE can still run.
                execute(conn, "SAVEPOINT sp_message_deletion_audit")
                try:
                    execute(
                        conn,
                        """
                            INSERT INTO message_deletion_audit
                            (message_id, user_id, session_id, message_content, message_type, sender)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (message_id, current_user.userid, session_id, None, msg_type, sender),
                    )
                    print(f"🗑️ DELETE STEP 7: Audit record inserted successfully")
                    execute(conn, "RELEASE SAVEPOINT sp_message_deletion_audit")
                except Exception as audit_error:
                    print(f"❌ DELETE STEP 7 ERROR: Audit insert failed: {audit_error}")
                    execute(conn, "ROLLBACK TO SAVEPOINT sp_message_deletion_audit")

            print(f"🗑️ DELETE STEP 8: Performing actual deletion")
            cur = execute(conn, "DELETE FROM chat_messages WHERE message_id = %s", (message_id,))
            deleted_rows = cur.rowcount
            print(f"🗑️ DELETE STEP 9: Deleted {deleted_rows} rows for message ID {message_id}")

            print(f"🗑️ DELETE STEP 10: Committing transaction")
            conn.commit()
            print(f"🗑️ DELETE STEP 11: Transaction committed successfully")

        print(f"🗑️ DELETE STEP 12: Database connection closed")
        
        print(f"✅ DELETE COMPLETE: Message {message_id} deleted successfully")
        return {"message": "Message deleted successfully"}
        
    except HTTPException as he:
        print(f"❌ DELETE HTTP ERROR: {he.detail}")
        raise he
    except Exception as e:
        print(f"❌ DELETE UNEXPECTED ERROR: {str(e)}")
        print(f"❌ ERROR TYPE: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/cleanup")
async def cleanup_old_chats():
    """Clean up chats older than 1 month (admin only)"""
    cutoff_date = datetime.now() - timedelta(days=30)

    with get_conn() as conn:
        # Delete old messages first (foreign key constraint)
        execute(
            conn,
            """
                DELETE FROM chat_messages
                WHERE session_id IN (
                    SELECT session_id FROM chat_sessions
                    WHERE created_at < %s
                )
            """,
            (cutoff_date,),
        )

        # Delete old sessions
        cur = execute(conn, "DELETE FROM chat_sessions WHERE created_at < %s", (cutoff_date,))
        deleted_sessions = cur.rowcount
        conn.commit()

    return {"message": f"Cleaned up {deleted_sessions} old sessions"}
