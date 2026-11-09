"""Owned, durable chapter purchases and saved readings."""
import asyncio
import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from typing import Literal
from starlette.concurrency import run_in_threadpool
from auth import get_current_user
from db import execute, get_conn
from credits.credit_service import CreditService
from .periods import select_next_antardasha
from .service import build_next_chapter, narrate_next_chapter

router = APIRouter(prefix='/next-chapter', tags=['next-chapter'])
log = logging.getLogger(__name__)
KEY = 'next_chapter_cost'


def schema(conn):
    execute(conn, '''CREATE TABLE IF NOT EXISTS next_chapter_jobs (
        id TEXT PRIMARY KEY, user_id INTEGER NOT NULL, chart_id INTEGER NOT NULL,
        cache_key TEXT NOT NULL, language TEXT NOT NULL, status TEXT NOT NULL,
        stage TEXT NOT NULL DEFAULT 'queued', cost INTEGER NOT NULL,
        refunded BOOLEAN NOT NULL DEFAULT FALSE, request_json TEXT NOT NULL,
        result_json TEXT, audit_json TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)''')
    execute(conn, '''CREATE UNIQUE INDEX IF NOT EXISTS next_chapter_active_key
        ON next_chapter_jobs(user_id, cache_key) WHERE status IN ('queued','processing','completed')''')
    execute(conn, '''CREATE TABLE IF NOT EXISTS next_chapter_quotes (
        id TEXT PRIMARY KEY, user_id INTEGER NOT NULL, payload TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)''')


def owned_birth(chart_id, user_id):
    from prediction_engine.routes import _load_owned_birth_chart, _normalise_birth_data
    return _normalise_birth_data(_load_owned_birth_chart(chart_id, user_id))


def price(user_id):
    service = CreditService()
    # The shared setting resolver applies Admin discounts and the 49-credit
    # default when this setting has not been seeded yet.
    base = service.get_credit_setting(KEY)
    return service.get_effective_cost(user_id, base, KEY), service.get_user_credits(user_id)


class QuoteRequest(BaseModel):
    birth_chart_id: int = Field(gt=0)
    language: Literal['en', 'hi'] = 'en'
    selection: Literal['current', 'next'] = 'current'


class PurchaseRequest(BaseModel):
    quote_id: str = Field(min_length=32, max_length=64)


def quote(payload, user_id):
    birth = owned_birth(payload.birth_chart_id, user_id)
    now = datetime.now(timezone.utc)
    spine = select_next_antardasha(birth, now, selection=payload.selection)
    cost, credits = price(user_id)
    fingerprint = hashlib.sha256(json.dumps(birth, sort_keys=True, default=str).encode()).hexdigest()
    cache_key = hashlib.sha256(f'{fingerprint}:{spine["antardasha"]["start_at"]}:{payload.language}'.encode()).hexdigest()
    request = {'birth': birth, 'chart_id': payload.birth_chart_id, 'as_of': now.isoformat(),
               'selection': payload.selection, 'language': payload.language, 'spine': spine, 'cost': cost, 'cache_key': cache_key,
               'fingerprint': fingerprint}
    quote_id = uuid.uuid4().hex
    with get_conn() as conn:
        schema(conn)
        saved = execute(conn, "SELECT id FROM next_chapter_jobs WHERE user_id=%s AND cache_key=%s AND status IN ('queued','processing','completed')", (user_id, cache_key)).fetchone()
        execute(conn, 'INSERT INTO next_chapter_quotes(id,user_id,payload) VALUES (%s,%s,%s)', (quote_id,user_id,json.dumps(request,default=str)))
        conn.commit()
    return {'quote_id': quote_id, 'credit_cost': cost, 'credits': credits,
            'spine': spine, 'native_name': birth.get('name'), 'saved_job_id': saved[0] if saved else None}


@router.post('/quote')
async def get_quote(payload: QuoteRequest, user=Depends(get_current_user)):
    return await run_in_threadpool(quote, payload, user.userid)


