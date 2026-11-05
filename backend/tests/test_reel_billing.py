"""Exercise billing mutations and job creation together, with rollback on error."""
import json
import sqlite3
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from fastapi import BackgroundTasks, HTTPException

from reel_studio import billing, routes


@pytest.fixture
def reel_db(monkeypatch):
    conn = sqlite3.connect(":memory:")
    conn.executescript("""
        CREATE TABLE user_credits (userid INTEGER PRIMARY KEY, credits INTEGER, updated_at TEXT);
        CREATE TABLE credit_transactions (userid INTEGER, transaction_type TEXT, amount INTEGER,
            balance_after INTEGER, source TEXT, reference_id TEXT, description TEXT, metadata TEXT);
        CREATE TABLE reel_storyboard_drafts (id TEXT PRIMARY KEY, user_id INTEGER, source_message_id INTEGER, plan_json TEXT);
        CREATE TABLE reel_render_jobs (id TEXT PRIMARY KEY, user_id INTEGER, source_message_id INTEGER,
            mode TEXT, status TEXT, plan_json TEXT);
        INSERT INTO user_credits VALUES (18, 100, NULL);
    """)
    request = routes.RenderRequest(message_id=42, visual_level="cinematic", draft_id="draft_test", approved_claim_ids=["c1"], confirmed_credit_cost=25)
    plan = {"run_id": "reel_test", "credit_cost": 25, "claims": [{"id": "c1"}], "cost_projection": {},
            "settings": {"message_id": 42, "duration_seconds": 180, "language": "en", "visual_level": "cinematic"}}
    conn.execute("INSERT INTO reel_storyboard_drafts VALUES (?, ?, ?, ?)", ("draft_test", 18, 42, json.dumps(plan)))
    conn.commit()

    @contextmanager
    def connection():
        try: yield conn
        finally: conn.rollback()

    def execute(connection, sql, args=()):
        return connection.execute(sql.replace("%s", "?").replace(" FOR UPDATE", ""), args)

    for module in (routes, billing):
        monkeypatch.setattr(module, "get_conn", connection)
        monkeypatch.setattr(module, "execute", execute)
    monkeypatch.setattr(routes, "_ensure_tables", lambda _: None)
    monkeypatch.setattr(routes, "reel_pricing", lambda _: {"credit_cost": 25, "credits": 100})
    monkeypatch.setenv("OPENAI_API_KEY", "test-no-network")
    yield conn, request, SimpleNamespace(userid=18)
    conn.close()


def test_queue_retries_charge_once_and_schedule_once(reel_db):
    conn, request, user = reel_db
    tasks = BackgroundTasks()
    first = routes.queue_render(request, tasks, user)
    second = routes.queue_render(request, tasks, user)
    assert first["job_id"] == second["job_id"]
    assert second["reused"] is True
    assert conn.execute("SELECT credits FROM user_credits").fetchone()[0] == 75
    assert conn.execute("SELECT COUNT(*) FROM credit_transactions").fetchone()[0] == 1
    assert len(tasks.tasks) == 1


def test_failure_refunds_once(reel_db):
    conn, request, user = reel_db
    job = routes.queue_render(request, BackgroundTasks(), user)
    billing.refund_reel(job["job_id"])
    billing.refund_reel(job["job_id"])
    assert conn.execute("SELECT credits FROM user_credits").fetchone()[0] == 100
    assert conn.execute("SELECT COUNT(*) FROM credit_transactions WHERE transaction_type='refund'").fetchone()[0] == 1


def test_insufficient_balance_does_not_create_job(reel_db):
    conn, request, user = reel_db
    conn.execute("UPDATE user_credits SET credits=2")
    conn.commit()
    with pytest.raises(HTTPException) as error:
        routes.queue_render(request, BackgroundTasks(), user)
    assert error.value.status_code == 402
    assert conn.execute("SELECT COUNT(*) FROM reel_render_jobs").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM credit_transactions").fetchone()[0] == 0


def test_changed_price_requires_new_confirmation(reel_db, monkeypatch):
    conn, request, user = reel_db
    monkeypatch.setattr(routes, "reel_pricing", lambda _: {"credit_cost": 30, "credits": 100})
    with pytest.raises(HTTPException) as error:
        routes.queue_render(request, BackgroundTasks(), user)
    assert error.value.status_code == 409
    assert conn.execute("SELECT credits FROM user_credits").fetchone()[0] == 100


def test_unconfigured_renderer_does_not_charge(reel_db, monkeypatch):
    conn, request, user = reel_db
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("PARTNER_PORTRAIT_OPENAI_API_KEY", raising=False)
    with pytest.raises(HTTPException) as error:
        routes.queue_render(request, BackgroundTasks(), user)
    assert error.value.status_code == 503
    assert conn.execute("SELECT credits FROM user_credits").fetchone()[0] == 100


def test_reel_pricing_uses_shared_admin_and_vip_rates(monkeypatch):
    calls = []
    monkeypatch.setattr(billing, "credit_service", SimpleNamespace(
        get_credit_setting=lambda key: calls.append(key) or 25,
        get_effective_cost=lambda uid, base, key: 20,
        get_user_credits=lambda uid: 75,
    ))
    assert billing.reel_pricing(18) == {"credit_cost": 20, "credits": 75}
    assert calls == ["reel_generation_cost"]


def test_job_insert_failure_rolls_back_charge(reel_db, monkeypatch):
    conn, request, user = reel_db
    original = routes.execute
    def broken_insert(connection, sql, args=()):
        if "INSERT INTO reel_render_jobs" in sql:
            raise RuntimeError("Job write failed")
        return original(connection, sql, args)
    monkeypatch.setattr(routes, "execute", broken_insert)
    with pytest.raises(RuntimeError, match="Job write failed"):
        routes.queue_render(request, BackgroundTasks(), user)
    assert conn.execute("SELECT credits FROM user_credits").fetchone()[0] == 100
    assert conn.execute("SELECT COUNT(*) FROM credit_transactions").fetchone()[0] == 0
