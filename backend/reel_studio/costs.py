"""Durable per-attempt metering. Usage-based estimates are not invoices.

Write an unknown-cost event BEFORE a paid call. A crash/timeout therefore cannot
silently turn a possibly billed request into zero. Each retry gets its own event;
settling the same event twice updates it rather than adding another charge.
"""
from contextlib import contextmanager
from contextvars import ContextVar
import json
import hashlib
import math
import os
import time
import uuid

from db import execute
from reel_studio.database import get_conn

CURRENT = ContextVar('reel_cost_run', default=None)
DEFAULTS = {
    'usd_to_inr': float(os.getenv('REEL_USD_TO_INR', '95')),
    'tax_percent': None, 'payment_fee_percent': None,
    'worker_inr_per_second': None, 'storage_inr_per_gib_month': None,
    'upload_inr_per_gib': None, 'storage_write_inr_per_1000': None,
    'storage_months': 1.0,
}
# Standard synchronous API rates, checked 2026-11-07. No free-tier allocation.
# https://developers.openai.com/api/docs/guides/image-generation
# https://developers.openai.com/api/docs/models/gpt-5.6-luna
# https://ai.google.dev/gemini-api/docs/pricing
# https://cloud.google.com/text-to-speech/pricing
RATES = {
    'gpt-image-2': {'text_input': 5.0, 'image_input': 8.0, 'output': 30.0},
    'gemini-3-flash-preview': {'input': .50, 'cached_input': .05, 'output': 3.0},
    'gpt-5.6-luna': {'input': .20, 'cached_input': .02, 'output': 1.20},
    'gemini-omni-1.1-flash': {'input': 1.50, 'video_output': 17.50, 'text_output': 9.0},
}


def ensure_tables(conn):
    execute(conn, '''CREATE TABLE IF NOT EXISTS reel_cost_runs (
        run_id TEXT PRIMARY KEY, user_id INTEGER NOT NULL, status TEXT NOT NULL,
        config_json TEXT NOT NULL, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)''')
    execute(conn, '''CREATE TABLE IF NOT EXISTS reel_cost_settings (
        id INTEGER PRIMARY KEY, config_json TEXT NOT NULL)''')
    execute(conn, '''CREATE TABLE IF NOT EXISTS reel_cost_reconciliations (
        id SERIAL PRIMARY KEY, run_id TEXT NOT NULL, total_inr DOUBLE PRECISION NOT NULL,
        reference TEXT NOT NULL, admin_id INTEGER NOT NULL, ledger_hash TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)''')


def settings(conn):
    row = execute(conn, 'SELECT config_json FROM reel_cost_settings WHERE id=1').fetchone()
    return {**DEFAULTS, **(json.loads(row[0]) if row else {})}


def validate_settings(value):
    if set(value) != set(DEFAULTS):
        raise ValueError('Provide every cost setting; use null for unknown charges.')
    for key, number in value.items():
        if number is None and key not in ('usd_to_inr', 'storage_months'):
            continue
        if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number) or number < 0:
            raise ValueError(f'Invalid {key}')
        if key == 'usd_to_inr' and number == 0:
            raise ValueError('Exchange rate must be positive')
        if key.endswith('percent') and number > 100:
            raise ValueError('Percentages must be between 0 and 100')
    return value


@contextmanager
def session(user_id, run_id, *, planning=False):
    from reel_studio.routes import _ensure_tables
    with get_conn() as conn:
        _ensure_tables(conn)
        config = settings(conn)
        execute(conn, '''INSERT INTO reel_cost_runs (run_id,user_id,status,config_json)
            VALUES (%s,%s,%s,%s) ON CONFLICT (run_id) DO NOTHING''',
            (run_id, user_id, 'planning' if planning else 'rendering', json.dumps(config)))
        row = execute(conn, 'SELECT config_json FROM reel_cost_runs WHERE run_id=%s', (run_id,)).fetchone()
        conn.commit()
    token = CURRENT.set((user_id, run_id, json.loads(row[0])))
    started = time.monotonic()
    try:
        with attempt('compute', 'worker', phase='planning' if planning else 'rendering') as event:
            try:
                yield
            except BaseException:
                set_status(run_id, 'planning_failed' if planning else 'render_failed')
                raise
            else:
                if planning:
                    set_status(run_id, 'draft_ready')
            finally:
                event.finish({'worker_seconds': time.monotonic()-started})
    finally:
        CURRENT.reset(token)