def progress_percent(status, stage, audit):
    """Weighted completed work, not elapsed time; repairs reserve the final 6%."""
    if status == 'completed':
        return 100
    if status == 'queued':
        return 0
    completed = {c.get('stage', '') for c in (audit or {}).get('calls', [])
                 if not c.get('validation_error') and not c.get('provider_error')}
    value = 2 if stage == 'mapping' and not completed else 5
    for prefix, total, weight in [('plan_', 9, 24), ('coverage_', 3, 15), ('write_', 3, 27)]:
        value += int(min(total, sum(s.startswith(prefix) for s in completed)) * weight / total)
    value += 3 * ('chapter_edit' in completed)
    value += 6 * ('chapter_spectrum' in completed)
    value += 5 * ('event_review' in completed)
    # Repeated review rounds and repairs must not count as new report sections.
    reviewed = {s.rsplit('_pd_', 1)[-1] for s in completed if s.startswith('fact_review_')}
    value += min(3, len(reviewed)) * 3
    return min(94, value)


def public_job(row, include_result=False):
    request = json.loads(row[7])
    result = {'id': row[0], 'chart_id': row[1], 'language': row[2], 'status': row[3],
              'stage': row[4], 'credit_cost': row[5], 'refunded': row[6],
              'native_name': request['birth'].get('name'), 'spine': request['spine'],
              'created_at': row[8],
              'progress_percent': progress_percent(row[3], row[4], json.loads(row[10]) if row[10] else {})}
    if include_result and row[9]:
        result['report'] = json.loads(row[9])
    return result


COLUMNS = 'id,chart_id,language,status,stage,cost,refunded,request_json,created_at,result_json,audit_json'


@router.get('/jobs')
def history(user=Depends(get_current_user)):
    with get_conn() as conn:
        schema(conn)
        rows = execute(conn, f'SELECT {COLUMNS} FROM next_chapter_jobs WHERE user_id=%s ORDER BY created_at DESC LIMIT 100', (user.userid,)).fetchall()
        conn.commit()
    return {'chapters': [public_job(row) for row in rows]}


@router.get('/jobs/{job_id}')
def get_job(job_id: str, response: Response, user=Depends(get_current_user)):
    response.headers['Cache-Control'] = 'no-store'
    with get_conn() as conn:
        row = execute(conn, f'SELECT {COLUMNS} FROM next_chapter_jobs WHERE id=%s AND user_id=%s', (job_id,user.userid)).fetchone()
        conn.commit()
    if not row:
        raise HTTPException(404, 'Chapter not found')
    return public_job(row, True)


def purchase(quote_id, user_id):
    with get_conn() as conn:
        schema(conn)
        row = execute(conn, "SELECT payload FROM next_chapter_quotes WHERE id=%s AND user_id=%s AND created_at > CURRENT_TIMESTAMP - INTERVAL '15 minutes' FOR UPDATE", (quote_id,user_id)).fetchone()
        if not row:
            raise HTTPException(409, 'quote_expired')
        request = json.loads(row[0])
        # Serialize all purchases for this user, including separate tabs/quotes.
        execute(conn, 'SELECT userid FROM user_credits WHERE userid=%s FOR UPDATE', (user_id,)).fetchone()
        saved = execute(conn, "SELECT id FROM next_chapter_jobs WHERE user_id=%s AND cache_key=%s AND status IN ('queued','processing','completed')", (user_id,request['cache_key'])).fetchone()
        if saved:
            return saved[0], False
        birth = owned_birth(request['chart_id'], user_id)
        fingerprint = hashlib.sha256(json.dumps(birth,sort_keys=True,default=str).encode()).hexdigest()
        cost, _ = price(user_id)
        if fingerprint != request['fingerprint'] or cost is None or cost != request['cost']:
            raise HTTPException(409, 'quote_changed')
        balance = execute(conn, 'UPDATE user_credits SET credits=credits-%s,updated_at=CURRENT_TIMESTAMP WHERE userid=%s AND credits >= %s RETURNING credits', (cost,user_id,cost)).fetchone()
        if not balance:
            raise HTTPException(402, 'insufficient_credits')
        job_id = 'chapter_' + uuid.uuid4().hex
        execute(conn, '''INSERT INTO next_chapter_jobs(id,user_id,chart_id,cache_key,language,status,cost,request_json)
            VALUES (%s,%s,%s,%s,%s,'queued',%s,%s)''', (job_id,user_id,request['chart_id'],request['cache_key'],request['language'],cost,json.dumps(request)))
        execute(conn, '''INSERT INTO credit_transactions(userid,transaction_type,amount,balance_after,source,reference_id,description)
            VALUES (%s,'spent',%s,%s,'feature_usage','next_chapter',%s)''', (user_id,-cost,balance[0],f'Your Next Chapter ({job_id})'))
        conn.commit()
    return job_id, True


