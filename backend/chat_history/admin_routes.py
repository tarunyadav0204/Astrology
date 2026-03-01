from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import sqlite3
import json
from datetime import datetime
from auth import get_current_user


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


def get_db_connection():
    conn = sqlite3.connect('astrology.db')
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/admin/chat/history/{user_id}")
async def get_user_chat_history(user_id: int, current_user: dict = Depends(require_admin)):
    """Get chat history for a specific user (admin only)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all sessions for the user
        cursor.execute("""
            SELECT session_id, created_at, 
                   (SELECT content FROM chat_messages 
                    WHERE session_id = cs.session_id 
                    AND sender = 'user' 
                    ORDER BY timestamp ASC LIMIT 1) as preview
            FROM chat_sessions cs
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,))
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                'session_id': row['session_id'],
                'created_at': row['created_at'],
                'preview': row['preview'][:100] + '...' if row['preview'] and len(row['preview']) > 100 else row['preview']
            })
        
        conn.close()
        return {"sessions": sessions}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching chat history: {str(e)}")

@router.get("/admin/chat/all-history")
async def get_all_chat_history(current_user: dict = Depends(require_admin)):
    """Get chat history for all users (admin only)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get new system sessions with last activity time and birth chart name
        cursor.execute("""
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
        """)
        
        from encryption_utils import EncryptionManager
        enc = EncryptionManager()
        sessions = []
        for row in cursor.fetchall():
            native_name = None
            raw = row['native_name_raw'] if row['native_name_raw'] is not None else None
            if raw:
                try:
                    native_name = enc.decrypt(raw)
                except Exception:
                    native_name = raw
            display_time = row['last_activity'] if row['last_activity'] else row['created_at']
            sessions.append({
                'session_id': row['session_id'],
                'user_id': row['user_id'],
                'user_name': row['name'] or 'Unknown User',
                'user_phone': row['phone'] or 'No phone',
                'created_at': display_time,
                'preview': row['preview'][:100] + '...' if row['preview'] and len(row['preview']) > 100 else row['preview'],
                'system_type': row['system_type'],
                'native_name': native_name
            })
        
        # Get old system conversations with created_at instead of updated_at
        cursor.execute("""
            SELECT cc.birth_hash, cc.conversation_data, cc.created_at,
                   'old' as system_type
            FROM chat_conversations cc
            ORDER BY cc.created_at DESC
            LIMIT 200
        """)
        
        for row in cursor.fetchall():
            try:
                conv_data = json.loads(row['conversation_data'])
                messages = conv_data.get('messages', [])
                birth_data = conv_data.get('birth_data', {})
                
                # Get name from birth data
                user_name = birth_data.get('name', f'Legacy User #{row["birth_hash"][:8]}')
                
                if messages:
                    first_question = messages[0].get('question', 'Chat conversation')
                    sessions.append({
                        'session_id': row['birth_hash'],
                        'user_id': 'legacy',
                        'user_name': user_name,
                        'user_phone': 'Legacy System',
                        'created_at': row['created_at'],
                        'preview': first_question[:100] + '...' if len(first_question) > 100 else first_question,
                        'system_type': row['system_type']
                    })
            except:
                pass
        
        # Sort all sessions by date
        sessions.sort(key=lambda x: x['created_at'], reverse=True)
        
        conn.close()
        return {"sessions": sessions[:500]}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching all chat history: {str(e)}")

@router.get("/admin/chat/session/{session_id}")
async def get_session_details(session_id: str, current_user: dict = Depends(require_admin)):
    """Get detailed messages for a specific session (admin only). Includes native_name (birth chart name) for the session."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First try new system: get session and join birth_charts for native_name
        cursor.execute("""
            SELECT cs.session_id, cs.user_id, cs.created_at, cs.birth_chart_id, bc.name as native_name_raw
            FROM chat_sessions cs
            LEFT JOIN birth_charts bc ON bc.id = cs.birth_chart_id
            WHERE cs.session_id = ?
        """, (session_id,))
        session_row = cursor.fetchone()
        
        if session_row:
            native_name = None
            raw_name = session_row['native_name_raw'] if session_row['native_name_raw'] is not None else None
            if raw_name:
                try:
                    from encryption_utils import EncryptionManager
                    enc = EncryptionManager()
                    native_name = enc.decrypt(raw_name)
                except Exception:
                    native_name = raw_name
            
            cursor.execute("""
                SELECT sender, content, timestamp 
                FROM chat_messages 
                WHERE session_id = ? 
                ORDER BY timestamp ASC
            """, (session_id,))
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'sender': row['sender'],
                    'content': row['content'],
                    'timestamp': row['timestamp'],
                    'native_name': native_name
                })
            
            conn.close()
            return {
                "session_id": session_row['session_id'],
                "user_id": session_row['user_id'],
                "created_at": session_row['created_at'],
                "native_name": native_name,
                "messages": messages
            }
        
        # Try legacy system
        cursor.execute("SELECT * FROM chat_conversations WHERE birth_hash = ?", (session_id,))
        legacy_conv = cursor.fetchone()
        
        if legacy_conv:
            try:
                conv_data = json.loads(legacy_conv['conversation_data'])
                birth_data = conv_data.get('birth_data', {})
                legacy_native_name = birth_data.get('name') or None
                messages = []
                
                for msg in conv_data.get('messages', []):
                    if msg.get('question'):
                        messages.append({
                            'sender': 'user',
                            'content': msg['question'],
                            'timestamp': msg.get('timestamp', legacy_conv['updated_at']),
                            'native_name': legacy_native_name
                        })
                    
                    if msg.get('response'):
                        messages.append({
                            'sender': 'assistant',
                            'content': msg['response'],
                            'timestamp': msg.get('timestamp', legacy_conv['updated_at']),
                            'native_name': legacy_native_name
                        })
                
                conn.close()
                return {
                    "session_id": session_id,
                    "user_id": "legacy",
                    "created_at": legacy_conv['updated_at'],
                    "native_name": legacy_native_name,
                    "messages": messages
                }
            except Exception:
                pass
        
        conn.close()
        raise HTTPException(status_code=404, detail="Session not found")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching session details: {str(e)}")


