from fastapi import APIRouter, Depends, HTTPException, Query
from auth import get_current_user
from db import get_conn, execute
from encryption_utils import EncryptionManager

router = APIRouter(prefix='/chat/bookmarks', tags=['chat_bookmarks'])


def ensure_table(conn):
    execute(conn, '''CREATE TABLE IF NOT EXISTS chat_answer_bookmarks (
        user_id INTEGER NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
        message_id INTEGER NOT NULL REFERENCES chat_messages(message_id) ON DELETE CASCADE,
        saved_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, message_id)
    )''', ())


def require_answer(conn, message_id, user_id):
    row = execute(conn, '''SELECT cm.message_id FROM chat_messages cm
        JOIN chat_sessions cs ON cs.session_id = cm.session_id
        WHERE cm.message_id = %s AND cs.user_id = %s AND cm.sender = 'assistant'
        AND COALESCE(cm.status, 'completed') = 'completed'
        AND COALESCE(cm.message_type, 'answer') = 'answer'
        AND LENGTH(TRIM(COALESCE(cm.content, ''))) > 0''', (message_id, user_id)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail='Answer not found')


@router.get('')
async def list_bookmarks(q: str = Query('', max_length=200), page: int = Query(1, ge=1), limit: int = Query(30, ge=1, le=100), current_user=Depends(get_current_user)):
    with get_conn() as conn:
        ensure_table(conn)
        rows = execute(conn, '''SELECT cm.message_id, cm.content, b.saved_at,
            COALESCE(question.content, ''), COALESCE(bc.name, ''), cm.session_id
            FROM chat_answer_bookmarks b
            JOIN chat_messages cm ON cm.message_id = b.message_id
            JOIN chat_sessions cs ON cs.session_id = cm.session_id AND cs.user_id = b.user_id
            LEFT JOIN birth_charts bc ON bc.id = cs.birth_chart_id
            LEFT JOIN LATERAL (SELECT content FROM chat_messages prev
              WHERE prev.session_id = cm.session_id AND prev.sender = 'user' AND prev.message_id < cm.message_id
              ORDER BY prev.message_id DESC LIMIT 1) question ON TRUE
            WHERE b.user_id = %s
            ORDER BY b.saved_at DESC, b.message_id DESC''',
            (current_user.userid,)).fetchall()
        conn.commit()
    encryptor = EncryptionManager()
    answers = []
    query = q.strip().casefold()
    for row in rows:
        raw_name = row[4] or ''
        try:
            name = encryptor.decrypt(raw_name) if raw_name else ''
        except Exception:
            # Never expose encrypted PII if a record cannot be decrypted.
            name = '' if raw_name.startswith('gAAAA') else raw_name
        answer = dict(message_id=row[0], content=row[1], saved_at=row[2], question=row[3], name=name, session_id=row[5])
        if not query or any(query in str(value or '').casefold() for value in (answer['content'], answer['question'], name)):
            answers.append(answer)
    offset = (page - 1) * limit
    return {'answers': answers[offset:offset + limit], 'has_more': len(answers) > offset + limit}



@router.get('/{message_id}')
async def bookmark_status(message_id: int, current_user=Depends(get_current_user)):
    with get_conn() as conn:
        ensure_table(conn)
        require_answer(conn, message_id, current_user.userid)
        saved = bool(execute(conn, 'SELECT 1 FROM chat_answer_bookmarks WHERE user_id = %s AND message_id = %s', (current_user.userid, message_id)).fetchone())
        conn.commit()
    return {'saved': saved}


@router.put('/{message_id}')
async def save_answer(message_id: int, current_user=Depends(get_current_user)):
    with get_conn() as conn:
        ensure_table(conn)
        require_answer(conn, message_id, current_user.userid)
        execute(conn, 'INSERT INTO chat_answer_bookmarks (user_id, message_id) VALUES (%s, %s) ON CONFLICT DO NOTHING', (current_user.userid, message_id))
        conn.commit()
    return {'saved': True}


@router.delete('/{message_id}')
async def remove_answer(message_id: int, current_user=Depends(get_current_user)):
    with get_conn() as conn:
        ensure_table(conn)
        execute(conn, 'DELETE FROM chat_answer_bookmarks WHERE user_id = %s AND message_id = %s', (current_user.userid, message_id))
        conn.commit()
    return {'saved': False}
