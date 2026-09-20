"""Unified administrative billing view. Provider reads never cancel or charge."""
from datetime import datetime, timedelta, timezone
import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from auth import User, get_current_user
from db import execute, get_conn
from credits import subscription_ledger as ledger

router = APIRouter(prefix='/admin/subscriptions', tags=['admin subscriptions'])
logger = logging.getLogger(__name__)


def admin(user: User = Depends(get_current_user)):
    if user.role != 'admin':
        raise HTTPException(403, 'Admin access required')
    return user


def rows(cursor):
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row)) for row in cursor.fetchall()]


def present(row):
    # Existing access dates are UTC timestamps without a timezone in PostgreSQL.
    for key in ('start_date', 'access_until'):
        value = row.get(key)
        if isinstance(value, datetime) and value.tzinfo is None:
            row[key] = value.replace(tzinfo=timezone.utc)
    snapshot = row.pop('snapshot', None) or {}
    status = snapshot.get('status') or 'unverified'
    auto = snapshot.get('auto_renew')
    cancelled = status in ('cancelled', 'completed', 'expired') or snapshot.get('cancel_requested') or row.get('cancel_at_period_end')
    if cancelled:
        auto = False
    elif row['provider'] == 'razorpay' and status == 'active':
        auto = True
    next_charge = ledger.utc_timestamp(snapshot.get('charge_at')) if auto is True else None
    checked = row.get('checked_at')
    issue = row.get('issue')
    if not issue and (not checked or checked < datetime.now(timezone.utc) - timedelta(hours=24)):
        issue = 'Provider status has not been verified in the last 24 hours.'
    row.update(billing_status='cancel_scheduled' if cancelled and status == 'active' else status,
               auto_renew=auto, next_charge_at=next_charge,
               provider_period_end=ledger.utc_timestamp(snapshot.get('current_end')),
               subscribed_at=ledger.utc_timestamp(snapshot.get('created_at') or snapshot.get('start_at')) or row.get('start_date'),
               cancelled_at=ledger.utc_timestamp(snapshot.get('ended_at')) if status == 'cancelled' else None,
               paid_count=snapshot.get('paid_count'),
               provider_order_id=snapshot.get('order_id'), issue=issue)
    return row