def fail_and_refund(job_id):
    with get_conn() as conn:
        row = execute(conn, 'SELECT user_id,cost,refunded,status FROM next_chapter_jobs WHERE id=%s FOR UPDATE', (job_id,)).fetchone()
        if not row or row[3] == 'completed':
            return
        if not row[2] and row[1]:
            balance = execute(conn, 'UPDATE user_credits SET credits=credits+%s,updated_at=CURRENT_TIMESTAMP WHERE userid=%s RETURNING credits', (row[1],row[0])).fetchone()
            if not balance:
                raise RuntimeError('Missing credit account during chapter refund')
            execute(conn, '''INSERT INTO credit_transactions(userid,transaction_type,amount,balance_after,source,reference_id,description)
                VALUES (%s,'refund',%s,%s,'refund','next_chapter',%s)''', (row[0],row[1],balance[0],f'Your Next Chapter refund ({job_id})'))
        execute(conn, "UPDATE next_chapter_jobs SET status='failed',stage='failed',refunded=TRUE,updated_at=CURRENT_TIMESTAMP WHERE id=%s", (job_id,))
        conn.commit()


@router.post('/jobs')
async def create_job(payload: PurchaseRequest, background_tasks: BackgroundTasks, user=Depends(get_current_user)):
    from reports.task_queue import enqueue_report_processing_task, report_tasks_enabled
    job_id, created = await run_in_threadpool(purchase, payload.quote_id, user.userid)
    if created:
        queued = await run_in_threadpool(enqueue_report_processing_task, report_id=job_id, payload={'report_type':'next_chapter'})
        if not queued:
            if report_tasks_enabled():
                await run_in_threadpool(fail_and_refund, job_id)
                raise HTTPException(503, 'queue_unavailable_refunded')
            background_tasks.add_task(process_job, job_id)
    return {'id': job_id, 'cached': not created}


async def process_job(job_id):
    # Transaction advisory lock also works through transaction-pooling proxies.
    # Keep table reads on separate short transactions so polling never waits on
    # table locks held for the full generation.
    lock = int.from_bytes(hashlib.sha256(job_id.encode()).digest()[:8], 'big', signed=True)
    with get_conn() as guard:
        if not execute(guard,'SELECT pg_try_advisory_xact_lock(%s)',(lock,)).fetchone()[0]:
            raise HTTPException(503, 'Chapter already processing')
        try:
            with get_conn() as reader:
                row = execute(reader, 'SELECT request_json,status,audit_json FROM next_chapter_jobs WHERE id=%s', (job_id,)).fetchone()
            if not row or row[1] in ('completed','failed'):
                return {'status': row[1] if row else 'missing'}
            request = json.loads(row[0])
            def update(stage, audit=None):
                with get_conn() as conn:
                    execute(conn,"UPDATE next_chapter_jobs SET status='processing',stage=%s,audit_json=COALESCE(%s,audit_json),updated_at=CURRENT_TIMESTAMP WHERE id=%s AND status IN ('queued','processing')", (stage,json.dumps(audit,default=str) if audit else None,job_id))
                    conn.commit()
            update('mapping')
            dossier = await run_in_threadpool(build_next_chapter,request['birth'],datetime.fromisoformat(request['as_of']),selection=request.get('selection', 'next'))
            update('exploring')
            def audit_sink(audit):
                calls = audit.get('calls', [])
                stage = calls[-1]['stage'] if calls else ''
                update('reviewing' if 'review' in stage or 'repair' in stage or 'patch' in stage else 'writing' if 'write' in stage or 'spectrum' in stage else 'exploring', audit)
            output = await narrate_next_chapter(dossier,request['language'],audit_sink=audit_sink,resume_audit=json.loads(row[2]) if row[2] else None)
            with get_conn() as conn:
                execute(conn,"UPDATE next_chapter_jobs SET status='completed',stage='completed',result_json=%s,updated_at=CURRENT_TIMESTAMP WHERE id=%s", (json.dumps(output['report'],ensure_ascii=False),job_id))
                conn.commit()
            return {'status':'completed'}
        except Exception:
            log.exception('Chapter generation failed job=%s',job_id)
            await run_in_threadpool(fail_and_refund,job_id)
            return {'status':'failed'}
        finally:
            guard.rollback()


@router.post('/jobs/{job_id}/reel-source')
def create_reel_source(job_id: str, user=Depends(get_current_user)):
    from .reel_source import source_for_chapter
    return source_for_chapter(job_id, user.userid)