@router.get("/admin/chat/analysis-stats")
async def get_chat_analysis_stats(current_user: dict = Depends(require_admin)):
    """Get category counts and FAQ (canonical_question) counts for chat analysis dashboard (admin only)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT category, COUNT(*) AS count
            FROM chat_messages
            WHERE sender = 'user' AND category IS NOT NULL AND trim(category) != ''
            GROUP BY category
            ORDER BY count DESC
        """)
        by_category = [{"category": row["category"], "count": row["count"]} for row in cursor.fetchall()]
        cursor.execute("""
            SELECT canonical_question, COUNT(*) AS count
            FROM chat_messages
            WHERE sender = 'user' AND canonical_question IS NOT NULL AND trim(canonical_question) != ''
            GROUP BY canonical_question
            ORDER BY count DESC
        """)
        by_faq = [{"canonical_question": row["canonical_question"], "count": row["count"]} for row in cursor.fetchall()]
        conn.close()
        return {"by_category": by_category, "by_faq": by_faq}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching chat analysis stats: {str(e)}")


@router.get("/admin/settings")
async def get_all_settings(current_user: dict = Depends(require_admin)):
    """Get all admin settings"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT key, value, description FROM admin_settings")
        settings = [{"key": row["key"], "value": row["value"], "description": row["description"]} for row in cursor.fetchall()]
        conn.close()
        return {"settings": settings}
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
        conn = get_db_connection()
        cursor = conn.cursor()

        where_clause = ""
        params: List[Any] = []
        if search:
            where_clause = "WHERE term_id LIKE ? OR display_text LIKE ?"
            like = f"%{search}%"
            params.extend([like, like])

        # Total count
        cursor.execute(
            f"SELECT COUNT(*) AS total FROM glossary_terms {where_clause}",
            params,
        )
        total = cursor.fetchone()["total"]

        offset = (page - 1) * limit
        cursor.execute(
            f"""
            SELECT term_id, display_text, definition, language, COALESCE(aliases, '[]') AS aliases_json
            FROM glossary_terms
            {where_clause}
            ORDER BY term_id ASC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        )

        rows = cursor.fetchall()
        conn.close()

        terms: List[Dict[str, Any]] = []
        for row in rows:
            try:
                aliases = json.loads(row["aliases_json"]) if row["aliases_json"] else []
                if not isinstance(aliases, list):
                    aliases = []
            except Exception:
                aliases = []
            terms.append(
                {
                    "term_id": row["term_id"],
                    "display_text": row["display_text"],
                    "definition": row["definition"],
                    "language": row["language"],
                    "aliases": aliases,
                }
            )

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
        conn = get_db_connection()
        cursor = conn.cursor()
        aliases_json = json.dumps(term.aliases or [])
        cursor.execute(
            """
            INSERT OR REPLACE INTO glossary_terms (term_id, display_text, definition, language, aliases)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                term.term_id.strip(),
                term.display_text.strip(),
                term.definition.strip(),
                term.language or "english",
                aliases_json,
            ),
        )
        conn.commit()
        conn.close()
        return {"message": "Term saved", "term_id": term.term_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving term: {str(e)}")


@router.put("/admin/terms/{term_id}")
async def update_glossary_term(
    term_id: str, term: GlossaryTerm, current_user: dict = Depends(require_admin)
):
    """Update an existing glossary term."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        aliases_json = json.dumps(term.aliases or [])
        cursor.execute(
            """
            UPDATE glossary_terms
            SET display_text = ?, definition = ?, language = ?, aliases = ?
            WHERE term_id = ?
            """,
            (
                term.display_text.strip(),
                term.definition.strip(),
                term.language or "english",
                aliases_json,
                term_id,
            ),
        )
        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Term not found")
        conn.commit()
        conn.close()
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
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM glossary_terms WHERE term_id = ?", (term_id,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
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
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO admin_settings (key, value, description, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
            (key, setting.value, setting.description)
        )
        conn.commit()
        conn.close()
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
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build WHERE clause
        where_clause = ""
        params = []
        if search:
            where_clause = " WHERE (u.name LIKE ? OR u.phone LIKE ? OR bc.name LIKE ?)"
            params = [f"%{search}%", f"%{search}%", f"%{search}%"]
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*) as total
            FROM user_facts uf
            INNER JOIN birth_charts bc ON bc.id = uf.birth_chart_id
            INNER JOIN users u ON u.userid = bc.userid
            {where_clause}
        """
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        # Get facts with user and birth chart info
        query = f"""
            SELECT 
                u.userid, COALESCE(u.name, u.phone) as username, u.phone,
                bc.id as birth_chart_id, bc.name as native_name,
                uf.category, uf.fact, uf.extracted_at
            FROM user_facts uf
            INNER JOIN birth_charts bc ON bc.id = uf.birth_chart_id
            INNER JOIN users u ON u.userid = bc.userid
            {where_clause}
            ORDER BY u.name, bc.id, uf.category, uf.extracted_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, (page - 1) * limit])
        
        cursor.execute(query, params)
        facts = []
        for row in cursor.fetchall():
            facts.append({
                'user_id': row['userid'],
                'username': row['username'],
                'phone': row['phone'],
                'birth_chart_id': row['birth_chart_id'],
                'native_name': encryption.decrypt(row['native_name']),
                'category': row['category'],
                'fact': row['fact'],
                'extracted_at': row['extracted_at']
            })
        
        conn.close()
        
        return {
            'success': True,
            'facts': facts,
            'page': page,
            'limit': limit,
            'total': total,
            'total_pages': (total + limit - 1) // limit
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
        conn = get_db_connection()
        cursor = conn.cursor()
        base_where = """
            cm.sender = 'assistant' AND cm.status = 'completed'
            AND (cm.message_type = 'answer' OR (cm.content IS NOT NULL AND cm.content != ''))
        """
        duration_where = ""
        count_params = []
        if duration_filter:
            lo, hi = duration_filter
            duration_where = " AND cm.started_at IS NOT NULL AND cm.completed_at IS NOT NULL"
            duration_where += " AND (julianday(cm.completed_at) - julianday(cm.started_at)) * 86400 >= ?"
            count_params.append(lo)
            if hi is not None:
                duration_where += " AND (julianday(cm.completed_at) - julianday(cm.started_at)) * 86400 < ?"
                count_params.append(hi)
        date_where = ""
        if start_date and end_date:
            date_where = " AND date(cm.completed_at) >= date(?) AND date(cm.completed_at) <= date(?)"
            count_params.extend([start_date, end_date])
        cursor.execute(f"""
            SELECT COUNT(*) FROM chat_messages cm
            WHERE {base_where}{duration_where}{date_where}
        """, count_params)
        total = cursor.fetchone()[0]
        # Optional columns language, intent_router_ms may not exist on older DBs
        try:
            cursor.execute("PRAGMA table_info(chat_messages)")
            cols = [r[1] for r in cursor.fetchall()]
            has_language = 'language' in cols
            has_intent_ms = 'intent_router_ms' in cols
        except Exception:
            has_language = has_intent_ms = False
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
            LIMIT ? OFFSET ?
        """
        cursor.execute(sel, count_params + [per_page, offset])
        rows = cursor.fetchall()
        items = []
        for row in rows:
            row_dict = dict(row)
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
                'message_id': row_dict['message_id'],
                'user_name': row_dict.get('user_name') or '—',
                'user_phone': row_dict.get('user_phone') or '—',
                'user_question': uq_preview,
                'response_preview': preview,
                'native_name': native_name,
                'intent_router_ms': row_dict.get('intent_router_ms') if has_intent_ms else None,
                'duration_seconds': duration_seconds,
                'completed_at': row_dict.get('completed_at'),
            })
        conn.close()
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
        conn = get_db_connection()
        cursor = conn.cursor()
        date_where = ""
        params = [limit]
        if start_date and end_date:
            date_where = " AND date(cm.completed_at) >= date(?) AND date(cm.completed_at) <= date(?)"
            params = [start_date, end_date, limit]
        cursor.execute(f"""
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
            LIMIT ?
        """, params)
        rows = cursor.fetchall()
        conn.close()
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

    # Overall counts per bucket
    bucket_counts = {label: 0 for label, _, _ in DURATION_BUCKETS}
    # By user: { user_key: { bucket: count } }
    user_buckets = {}

    for row in rows:
        r = dict(row)
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

    # Slow responses (>2 min) by hour of day (when completed_at occurred)
    SLOW_THRESHOLD_SEC = 120
    hour_labels = [
        "12am", "1am", "2am", "3am", "4am", "5am", "6am", "7am", "8am", "9am", "10am", "11am",
        "12pm", "1pm", "2pm", "3pm", "4pm", "5pm", "6pm", "7pm", "8pm", "9pm", "10pm", "11pm",
    ]
    slow_by_hour = {h: 0 for h in range(24)}
    for row in rows:
        r = dict(row)
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