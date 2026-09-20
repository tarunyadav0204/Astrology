"""Provider billing state and durable lifecycle history, separate from access grants."""
import hashlib
import json
from contextlib import contextmanager
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from db import execute, get_conn


def ensure_schema():
    with get_conn() as conn:
        execute(conn, '''CREATE TABLE IF NOT EXISTS subscription_billing_state (
            provider TEXT NOT NULL, external_id TEXT NOT NULL, userid INTEGER,
            snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
            source_at TIMESTAMPTZ NOT NULL, checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            issue TEXT, PRIMARY KEY (provider, external_id))''')
        execute(conn, '''CREATE TABLE IF NOT EXISTS subscription_lifecycle_events (
            id BIGSERIAL PRIMARY KEY, event_key TEXT UNIQUE NOT NULL,
            provider TEXT NOT NULL, external_id TEXT NOT NULL, userid INTEGER,
            kind TEXT NOT NULL, source TEXT NOT NULL, actor TEXT NOT NULL DEFAULT 'unknown',
            actor_userid INTEGER, occurred_at TIMESTAMPTZ NOT NULL,
            received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            processing_status TEXT NOT NULL DEFAULT 'received', error TEXT,
            snapshot JSONB NOT NULL)''')
        execute(conn, '''CREATE INDEX IF NOT EXISTS subscription_lifecycle_time_idx
            ON subscription_lifecycle_events (occurred_at DESC)''')
        conn.commit()


def utc_timestamp(value):
    try:
        return datetime.fromtimestamp(float(value), timezone.utc) if value else None
    except (ValueError, TypeError, OverflowError, OSError):
        return None


def razorpay_snapshot(entity):
    # Do not store payment credentials, purchase tokens or arbitrary customer notes.
    keys = ('id', 'plan_id', 'status', 'created_at', 'start_at', 'current_start',
            'current_end', 'charge_at', 'ended_at', 'paid_count', 'total_count',
            'remaining_count', 'has_scheduled_changes', 'change_scheduled_at')
    snapshot = {key: entity.get(key) for key in keys}
    notes = entity.get('notes') or {}
    if isinstance(notes, dict):
        for key in ('userid', 'internal_plan_id', 'product_id'):
            snapshot[key] = notes.get(key)
    return snapshot


def play_reference(token):
    return 'play_' + hashlib.sha256(token.encode()).hexdigest()[:24]


def record_play_state(userid, product_id, token, purchase):
    ensure_schema()
    line = (purchase.get('lineItems') or [{}])[0]
    auto = (line.get('autoRenewingPlan') or {}).get('autoRenewEnabled', purchase.get('autoRenewing'))
    status = str(purchase.get('subscriptionState') or '').replace('SUBSCRIPTION_STATE_', '').lower()
    if not status:
        expiry = utc_timestamp(float(purchase.get('expiryTimeMillis') or 0) / 1000)
        status = 'expired' if expiry and expiry < datetime.now(timezone.utc) else ('cancelled' if auto is False else 'active')
    status = 'cancelled' if status == 'canceled' else status
    snapshot = {'status': status, 'product_id': product_id, 'auto_renew': auto,
                'start_at': float(purchase.get('startTimeMillis') or 0) / 1000,
                'current_end': float(purchase.get('expiryTimeMillis') or 0) / 1000,
                'order_id': purchase.get('orderId') or purchase.get('latestOrderId')}
    snapshot['charge_at'] = snapshot['current_end'] if auto is True and status == 'active' else None
    reference = play_reference(token)
    with get_conn() as conn:
        execute(conn, '''INSERT INTO subscription_billing_state(provider,external_id,userid,snapshot,source_at)
            VALUES ('google_play',%s,%s,%s::jsonb,NOW()) ON CONFLICT(provider,external_id) DO UPDATE
            SET userid=EXCLUDED.userid,snapshot=EXCLUDED.snapshot,source_at=NOW(),checked_at=NOW(),issue=NULL''',
            (reference, userid, json.dumps(snapshot)))
        conn.commit()


