"""Read-only, paginated admin queue for calculator audit findings."""
from datetime import datetime, time, timedelta, timezone
import re
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from db import execute

VIEWS = ('mismatches', 'unverified', 'failures')
CHAT_TYPES = ('standard', 'premium', 'instant', 'speech', 'verified')


def query_filters(view, username, start_date, end_date, chat_type):
    if view not in VIEWS or (chat_type and chat_type not in CHAT_TYPES):
        raise HTTPException(422, 'Invalid evidence view or chat type.')
    dates = []
    for value in (start_date, end_date):
        try:
            if value and not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
                raise ValueError('Invalid date format')
            dates.append(datetime.strptime(value, '%Y-%m-%d').date() if value else None)
        except ValueError:
            raise HTTPException(422, 'Dates must be YYYY-MM-DD.')
    if all(dates) and dates[0] > dates[1]:
        raise HTTPException(422, 'Start date must be on or before end date.')
    clauses, params = [], []
    if username and username.strip():
        # Literal contains search, not SQL wildcard interpretation.
        value = username.strip().replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        clauses.append("COALESCE(u.name, '') ILIKE %s")
        params.append('%' + value + '%')
    for date, op, extra in ((dates[0], '>=', 0), (dates[1], '<', 1)):
        if date:
            bound = datetime.combine(date + timedelta(days=extra), time.min, ZoneInfo('Asia/Kolkata'))
            clauses.append(f'm.timestamp {op} %s')
            params.append(bound.astimezone(timezone.utc).replace(tzinfo=None))
    if chat_type:
        clauses.append('chat_type = %s')
        params.append(chat_type)
    classification = {
        'mismatches': "status = 'completed' AND mismatch_count > 0",
        'unverified': "status = 'completed' AND unverified_count > 0",
        'failures': "status = 'failed'",
    }[view]
    # User/date filtering is inside the join; chat_type is an alias in the CTE.
    type_filter = clauses.pop() if chat_type else None
    base = ('WHERE ' + ' AND '.join(clauses)) if clauses else ''
    final = classification + (' AND ' + type_filter if type_filter else '')
    return base, final, params


def list_evidence_errors(conn, *, view='mismatches', username=None, start_date=None,
                         end_date=None, chat_type=None, page=1, limit=25):
    base, final, params = query_filters(view, username, start_date, end_date, chat_type)
    # Legacy model opinions in claim_checks are intentionally NOT treated as
    # confirmed calculator mismatches. Use typed fact_checks, never cached counts.
    cte = f"""
    WITH source AS (
      SELECT a.message_id, a.status, a.error_message, a.created_at AS audit_created_at,
             m.timestamp AS answer_at, m.session_id, s.user_id,
             COALESCE(NULLIF(u.name,''), 'User #' || s.user_id::text) AS username,
             COALESCE(NULLIF(a.evidence_brief,''),'{{}}')::jsonb AS brief,
             COALESCE(NULLIF(a.evaluator_result,''),'{{}}')::jsonb AS report,
             lower(COALESCE(NULLIF(COALESCE(NULLIF(a.evidence_brief,''),'{{}}')::jsonb->>'chat_tier',''),
                            NULLIF(m.chat_tier,''), 'standard')) AS chat_type
      FROM chat_answer_evidence_audits a
      JOIN chat_messages m ON m.message_id=a.message_id
      JOIN chat_sessions s ON s.session_id=m.session_id
      LEFT JOIN users u ON u.userid=s.user_id
      {base}
    ), counted AS (
      SELECT source.*, counts.* FROM source
      CROSS JOIN LATERAL (
        SELECT count(*) FILTER (WHERE f->>'status'='mismatch')::int AS mismatch_count,
               count(*) FILTER (WHERE f->>'status' IN ('unsupported','ambiguous','invalid_extraction','calculation_failed'))::int AS unverified_count
        FROM jsonb_array_elements(CASE WHEN jsonb_typeof(report->'fact_checks')='array'
             THEN report->'fact_checks' ELSE '[]'::jsonb END) f
      ) counts
    ), filtered AS (SELECT * FROM counted WHERE {final})
    """
    total = int(execute(conn, cte + 'SELECT count(*) FROM filtered', tuple(params)).fetchone()[0])
    rows = execute(conn, cte + """
      SELECT message_id, status, error_message, answer_at, session_id, user_id, username, chat_type,
             brief->>'question', report->>'summary', mismatch_count, unverified_count
      FROM filtered ORDER BY answer_at DESC NULLS LAST, message_id DESC LIMIT %s OFFSET %s
    """, (*params, limit, (page-1)*limit)).fetchall()
    fields = ('message_id','status','error_message','answer_at','session_id','user_id','username',
              'chat_type','question','summary','mismatch_count','unverified_count')
    items = [dict(zip(fields,row)) for row in rows]
    for item in items:
        date=item['answer_at']
        if isinstance(date,datetime):
            if date.tzinfo is None: date=date.replace(tzinfo=timezone.utc)
            item['answer_at']=date.astimezone(ZoneInfo('Asia/Kolkata')).isoformat()
    return {'items':items,'total':total,'page':page,'total_pages':max(1,(total+limit-1)//limit),
            'view':view,'timezone':'Asia/Kolkata'}