def set_status(run_id, status):
    with get_conn() as conn:
        execute(conn, 'UPDATE reel_cost_runs SET status=%s, updated_at=CURRENT_TIMESTAMP WHERE run_id=%s', (status, run_id))
        conn.commit()


def price(stage, model, usage, config):
    """Return INR and rate breakdown, or None when usage/rates are unknown."""
    components = []
    def add(name, count, rate, divisor=1_000_000):
        if count is None or rate is None:
            raise ValueError('Missing usage or rate')
        count, rate = float(count), float(rate)
        if not math.isfinite(count) or count < 0 or not math.isfinite(rate) or rate < 0:
            raise ValueError('Invalid usage or rate')
        components.append({'unit': name, 'units': count, 'rate': rate, 'divisor': divisor,
                           'subtotal': count*rate/divisor})
    try:
        rates = RATES.get(model, {})
        currency = 'USD'
        if stage == 'image':
            details = usage.get('input_tokens_details') or {}
            add('text_input_tokens', details.get('text_tokens'), rates.get('text_input'))
            add('image_input_tokens', details.get('image_tokens'), rates.get('image_input'))
            if sum(c['units'] for c in components) != usage.get('input_tokens'):
                raise ValueError('Input modality totals do not match')
            add('image_output_tokens', usage.get('output_tokens'), rates.get('output'))
        elif stage in ('planning', 'plan_repair', 'presenter_rewrite', 'studio_reading'):
            cached = (usage.get('input_tokens_details') or {}).get('cached_tokens', 0)
            total = usage.get('input_tokens')
            add('input_tokens', None if total is None else total-cached, rates.get('input'))
            add('cached_tokens', cached, rates.get('cached_input'))
            # Reasoning tokens are already included in output_tokens.
            add('output_tokens', usage.get('output_tokens'), rates.get('output'))
        elif stage == 'video':
            add('input_tokens', usage.get('total_input_tokens'), rates.get('input'))
            modalities = {r['modality']: r['tokens'] for r in usage.get('output_tokens_by_modality', [])}
            if set(modalities) - {'video', 'text'}:
                raise ValueError('Unpriced output modality')
            add('video_output_tokens', modalities.get('video'), rates.get('video_output'))
            add('text_output_tokens', modalities.get('text', 0), rates.get('text_output'))
            add('thought_tokens', usage.get('total_thought_tokens'), rates.get('text_output'))
        elif stage == 'tts':
            rate = next((r for name, r in [('Chirp', 30), ('Studio', 160), ('Neural2', 16),
                        ('Polyglot', 16), ('Wavenet', 4), ('Standard', 4)] if name.lower() in model.lower()), None)
            add('characters', usage.get('characters'), rate)
        elif stage == 'compute':
            currency = 'INR'
            add('allocated_worker_seconds', usage.get('worker_seconds'), config.get('worker_inr_per_second'), 1)
        elif stage == 'storage':
            currency = 'INR'
            add('gib_months', usage.get('bytes', 0)/1024**3*config['storage_months'], config.get('storage_inr_per_gib_month'), 1)
            add('upload_gib', usage.get('bytes', 0)/1024**3, config.get('upload_inr_per_gib'), 1)
            add('object_writes', usage.get('writes'), config.get('storage_write_inr_per_1000'), 1000)
        else:
            return None, []
        total = sum(c['subtotal'] for c in components)
        return total*(config['usd_to_inr'] if currency == 'USD' else 1), components
    except (ValueError, TypeError, KeyError):
        return None, components