@router.get('')
def overview(query: str = '', provider: str = '', view: str = '',
             page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=200), user=Depends(admin)):
    ledger.ensure_schema()
    with get_conn() as conn:
        # Maps retain subscriptions even if their access row was superseded or not linked.
        rz = rows(execute(conn, '''SELECT 'razorpay' AS provider, m.razorpay_subscription_id AS external_id,
            m.userid,u.name AS user_name,u.phone AS user_phone,sp.plan_name,sp.tier_name,
            a.start_date,a.end_date AS access_until,a.status AS access_status,a.cancel_at_period_end,
            b.snapshot,b.checked_at,b.issue
            FROM razorpay_subscription_map m LEFT JOIN users u ON u.userid=m.userid
            LEFT JOIN subscription_plans sp ON sp.plan_id=m.internal_plan_id
            LEFT JOIN subscription_billing_state b ON b.provider='razorpay' AND b.external_id=m.razorpay_subscription_id
            LEFT JOIN LATERAL (SELECT * FROM user_subscriptions us WHERE us.razorpay_subscription_id=m.razorpay_subscription_id
                AND us.userid=m.userid ORDER BY us.id DESC LIMIT 1) a ON TRUE'''))
        play = rows(execute(conn, '''SELECT 'google_play' AS provider,m.purchase_token,m.userid,
            u.name AS user_name,u.phone AS user_phone,sp.plan_name,sp.tier_name,
            a.start_date,a.end_date AS access_until,a.status AS access_status,a.cancel_at_period_end
            FROM play_subscription_token_map m LEFT JOIN users u ON u.userid=m.userid
            LEFT JOIN subscription_plans sp ON sp.google_play_product_id=m.product_id
            LEFT JOIN LATERAL (SELECT * FROM user_subscriptions us WHERE us.userid=m.userid
                AND us.plan_id=sp.plan_id AND us.billing_provider='google_play'
                AND split_part(COALESCE(us.google_play_order_id,''),'..',1)=split_part(COALESCE(m.latest_order_id,''),'..',1)
                AND m.latest_order_id IS NOT NULL ORDER BY us.id DESC LIMIT 1) a ON TRUE'''))
        states = {(r['provider'], r['external_id']): r for r in rows(execute(conn,
            'SELECT provider,external_id,snapshot,checked_at,issue FROM subscription_billing_state'))}
        unlinked = rows(execute(conn, '''SELECT COALESCE(us.billing_provider,'unknown') AS provider,
            'membership_' || us.id AS external_id,us.userid,u.name AS user_name,u.phone AS user_phone,
            sp.plan_name,sp.tier_name,us.start_date,us.end_date AS access_until,us.status AS access_status,
            us.cancel_at_period_end,'Membership has no provider subscription link.' AS issue
            FROM user_subscriptions us JOIN users u ON u.userid=us.userid
            JOIN subscription_plans sp ON sp.plan_id=us.plan_id
            WHERE us.status='active' AND us.end_date>=CURRENT_DATE AND us.razorpay_subscription_id IS NULL
              AND us.google_play_order_id IS NULL AND COALESCE(sp.price,0)>0'''))
        unresolved = execute(conn, "SELECT COUNT(*) FROM subscription_lifecycle_events WHERE processing_status IN ('received','failed','needs_attention')").fetchone()[0]
    for row in play:
        row['external_id'] = ledger.play_reference(row.pop('purchase_token'))
        row.update(states.get(('google_play', row['external_id']), {}))
    records = [present(r) for r in rz + play + unlinked]
    now = datetime.now(timezone.utc)
    summary = {'subscribers': len({r['userid'] for r in records if r.get('access_status') == 'active' and r.get('access_until') and str(r['access_until'])[:10] >= now.date().isoformat()}),
               'renewing_soon': sum(bool(r['next_charge_at'] and now <= r['next_charge_at'] <= now + timedelta(days=7)) for r in records),
               'cancelled': sum(r['billing_status'] in ('cancelled','cancel_scheduled') for r in records),
               'payment_issues': sum(r['billing_status'] in ('halted','pending','on_hold','in_grace_period') for r in records),
               'needs_attention': sum(bool(r['issue']) for r in records), 'unresolved_events': unresolved}
    if query.strip():
        q = query.strip().lower()
        records = [r for r in records if any(q in str(r.get(k) or '').lower() for k in ('external_id','userid','user_name','user_phone','provider_order_id'))]
    if provider:
        records = [r for r in records if r['provider'] == provider]
    if view == 'attention':
        records = [r for r in records if r['issue']]
    elif view == 'cancelled':
        records = [r for r in records if r['billing_status'] in ('cancelled','cancel_scheduled')]
    elif view == 'renewing':
        records = [r for r in records if r['next_charge_at'] and now <= r['next_charge_at'] <= now + timedelta(days=7)]
    elif view == 'payment':
        records = [r for r in records if r['billing_status'] in ('halted','pending','on_hold','in_grace_period')]
    records.sort(key=lambda r: str(r.get('subscribed_at') or ''), reverse=True)
    return {'subscriptions': records[(page-1)*limit:page*limit], 'total': len(records), 'summary': summary}


@router.get('/activity')
def activity(query: str = '', view: str = '', page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=200), user=Depends(admin)):
    ledger.ensure_schema()
    sql = '''WITH events AS (
        SELECT 'razorpay' AS provider,e.external_id,e.userid,u.name AS user_name,e.kind,e.source,
            e.actor,e.actor_userid,e.occurred_at,e.received_at,e.processing_status,e.error
        FROM subscription_lifecycle_events e LEFT JOIN users u ON u.userid=e.userid
        UNION ALL
        SELECT 'google_play',e.google_play_order_id,COALESCE(e.userid,m.userid),u.name,e.event_kind,e.source,
            'unknown',NULL,COALESCE(to_timestamp(e.event_time_millis/1000.0),e.processed_at AT TIME ZONE 'UTC'),
            e.processed_at AT TIME ZONE 'UTC','processed',NULL
        FROM play_subscription_event_log e LEFT JOIN play_subscription_token_map m ON m.purchase_token=e.purchase_token
        LEFT JOIN users u ON u.userid=COALESCE(e.userid,m.userid)
    ) SELECT * FROM events WHERE (%s='' OR external_id ILIKE %s OR user_name ILIKE %s OR userid::text=%s)
        AND (%s<>'unresolved' OR processing_status IN ('received','failed','needs_attention'))
        ORDER BY occurred_at DESC LIMIT %s OFFSET %s'''
    with get_conn() as conn:
        result = rows(execute(conn, sql, (query, '%'+query+'%', '%'+query+'%', query, view, limit+1, (page-1)*limit)))
    return {'events': result[:limit], 'has_more': len(result)>limit}


