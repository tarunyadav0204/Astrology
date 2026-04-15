import re
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel
import json
from datetime import datetime
from auth import get_current_user
from db import get_conn, execute

# YYYY-MM-DD for date filters (today / this month)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _normalize_date_range(
    start_date: Optional[str], end_date: Optional[str]
) -> Tuple[Optional[str], Optional[str]]:
    """Return (start, end) as YYYY-MM-DD if both valid; else (None, None)."""
    if not start_date or not end_date:
        return None, None
    s = (start_date or "").strip()
    e = (end_date or "").strip()
    if not DATE_RE.match(s) or not DATE_RE.match(e) or s > e:
        return None, None
    return s, e


class AdminSetting(BaseModel):
    key: str
    value: str
    description: Optional[str] = None


class GlossaryTerm(BaseModel):
    term_id: str
    display_text: str
    definition: str
    language: Optional[str] = "english"
    aliases: Optional[List[str]] = None


def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


router = APIRouter()


def _timestamp_to_ist_iso(val) -> Optional[str]:
    """Convert DB timestamp (naive, stored as server local / IST) to ISO string with +05:30 so frontend displays correct IST."""
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    # Already has timezone suffix
    if "Z" in s or "+" in s or (s.count("-") >= 2 and len(s) > 19 and s[-6] in ("+", "-")):
        return s
    # Naive: treat as IST and append +05:30
    s = s.replace(" ", "T", 1)
    if len(s) >= 19:
        s = s[:19]  # YYYY-MM-DDTHH:MM:SS
    return s + "+05:30"

@router.get("/admin/chat/history/{user_id}")
async def get_user_chat_history(user_id: int, current_user: dict = Depends(require_admin)):
    """Get chat history for a specific user (admin only)"""
    try:
        with get_conn() as conn:
            cur = execute(
                conn,
                """
                SELECT session_id, created_at,
                       (SELECT content FROM chat_messages
                        WHERE session_id = cs.session_id
                        AND sender = 'user'
                        ORDER BY timestamp ASC LIMIT 1) as preview
                FROM chat_sessions cs
                WHERE user_id = %s
                ORDER BY created_at DESC
                """,
                (user_id,),
            )
            rows = cur.fetchall() or []
        sessions = []
        for row in rows:
            preview = row[2]
            preview_str = (preview[:100] + '...') if preview and len(preview) > 100 else preview
            sessions.append({
                'session_id': row[0],
                'created_at': _timestamp_to_ist_iso(row[1]),
                'preview': preview_str,
            })
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching chat history: {str(e)}")