def receive_event(entity, kind, *, source='webhook', event_id=None, event_time=None,
                  actor='unknown', actor_userid=None):
    ensure_schema()
    snapshot = razorpay_snapshot(entity)
    external_id = str(snapshot.get('id') or '').strip()
    if not external_id:
        raise ValueError('Subscription ID is missing')
    occurred = utc_timestamp(event_time) or datetime.now(timezone.utc)
    signature = json.dumps([kind, snapshot, event_time], sort_keys=True)
    key = f"razorpay:{source}:{event_id or hashlib.sha256(signature.encode()).hexdigest()}"
    with get_conn() as conn:
        mapping = execute(conn, '''SELECT userid, internal_plan_id, product_id
            FROM razorpay_subscription_map WHERE razorpay_subscription_id=%s''', (external_id,)).fetchone()
        if mapping:
            snapshot.update(userid=mapping[0], internal_plan_id=mapping[1], product_id=mapping[2])
        try:
            userid = int(snapshot.get('userid'))
        except (ValueError, TypeError):
            userid = None
        row = execute(conn, '''INSERT INTO subscription_lifecycle_events
            (event_key, provider, external_id, userid, kind, source, actor, actor_userid,
             occurred_at, snapshot) VALUES (%s,'razorpay',%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
            ON CONFLICT(event_key) DO UPDATE SET event_key=EXCLUDED.event_key
            RETURNING id, processing_status''',
            (key, external_id, userid, kind, source, actor, actor_userid, occurred, json.dumps(snapshot))).fetchone()
        conn.commit()
    return {'id': row[0], 'done': row[1] in ('processed', 'stale', 'resolved'),
            'snapshot': snapshot, 'occurred_at': occurred, 'userid': userid}


def event_is_done(event_id):
    with get_conn() as conn:
        row = execute(conn, 'SELECT processing_status FROM subscription_lifecycle_events WHERE id=%s', (event_id,)).fetchone()
        return bool(row and row[0] in ('processed', 'stale', 'resolved'))


def finish_event(event_id, status, error=None):
    with get_conn() as conn:
        execute(conn, '''UPDATE subscription_lifecycle_events SET processing_status=%s,error=%s
            WHERE id=%s''', (status, error, event_id))
        conn.commit()


@contextmanager
def processing_lock(external_id):
    with get_conn() as conn:
        acquired = execute(conn, 'SELECT pg_try_advisory_xact_lock(hashtext(%s))',
                           ('subscription-processing:' + external_id,)).fetchone()[0]
        if not acquired:
            raise RuntimeError('Subscription is already being processed; retry later')
        yield
        conn.commit()


def is_stale(event):
    with get_conn() as conn:
        row = execute(conn, '''SELECT source_at, snapshot FROM subscription_billing_state
            WHERE provider='razorpay' AND external_id=%s''', (event['snapshot']['id'],)).fetchone()
        if not row or row[0] <= event['occurred_at']:
            return False
        # A provider read may precede delivery of the charged webhook. Allow
        # that webhook to grant access when it describes the same billing state.
        keys = ('status', 'current_start', 'current_end', 'paid_count')
        return any(row[1].get(key) != event['snapshot'].get(key) for key in keys)