class ReconcileBody(BaseModel):
    provider: str
    external_id: str


def reconcile_one(provider, external_id, actor_userid=None):
    ledger.ensure_schema()
    if provider == 'razorpay':
        from credits.razorpay_subscription_routes import _fetch_razorpay_subscription
        with get_conn() as conn:
            exists = execute(conn, 'SELECT 1 FROM razorpay_subscription_map WHERE razorpay_subscription_id=%s', (external_id,)).fetchone()
        if not exists:
            raise HTTPException(404, 'Subscription mapping not found')
        with ledger.processing_lock(external_id):
            return ledger.reconcile_razorpay(external_id, _fetch_razorpay_subscription, actor_userid=actor_userid)
    if provider == 'google_play':
        from credits.routes import _fetch_google_play_subscription_purchase, PACKAGE_NAME
        with get_conn() as conn:
            mappings = execute(conn, 'SELECT userid,product_id,purchase_token FROM play_subscription_token_map').fetchall()
        mapping = next((m for m in mappings if ledger.play_reference(m[2]) == external_id), None)
        if not mapping:
            raise HTTPException(404, 'Subscription mapping not found')
        purchase = _fetch_google_play_subscription_purchase(PACKAGE_NAME, mapping[1], mapping[2])
        ledger.record_play_state(mapping[0], mapping[1], mapping[2], purchase)
        return {'status': 'processed'}
    raise HTTPException(400, 'This membership needs manual provider-link review')


@router.post('/reconcile')
def reconcile(body: ReconcileBody, user=Depends(admin)):
    try:
        return reconcile_one(body.provider, body.external_id, user.userid)
    except HTTPException:
        raise
    except Exception:
        logger.exception('Subscription reconciliation failed for %s', body.external_id)
        raise HTTPException(502, 'Provider reconciliation failed; try again later')


def reconcile_batch(limit=20):
    ledger.ensure_schema()
    with get_conn() as conn:
        # One worker across all production instances; transaction lock released on crash.
        if not execute(conn, 'SELECT pg_try_advisory_xact_lock(73106)').fetchone()[0]:
            return
        refs = [('razorpay', r[0]) for r in execute(conn, 'SELECT razorpay_subscription_id FROM razorpay_subscription_map').fetchall()]
        refs += [('google_play', ledger.play_reference(r[0])) for r in execute(conn, 'SELECT purchase_token FROM play_subscription_token_map').fetchall()]
        checked = {(r[0],r[1]):r[2] for r in execute(conn, 'SELECT provider,external_id,checked_at FROM subscription_billing_state').fetchall()}
        cutoff = datetime.now(timezone.utc)-timedelta(hours=6)
        refs = sorted((r for r in refs if r not in checked or checked[r]<cutoff), key=lambda r: checked.get(r,datetime.min.replace(tzinfo=timezone.utc)))[:limit]
        for provider, reference in refs:
            try:
                reconcile_one(provider, reference)
            except Exception:
                logger.exception('Subscription reconciliation failed provider=%s id=%s', provider, reference)
                with get_conn() as failure_conn:
                    execute(failure_conn, '''INSERT INTO subscription_billing_state(provider,external_id,source_at,issue)
                        VALUES (%s,%s,to_timestamp(0),'Provider sync failed; retry pending')
                        ON CONFLICT(provider,external_id) DO UPDATE SET checked_at=NOW(),issue=EXCLUDED.issue''', (provider, reference))
                    failure_conn.commit()
        conn.commit()


async def reconciliation_loop():
    while True:
        await asyncio.sleep(60)
        try:
            await asyncio.to_thread(reconcile_batch)
        except Exception:
            logger.exception('Subscription reconciliation batch failed')
        await asyncio.sleep(540)