class Attempt:
    def __init__(self, stage, model, metadata):
        self.context, self.stage, self.model = CURRENT.get(), stage, model
        self.metadata = {'ledger_version': 2, 'state': 'pending', 'basis': 'unknown',
                         'attempt_id': uuid.uuid4().hex, **metadata}
        self.id = None
        self.finished = False
        if self.context:
            user, run, config = self.context
            self.metadata['pricing_config'] = config
            with get_conn() as conn:
                self.id = execute(conn, '''INSERT INTO reel_generation_costs
                    (user_id,run_id,stage,provider,units,unit_cost_inr,total_cost_inr,metadata_json)
                    VALUES (%s,%s,%s,%s,1,0,0,%s) RETURNING id''',
                    (user, run, stage, model, json.dumps(self.metadata))).fetchone()[0]
                conn.commit()

    def finish(self, usage, request_id=None):
        if not self.context:
            return
        if hasattr(usage, 'model_dump'):
            usage = usage.model_dump()
        usage = usage if isinstance(usage, dict) else {}
        cost, parts = price(self.stage, self.model, usage, self.context[2])
        self.metadata.update(state='received', usage=usage, request_id=request_id,
                             basis='usage_estimate' if cost is not None else 'unknown', components=parts)
        self.save(cost)
        self.finished = True

    def save(self, cost=None):
        if self.id is not None:
            with get_conn() as conn:
                execute(conn, '''UPDATE reel_generation_costs SET total_cost_inr=%s, metadata_json=%s
                    WHERE id=%s''', (cost or 0, json.dumps(self.metadata), self.id))
                conn.commit()


@contextmanager
def attempt(stage, model, **metadata):
    event = Attempt(stage, model, metadata)
    try:
        yield event
    except BaseException as exc:
        if not event.finished:
            event.metadata.update(state='uncertain', error_type=type(exc).__name__)
            event.save()
        raise
    else:
        if not event.finished:
            event.metadata['state'] = 'usage_missing'
            event.save()


def responses_create(stage, **kwargs):
    from openai import OpenAI
    with attempt(stage, kwargs['model']) as event:
        # Disable invisible SDK retries: each repair/request is separately metered.
        response = OpenAI(api_key=os.environ['OPENAI_API_KEY'], timeout=45, max_retries=0).responses.create(**kwargs)
        event.finish(getattr(response, 'usage', None), getattr(response, 'id', None))
        return response


def summarize(charges, config, *, tracked):
    known = sum(c['total_inr'] for c in charges if c['total_inr'] is not None)
    missing = [f"{c['stage']}: usage or rate unavailable" for c in charges if c['total_inr'] is None]
    if not tracked:
        missing.append('Legacy run: planning, retries and input charges may be missing')
    tax_rate, fee_rate = config.get('tax_percent'), config.get('payment_fee_percent')
    tax = None if tax_rate is None else known*tax_rate/100
    fee = None if fee_rate is None else (known+(tax or 0))*fee_rate/100
    if tax_rate is None: missing.append('Tax rate not configured')
    if fee_rate is None: missing.append('Payment/FX fee not configured')
    return {'known_subtotal_inr': round(known, 6), 'tax_inr': tax, 'payment_fee_inr': fee,
            'estimated_total_inr': round(known+(tax or 0)+(fee or 0), 6),
            'cost_complete': not missing, 'missing_costs': sorted(set(missing)),
            'actual_total_inr': None, 'pricing_config': config}


def read_charges(conn, run_id, user_id):
    rows = execute(conn, '''SELECT stage,provider,units,unit_cost_inr,total_cost_inr,metadata_json,created_at
        FROM reel_generation_costs WHERE run_id=%s AND user_id=%s ORDER BY id''', (run_id,user_id)).fetchall()
    result = []
    for stage, provider, units, rate, total, raw, created in rows:
        meta = json.loads(raw or '{}')
        tracked = meta.get('ledger_version') == 2
        known = meta.get('basis') == 'usage_estimate' if tracked else float(total) > 0
        result.append({'stage': stage, 'provider': provider, 'total_inr': float(total) if known else None,
                       'basis': meta.get('basis', 'legacy_estimate'), 'metadata': meta,
                       'created_at': created.isoformat() if created else None})
    return result


def ledger_hash(charges):
    return hashlib.sha256(json.dumps(charges, sort_keys=True).encode()).hexdigest()