def apply_billing_event(event):
    """Repair only an unambiguous, exact billing-period match. Never grant access."""
    snapshot, userid = event['snapshot'], event['userid']
    external_id = snapshot['id']
    issue = None
    with get_conn() as conn:
        execute(conn, 'SELECT pg_advisory_xact_lock(hashtext(%s))', ('subscription:' + external_id,))
        previous = execute(conn, '''SELECT source_at FROM subscription_billing_state
            WHERE provider='razorpay' AND external_id=%s FOR UPDATE''', (external_id,)).fetchone()
        if previous and previous[0] > event['occurred_at']:
            execute(conn, "UPDATE subscription_lifecycle_events SET processing_status='stale' WHERE id=%s", (event['id'],))
            conn.commit()
            return {'status': 'stale', 'issue': None}
        linked = execute(conn, '''SELECT id FROM user_subscriptions
            WHERE userid=%s AND razorpay_subscription_id=%s ORDER BY id DESC''', (userid, external_id)).fetchall()
        start = utc_timestamp(snapshot.get('current_start') or snapshot.get('start_at'))
        end = utc_timestamp(snapshot.get('current_end'))
        if not linked and userid and snapshot.get('internal_plan_id') and start and end:
            # Legacy membership dates exist in UTC and IST. Accept either exact
            # pair, but never a fuzzy date range or more than one candidate.
            ist = ZoneInfo('Asia/Kolkata')
            candidates = execute(conn, '''SELECT id FROM user_subscriptions
                WHERE userid=%s AND plan_id=%s AND
                  ((DATE(start_date)=%s AND DATE(end_date)=%s) OR
                   (DATE(start_date)=%s AND DATE(end_date)=%s))
                  AND razorpay_subscription_id IS NULL AND billing_provider IS NULL
                FOR UPDATE''', (userid, int(snapshot['internal_plan_id']), start.date(), end.date(),
                               start.astimezone(ist).date(), end.astimezone(ist).date())).fetchall()
            # Multiple provider subscriptions for one period must be reviewed, not guessed.
            competing = execute(conn, '''SELECT m.razorpay_subscription_id FROM razorpay_subscription_map m
                LEFT JOIN subscription_billing_state b ON b.provider='razorpay' AND b.external_id=m.razorpay_subscription_id
                WHERE m.userid=%s AND m.razorpay_subscription_id<>%s AND m.internal_plan_id=%s
                  AND (b.snapshot IS NULL OR b.snapshot='{}'::jsonb OR
                    (b.snapshot->>'status' IN ('active','cancelled','halted','paused')
                     AND b.snapshot->>'current_start'=%s AND b.snapshot->>'current_end'=%s))''',
                (userid, external_id, int(snapshot['internal_plan_id']), str(snapshot.get('current_start')), str(snapshot.get('current_end')))).fetchall()
            if len(candidates) == 1 and not competing and int(snapshot.get('paid_count') or 0) > 0:
                execute(conn, '''UPDATE user_subscriptions SET billing_provider='razorpay',
                    razorpay_subscription_id=%s WHERE id=%s''', (external_id, candidates[0][0]))
                linked = candidates
        if not linked and snapshot.get('status') not in ('created', 'authenticated'):
            issue = 'No unambiguous membership link; review provider and access records.'
        if not userid:
            issue = 'Unknown subscription owner.'
        if snapshot.get('status') == 'cancelled' or snapshot.get('cancel_requested'):
            execute(conn, '''UPDATE user_subscriptions SET cancel_at_period_end=TRUE
                WHERE userid=%s AND razorpay_subscription_id=%s''', (userid, external_id))
        execute(conn, '''INSERT INTO subscription_billing_state
            (provider,external_id,userid,snapshot,source_at,issue) VALUES ('razorpay',%s,%s,%s::jsonb,%s,%s)
            ON CONFLICT(provider,external_id) DO UPDATE SET userid=EXCLUDED.userid,
                snapshot=EXCLUDED.snapshot, source_at=EXCLUDED.source_at, checked_at=NOW(), issue=EXCLUDED.issue''',
            (external_id, userid, json.dumps(snapshot), event['occurred_at'], issue))
        execute(conn, '''UPDATE subscription_lifecycle_events SET processing_status=%s,error=%s
            WHERE id=%s''', ('needs_attention' if issue else 'processed', issue, event['id']))
        if not issue:
            execute(conn, '''UPDATE subscription_lifecycle_events SET processing_status='resolved'
                WHERE provider='razorpay' AND external_id=%s AND id<>%s
                  AND processing_status='needs_attention' AND occurred_at<=%s''',
                (external_id, event['id'], event['occurred_at']))
        conn.commit()
    return {'status': 'needs_attention' if issue else 'processed', 'issue': issue}


def reconcile_razorpay(external_id, fetch_subscription, *, actor_userid=None):
    """Read provider state; never invoke provider mutation APIs."""
    entity = fetch_subscription(external_id)
    if entity.get('id') != external_id:
        raise ValueError('Provider returned a different subscription')
    now = datetime.now(timezone.utc)
    event = receive_event(entity, 'reconciled', source='reconciliation',
                          event_time=now.timestamp(), actor='admin' if actor_userid else 'system', actor_userid=actor_userid)
    try:
        result = apply_billing_event(event)
        # Recover an actual cancellation with its provider timestamp, not today's sync time.
        if entity.get('status') == 'cancelled' and entity.get('ended_at'):
            historical = receive_event(entity, 'subscription.cancelled', source='provider_recovery',
                event_id=f"{external_id}:cancelled:{entity['ended_at']}", event_time=entity['ended_at'])
            finish_event(historical['id'], 'processed')
        return result
    except Exception as error:
        finish_event(event['id'], 'failed', type(error).__name__)
        raise