@router.get("/admin/chat/all-history")
async def get_all_chat_history(current_user: dict = Depends(require_admin)):
    """Get chat history for all users (admin only)"""
    try:
        from encryption_utils import EncryptionManager
        enc = EncryptionManager()
        sessions = []

        with get_conn() as conn:
            cur = execute(
                conn,
                """
                SELECT cs.session_id, cs.user_id, cs.created_at, cs.birth_chart_id, u.name, u.phone,
                       bc.name as native_name_raw,
                       (SELECT content FROM chat_messages
                        WHERE session_id = cs.session_id
                        AND sender = 'user'
                        ORDER BY timestamp ASC LIMIT 1) as preview,
                       (SELECT MAX(timestamp) FROM chat_messages
                        WHERE session_id = cs.session_id) as last_activity,
                       'new' as system_type
                FROM chat_sessions cs
                LEFT JOIN users u ON cs.user_id = u.userid
                LEFT JOIN birth_charts bc ON bc.id = cs.birth_chart_id
                ORDER BY cs.created_at DESC
                LIMIT 500
                """,
                (),
            )
            for row in cur.fetchall() or []:
                native_name = None
                raw = row[6] if row[6] is not None else None
                if raw:
                    try:
                        native_name = enc.decrypt(raw)
                    except Exception:
                        native_name = raw
                display_time = row[8] if row[8] else row[2]
                preview = row[7]
                preview_str = (preview[:100] + '...') if preview and len(preview) > 100 else preview
                sessions.append({
                    'session_id': row[0],
                    'user_id': row[1],
                    'user_name': row[4] or 'Unknown User',
                    'user_phone': row[5] or 'No phone',
                    'created_at': _timestamp_to_ist_iso(display_time),
                    'preview': preview_str,
                    'system_type': row[9],
                    'native_name': native_name,
                })

            cur = execute(
                conn,
                """
                SELECT cc.birth_hash, cc.conversation_data, cc.created_at,
                       'old' as system_type
                FROM chat_conversations cc
                ORDER BY cc.created_at DESC
                LIMIT 200
                """,
                (),
            )
            for row in cur.fetchall() or []:
                try:
                    conv_data = json.loads(row[1])
                    messages = conv_data.get('messages', [])
                    birth_data = conv_data.get('birth_data', {})
                    user_name = birth_data.get('name', f'Legacy User #{row[0][:8]}')
                    if messages:
                        first_question = messages[0].get('question', 'Chat conversation')
                        sessions.append({
                            'session_id': row[0],
                            'user_id': 'legacy',
                            'user_name': user_name,
                            'user_phone': 'Legacy System',
                            'created_at': _timestamp_to_ist_iso(row[2]),
                            'preview': first_question[:100] + '...' if len(first_question) > 100 else first_question,
                            'system_type': row[3],
                        })
                except Exception:
                    pass

        sessions.sort(key=lambda x: x['created_at'], reverse=True)
        return {"sessions": sessions[:500]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching all chat history: {str(e)}")

@router.get("/admin/chat/session/{session_id}")
async def get_session_details(session_id: str, current_user: dict = Depends(require_admin)):
    """Get detailed messages for a specific session (admin only). Includes native_name (birth chart name) for the session."""
    try:
        with get_conn() as conn:
            cur = execute(
                conn,
                """
                SELECT cs.session_id, cs.user_id, cs.created_at, cs.birth_chart_id, bc.name as native_name_raw
                FROM chat_sessions cs
                LEFT JOIN birth_charts bc ON bc.id = cs.birth_chart_id
                WHERE cs.session_id = %s
                """,
                (session_id,),
            )
            session_row = cur.fetchone()

        if session_row:
            native_name = None
            raw_name = session_row[4] if session_row[4] is not None else None
            if raw_name:
                try:
                    from encryption_utils import EncryptionManager
                    enc = EncryptionManager()
                    native_name = enc.decrypt(raw_name)
                except Exception:
                    native_name = raw_name

            with get_conn() as conn:
                cur = execute(
                    conn,
                    """
                    SELECT sender, content, timestamp
                    FROM chat_messages
                    WHERE session_id = %s
                    ORDER BY timestamp ASC
                    """,
                    (session_id,),
                )
                msg_rows = cur.fetchall() or []
            messages = [
                {'sender': r[0], 'content': r[1], 'timestamp': _timestamp_to_ist_iso(r[2]), 'native_name': native_name}
                for r in msg_rows
            ]
            return {
                "session_id": session_row[0],
                "user_id": session_row[1],
                "created_at": _timestamp_to_ist_iso(session_row[2]),
                "native_name": native_name,
                "messages": messages,
            }

        with get_conn() as conn:
            cur = execute(
                conn,
                "SELECT birth_hash, conversation_data, updated_at FROM chat_conversations WHERE birth_hash = %s",
                (session_id,),
            )
            legacy_conv = cur.fetchone()

        if legacy_conv:
            try:
                conv_data = json.loads(legacy_conv[1])
                birth_data = conv_data.get('birth_data', {})
                legacy_native_name = birth_data.get('name') or None
                messages = []
                updated_at = legacy_conv[2]
                for msg in conv_data.get('messages', []):
                    ts = _timestamp_to_ist_iso(msg.get('timestamp') or updated_at)
                    if msg.get('question'):
                        messages.append({
                            'sender': 'user',
                            'content': msg['question'],
                            'timestamp': ts,
                            'native_name': legacy_native_name,
                        })
                    if msg.get('response'):
                        messages.append({
                            'sender': 'assistant',
                            'content': msg['response'],
                            'timestamp': ts,
                            'native_name': legacy_native_name,
                        })
                return {
                    "session_id": session_id,
                    "user_id": "legacy",
                    "created_at": _timestamp_to_ist_iso(updated_at),
                    "native_name": legacy_native_name,
                    "messages": messages,
                }
            except Exception:
                pass

        raise HTTPException(status_code=404, detail="Session not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching session details: {str(e)}")


@router.get("/admin/chat/analysis-stats")
async def get_chat_analysis_stats(current_user: dict = Depends(require_admin)):
    """Get category counts and FAQ (canonical_question) counts for chat analysis dashboard (admin only)."""
    try:
        with get_conn() as conn:
            # Post-migration safety: older DBs may miss these columns.
            cur = execute(
                conn,
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'chat_messages'
                """,
                (),
            )
            cols = {row[0] for row in (cur.fetchall() or [])}
            has_category = "category" in cols
            has_canonical = "canonical_question" in cols

            by_category = []
            by_faq = []

            if has_category:
                cur = execute(
                    conn,
                    """
                    SELECT category, COUNT(*) AS count
                    FROM chat_messages
                    WHERE sender = 'user' AND category IS NOT NULL AND trim(category) != ''
                    GROUP BY category
                    ORDER BY count DESC
                    """,
                    (),
                )
                by_category = [{"category": row[0], "count": row[1]} for row in (cur.fetchall() or [])]

            if has_canonical:
                cur = execute(
                    conn,
                    """
                    SELECT canonical_question, COUNT(*) AS count
                    FROM chat_messages
                    WHERE sender = 'user' AND canonical_question IS NOT NULL AND trim(canonical_question) != ''
                    GROUP BY canonical_question
                    ORDER BY count DESC
                    """,
                    (),
                )
                by_faq = [{"canonical_question": row[0], "count": row[1]} for row in (cur.fetchall() or [])]
        return {"by_category": by_category, "by_faq": by_faq}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching chat analysis stats: {str(e)}")


@router.get("/admin/settings")
async def get_all_settings(current_user: dict = Depends(require_admin)):
    """Get all admin settings plus Gemini model options and current model IDs."""
    try:
        from utils.admin_settings import (
            _ensure_admin_settings_table,
            GEMINI_MODEL_OPTIONS,
            OPENAI_CHAT_MODEL_OPTIONS,
            get_gemini_chat_model,
            get_gemini_premium_model,
            get_gemini_analysis_model,
            get_podcast_provider,
            get_chat_llm_provider,
            get_openai_chat_model,
            get_openai_premium_model,
        )
        with get_conn() as conn:
            _ensure_admin_settings_table(conn)
            cur = execute(conn, "SELECT key, value, description FROM admin_settings", ())
            settings = [{"key": row[0], "value": row[1], "description": row[2]} for row in (cur.fetchall() or [])]
        return {
            "settings": settings,
            "gemini_model_options": [{"value": v, "label": l} for v, l in GEMINI_MODEL_OPTIONS],
            "openai_model_options": [{"value": v, "label": l} for v, l in OPENAI_CHAT_MODEL_OPTIONS],
            "gemini_chat_model": get_gemini_chat_model(),
            "gemini_premium_model": get_gemini_premium_model(),
            "gemini_analysis_model": get_gemini_analysis_model(),
            "chat_llm_provider": get_chat_llm_provider(),
            "openai_chat_model": get_openai_chat_model(),
            "openai_premium_model": get_openai_premium_model(),
            "podcast_provider": get_podcast_provider(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching settings: {str(e)}")


@router.get("/admin/terms")
async def get_glossary_terms(
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    current_user: dict = Depends(require_admin),
):
    """Get glossary terms (for chat glossary) with optional search and pagination."""
    try:
        where_clause = ""
        params: List[Any] = []
        if search:
            where_clause = "WHERE term_id LIKE %s OR display_text LIKE %s"
            like = f"%{search}%"
            params = [like, like]

        with get_conn() as conn:
            cur = execute(
                conn,
                f"SELECT COUNT(*) AS total FROM glossary_terms {where_clause}",
                tuple(params),
            )
            total = (cur.fetchone() or [0])[0]

            offset = (page - 1) * limit
            cur = execute(
                conn,
                f"""
                SELECT term_id, display_text, definition, language, COALESCE(aliases, '[]') AS aliases_json
                FROM glossary_terms
                {where_clause}
                ORDER BY term_id ASC
                LIMIT %s OFFSET %s
                """,
                tuple(params) + (limit, offset),
            )
            rows = cur.fetchall() or []

        terms: List[Dict[str, Any]] = []
        for row in rows:
            try:
                aliases = json.loads(row[4]) if row[4] else []
                if not isinstance(aliases, list):
                    aliases = []
            except Exception:
                aliases = []
            terms.append({
                "term_id": row[0],
                "display_text": row[1],
                "definition": row[2],
                "language": row[3],
                "aliases": aliases,
            })

        return {
            "terms": terms,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "has_more": offset + limit < total,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching terms: {str(e)}")


@router.post("/admin/terms")
async def create_glossary_term(
    term: GlossaryTerm, current_user: dict = Depends(require_admin)
):
    """Create or overwrite a glossary term."""
    try:
        aliases_json = json.dumps(term.aliases or [])
        with get_conn() as conn:
            execute(
                conn,
                """
                INSERT INTO glossary_terms (term_id, display_text, definition, language, aliases)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (term_id) DO UPDATE SET
                    display_text = EXCLUDED.display_text,
                    definition = EXCLUDED.definition,
                    language = EXCLUDED.language,
                    aliases = EXCLUDED.aliases
                """,
                (
                    term.term_id.strip(),
                    term.display_text.strip(),
                    term.definition.strip(),
                    term.language or "english",
                    aliases_json,
                ),
            )
        return {"message": "Term saved", "term_id": term.term_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving term: {str(e)}")


@router.put("/admin/terms/{term_id}")
async def update_glossary_term(
    term_id: str, term: GlossaryTerm, current_user: dict = Depends(require_admin)
):
    """Update an existing glossary term."""
    try:
        aliases_json = json.dumps(term.aliases or [])
        with get_conn() as conn:
            cur = execute(
                conn,
                """
                UPDATE glossary_terms
                SET display_text = %s, definition = %s, language = %s, aliases = %s
                WHERE term_id = %s
                """,
                (
                    term.display_text.strip(),
                    term.definition.strip(),
                    term.language or "english",
                    aliases_json,
                    term_id,
                ),
            )
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Term not found")
            conn.commit()
        return {"message": "Term updated", "term_id": term_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating term: {str(e)}")


@router.delete("/admin/terms/{term_id}")
async def delete_glossary_term(
    term_id: str, current_user: dict = Depends(require_admin)
):
    """Delete a glossary term."""
    try:
        with get_conn() as conn:
            cur = execute(conn, "DELETE FROM glossary_terms WHERE term_id = %s", (term_id,))
            deleted = cur.rowcount
            conn.commit()
        if deleted == 0:
            raise HTTPException(status_code=404, detail="Term not found")
        return {"message": "Term deleted", "term_id": term_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting term: {str(e)}")

@router.put("/admin/settings/{key}")
async def update_setting(key: str, setting: AdminSetting, current_user: dict = Depends(require_admin)):
    """Update admin setting"""
    try:
        from utils.admin_settings import _ensure_admin_settings_table
        with get_conn() as conn:
            _ensure_admin_settings_table(conn)
            execute(
                conn,
                """
                INSERT INTO admin_settings (key, value, description, updated_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT ("key") DO UPDATE SET
                    value = EXCLUDED.value,
                    description = EXCLUDED.description,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (key, setting.value, setting.description),
            )
            conn.commit()
        return {"message": "Setting updated", "key": key, "value": setting.value}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating setting: {str(e)}")

@router.get("/admin/facts")
async def get_all_user_facts(
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    current_user: dict = Depends(require_admin)
):
    """Get all facts in flat table format"""
    try:
        from encryption_utils import EncryptionManager
        encryption = EncryptionManager()

        where_clause = ""
        params: List[Any] = []
        if search:
            # Postgres: ILIKE is case-insensitive (LIKE alone is case-sensitive and often fails username search).
            # Match account name, phone, email, chart name (may be ciphertext), and stored fact text.
            pat = f"%{search}%"
            where_clause = (
                " WHERE (u.name ILIKE %s OR u.phone ILIKE %s OR COALESCE(u.email, '') ILIKE %s "
                "OR bc.name ILIKE %s OR uf.fact ILIKE %s)"
            )
            params = [pat, pat, pat, pat, pat]

        with get_conn() as conn:
            cur = execute(
                conn,
                f"""
                SELECT COUNT(*) as total
                FROM user_facts uf
                INNER JOIN birth_charts bc ON bc.id = uf.birth_chart_id
                INNER JOIN users u ON u.userid = bc.userid
                {where_clause}
                """,
                tuple(params),
            )
            total = (cur.fetchone() or [0])[0]

            offset = (page - 1) * limit
            cur = execute(
                conn,
                f"""
                SELECT
                    u.userid, COALESCE(u.name, u.phone) as username, u.phone,
                    bc.id as birth_chart_id, bc.name as native_name,
                    uf.category, uf.fact, uf.extracted_at
                FROM user_facts uf
                INNER JOIN birth_charts bc ON bc.id = uf.birth_chart_id
                INNER JOIN users u ON u.userid = bc.userid
                {where_clause}
                ORDER BY u.name, bc.id, uf.category, uf.extracted_at DESC
                LIMIT %s OFFSET %s
                """,
                tuple(params) + (limit, offset),
            )
            rows = cur.fetchall() or []

        facts = []
        for row in rows:
            native_name = row[4]
            try:
                native_name = encryption.decrypt(native_name)
            except Exception:
                pass
            facts.append({
                'user_id': row[0],
                'username': row[1],
                'phone': row[2],
                'birth_chart_id': row[3],
                'native_name': native_name,
                'category': row[5],
                'fact': row[6],
                'extracted_at': row[7],
            })

        total_pages = max(1, (total + limit - 1) // limit) if total else 1
        return {
            'success': True,
            'facts': facts,
            'page': page,
            'limit': limit,
            'total': total,
            'total_pages': total_pages,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching facts: {str(e)}")


# Duration bucket keys and (min_sec, max_sec) for list filter. max_sec None = no upper bound.
DURATION_BUCKETS_LIST = [
    ("<30s", 0, 30),
    ("30-60s", 30, 60),
    ("60-90s", 60, 90),
    ("90-120s", 90, 120),
    ("2-3min", 120, 180),
    ("3-4min", 180, 240),
    ("4-5min", 240, 300),
    (">5min", 300, None),
]


@router.get("/admin/chat-performance")
async def get_chat_performance(
    page: int = 1,
    per_page: int = 20,
    duration_bucket: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(require_admin)
):
    """Paginated chat performance. Optional duration_bucket and start_date/end_date (YYYY-MM-DD) to filter by completed_at."""
    if per_page < 1 or per_page > 100:
        per_page = 20
    if page < 1:
        page = 1
    offset = (page - 1) * per_page
    duration_filter = None
    if duration_bucket and duration_bucket != "all":
        for key, lo, hi in DURATION_BUCKETS_LIST:
            if key == duration_bucket:
                duration_filter = (lo, hi)
                break
    try:
        from encryption_utils import EncryptionManager
        try:
            encryption = EncryptionManager()
        except Exception:
            encryption = None

        base_where = """
            cm.sender = 'assistant' AND cm.status = 'completed'
            AND (cm.message_type = 'answer' OR (cm.content IS NOT NULL AND cm.content != ''))
        """
        duration_where = ""
        count_params: List[Any] = []
        if duration_filter:
            lo, hi = duration_filter
            duration_where = " AND cm.started_at IS NOT NULL AND cm.completed_at IS NOT NULL"
            duration_where += " AND EXTRACT(EPOCH FROM (cm.completed_at::timestamp - cm.started_at::timestamp)) >= %s"
            count_params.append(lo)
            if hi is not None:
                duration_where += " AND EXTRACT(EPOCH FROM (cm.completed_at::timestamp - cm.started_at::timestamp)) < %s"
                count_params.append(hi)
        date_where = ""
        sdate, edate = _normalize_date_range(start_date, end_date)
        if sdate and edate:
            date_where = " AND cm.completed_at IS NOT NULL AND cm.completed_at::date >= %s AND cm.completed_at::date <= %s"
            count_params.extend([sdate, edate])

        with get_conn() as conn:
            cur = execute(
                conn,
                f"""
                SELECT COUNT(*) FROM chat_messages cm
                WHERE {base_where}{duration_where}{date_where}
                """,
                tuple(count_params),
            )
            total = (cur.fetchone() or [0])[0]

            # Optional columns: check Postgres information_schema
            cur = execute(
                conn,
                "SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'chat_messages'",
                (),
            )
            cols = [r[0] for r in (cur.fetchall() or [])]
            has_language = 'language' in cols
            has_intent_ms = 'intent_router_ms' in cols

            sel = """
                SELECT cm.message_id, cm.content, cm.started_at, cm.completed_at,
                       cs.session_id, u.name as user_name, u.phone as user_phone,
                       bc.name as native_name,
                       (SELECT content FROM chat_messages m2
                        WHERE m2.session_id = cm.session_id AND m2.sender = 'user' AND m2.message_id < cm.message_id
                        ORDER BY m2.message_id DESC LIMIT 1) as user_question
            """
            if has_language:
                sel += ", cm.language"
            if has_intent_ms:
                sel += ", cm.intent_router_ms"
            sel += f"""
                FROM chat_messages cm
                JOIN chat_sessions cs ON cs.session_id = cm.session_id
                LEFT JOIN users u ON u.userid = cs.user_id
                LEFT JOIN birth_charts bc ON bc.id = cs.birth_chart_id
                WHERE {base_where}{duration_where}{date_where}
                ORDER BY cm.message_id DESC
                LIMIT %s OFFSET %s
            """
            cur = execute(conn, sel, tuple(count_params) + (per_page, offset))
            rows = cur.fetchall() or []
            colnames = [d[0] for d in cur.description] if cur.description else []

        items = []
        for row in rows:
            row_dict = dict(zip(colnames, row)) if colnames else {}
            content = row_dict.get('content') or ''
            preview = content[:300].strip() + ('…' if len(content) > 300 else '')
            user_question = row_dict.get('user_question') or ''
            uq_preview = user_question[:150].strip() + ('…' if len(user_question) > 150 else '')
            started = row_dict.get('started_at')
            completed = row_dict.get('completed_at')
            duration_seconds = None
            if started and completed:
                try:
                    s = datetime.fromisoformat(started.replace('Z', '+00:00')) if isinstance(started, str) else started
                    c = datetime.fromisoformat(completed.replace('Z', '+00:00')) if isinstance(completed, str) else completed
                    duration_seconds = round((c - s).total_seconds(), 2)
                except Exception:
                    pass
            raw_native = row_dict.get('native_name')
            if raw_native and encryption:
                try:
                    native_name = encryption.decrypt(raw_native)
                except Exception:
                    native_name = raw_native
            else:
                native_name = raw_native or '—'
            items.append({
                'message_id': row_dict.get('message_id'),
                'user_name': row_dict.get('user_name') or '—',
                'user_phone': row_dict.get('user_phone') or '—',
                'user_question': uq_preview,
                'response_preview': preview,
                'native_name': native_name,
                'intent_router_ms': row_dict.get('intent_router_ms') if has_intent_ms else None,
                'duration_seconds': duration_seconds,
                'completed_at': row_dict.get('completed_at'),
            })
        return {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page if per_page else 0,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching chat performance: {str(e)}")


# Duration buckets for charts: (label, min_seconds, max_seconds). max_seconds None = no upper bound.
DURATION_BUCKETS = [
    ("<30s", 0, 30),
    ("30-60s", 30, 60),
    ("60-90s", 60, 90),
    ("90-120s", 90, 120),
    ("2-3 min", 120, 180),
    ("3-4 min", 180, 240),
    ("4-5 min", 240, 300),
    (">5 min", 300, None),
]


@router.get("/admin/chat-performance/stats")
async def get_chat_performance_stats(
    limit: int = 5000,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(require_admin)
):
    """Aggregated duration bucket counts (overall and by user) for Charts tab. Optional start_date/end_date (YYYY-MM-DD)."""
    if limit < 1 or limit > 20000:
        limit = 5000
    try:
        date_where = ""
        params: List[Any] = [limit]
        sdate, edate = _normalize_date_range(start_date, end_date)
        if sdate and edate:
            date_where = " AND cm.completed_at IS NOT NULL AND cm.completed_at::date >= %s AND cm.completed_at::date <= %s"
            params = [sdate, edate, limit]
        with get_conn() as conn:
            cur = execute(
                conn,
                f"""
                SELECT cm.message_id, cm.started_at, cm.completed_at,
                       COALESCE(u.name, u.phone, 'Unknown') as user_name, u.phone as user_phone
                FROM chat_messages cm
                JOIN chat_sessions cs ON cs.session_id = cm.session_id
                LEFT JOIN users u ON u.userid = cs.user_id
                WHERE cm.sender = 'assistant' AND cm.status = 'completed'
                AND (cm.message_type = 'answer' OR (cm.content IS NOT NULL AND cm.content != ''))
                AND cm.started_at IS NOT NULL AND cm.completed_at IS NOT NULL
                {date_where}
                ORDER BY cm.message_id DESC
                LIMIT %s
                """,
                tuple(params),
            )
            rows = cur.fetchall() or []
            colnames = [d[0] for d in cur.description] if cur.description else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")

    def duration_seconds(started, completed):
        if not started or not completed:
            return None
        try:
            s = datetime.fromisoformat(str(started).replace("Z", "+00:00"))
            c = datetime.fromisoformat(str(completed).replace("Z", "+00:00"))
            return (c - s).total_seconds()
        except Exception:
            return None

    def bucket_for(sec):
        if sec is None:
            return None
        for label, lo, hi in DURATION_BUCKETS:
            if hi is None:
                if sec >= lo:
                    return label
            elif lo <= sec < hi:
                return label
        return None

    bucket_counts = {label: 0 for label, _, _ in DURATION_BUCKETS}
    user_buckets = {}

    for row in rows:
        r = dict(zip(colnames, row)) if colnames else {}
        sec = duration_seconds(r.get("started_at"), r.get("completed_at"))
        b = bucket_for(sec)
        if b is None:
            continue
        bucket_counts[b] = bucket_counts.get(b, 0) + 1
        user_key = (r.get("user_name") or "Unknown", r.get("user_phone") or "")
        if user_key not in user_buckets:
            user_buckets[user_key] = {label: 0 for label, _, _ in DURATION_BUCKETS}
        user_buckets[user_key][b] = user_buckets[user_key].get(b, 0) + 1

    buckets = [{"name": label, "count": bucket_counts[label]} for label, _, _ in DURATION_BUCKETS]
    by_user = []
    for (uname, uphone), counts in user_buckets.items():
        by_user.append({
            "user_name": uname,
            "user_phone": uphone or "",
            "buckets": [{"name": label, "count": counts.get(label, 0)} for label, _, _ in DURATION_BUCKETS],
        })

    SLOW_THRESHOLD_SEC = 120
    hour_labels = [
        "12am", "1am", "2am", "3am", "4am", "5am", "6am", "7am", "8am", "9am", "10am", "11am",
        "12pm", "1pm", "2pm", "3pm", "4pm", "5pm", "6pm", "7pm", "8pm", "9pm", "10pm", "11pm",
    ]
    slow_by_hour = {h: 0 for h in range(24)}
    for row in rows:
        r = dict(zip(colnames, row)) if colnames else {}
        sec = duration_seconds(r.get("started_at"), r.get("completed_at"))
        if sec is None or sec < SLOW_THRESHOLD_SEC:
            continue
        completed = r.get("completed_at")
        if not completed:
            continue
        try:
            if isinstance(completed, str):
                dt = datetime.fromisoformat(completed.replace("Z", "+00:00"))
            else:
                dt = completed
            hour = dt.hour
            slow_by_hour[hour] = slow_by_hour.get(hour, 0) + 1
        except Exception:
            pass
    slow_by_hour_list = [
        {"hour": h, "hour_label": hour_labels[h], "count": slow_by_hour[h]}
        for h in range(24)
    ]

    return {"buckets": buckets, "by_user": by_user, "slow_by_hour": slow_by_hour_list}