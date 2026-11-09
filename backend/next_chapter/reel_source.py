"""Stable, owned chapter sources for the existing reel pipeline.

Negative source IDs are reserved for chapters; chat message IDs are positive.
No synthetic chat messages or duplicate credit charging are needed.
"""
import hashlib
import json
from fastapi import HTTPException
from db import execute, get_conn


def source_for_chapter(chapter_id, user_id):
    with get_conn() as conn:
        row = execute(conn, 'SELECT status FROM next_chapter_jobs WHERE id=%s AND user_id=%s', (chapter_id, user_id)).fetchone()
        if not row:
            raise HTTPException(404, 'Chapter not found')
        if row[0] != 'completed':
            raise HTTPException(409, 'Chapter is not ready')
        execute(conn, '''CREATE TABLE IF NOT EXISTS next_chapter_reel_sources (
            id SERIAL PRIMARY KEY, chapter_id TEXT NOT NULL UNIQUE,
            user_id INTEGER NOT NULL)''')
        source = execute(conn, '''INSERT INTO next_chapter_reel_sources(chapter_id,user_id)
            VALUES (%s,%s) ON CONFLICT(chapter_id) DO UPDATE SET chapter_id=EXCLUDED.chapter_id
            RETURNING id''', (chapter_id, user_id)).fetchone()
        conn.commit()
    return {'message_id': -source[0]}


def answer_for_source(source_id, user_id):
    from .customer import owned_birth
    with get_conn() as conn:
        row = execute(conn, '''SELECT j.chart_id,j.request_json,j.result_json
            FROM next_chapter_reel_sources s JOIN next_chapter_jobs j ON j.id=s.chapter_id
            WHERE s.id=%s AND s.user_id=%s AND j.user_id=%s AND j.status='completed' ''',
            (-source_id, user_id, user_id)).fetchone()
    if not row or not row[2]:
        raise HTTPException(404, 'Completed chapter not found')
    request = json.loads(row[1])
    birth = owned_birth(row[0], user_id)
    fingerprint = hashlib.sha256(json.dumps(birth, sort_keys=True, default=str).encode()).hexdigest()
    if fingerprint != request['fingerprint']:
        raise HTTPException(409, 'The chart has changed since this chapter was created. Create an updated chapter first.')
    report = json.loads(row[2])
    # Retain every period and its dates, while excluding internal evidence IDs.
    allowed = {'title','overview','mahadasha_context','antardasha_themes','antardasha_events',
               'antardasha_transits','periods','closing','summary','what_changes','manifestations',
               'theme','circumstances','possibilities','why','timing','timing_explanation',
               'timing_windows','practical_guidance','conditions_and_cautions','transit_story',
               'explanation','start_at','end_at','transiting_planet','natal_planet'}
    def clean(value):
        if isinstance(value, dict):
            return {k: clean(v) for k, v in value.items() if k in allowed}
        if isinstance(value, list):
            return [clean(v) for v in value]
        return value
    content = clean(report)
    content['period_calendar'] = request['spine']
    question = ('Create a concise visual overview of this Your Next Chapter report: the selected '
                'Antardasha, its dates, meaningful life events and the most useful Pratyantardasha windows. '
                'Select representative themes across life areas and across the whole period; do not simply '
                'read the beginning or repeat finance and career. Preserve conditional language and dates. '
                'This is a summary, not an exhaustive reading. Use the report calendar and distinguish elapsed from upcoming periods; '
                'do not substitute current dashas from visual data. Do not invent certainty or events.')
    return json.dumps(content, ensure_ascii=False), row[0], question
