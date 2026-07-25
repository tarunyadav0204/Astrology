import asyncio

from auth import User
from nudge_engine import db
from nudge_engine.conversions import record_nudge_conversion
from nudge_engine.routes import NudgeClickRequest, record_nudge_click


class _Cursor:
    rowcount = 1


class _Conn:
    def __init__(self):
        self.committed = False

    def commit(self):
        self.committed = True


class _ConnContext:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self.conn

    def __exit__(self, *_args):
        return False


def test_mark_delivery_clicked_can_be_scoped_to_the_authenticated_user(monkeypatch):
    calls = []

    def fake_execute(_conn, sql, params):
        calls.append((sql, params))
        return _Cursor()

    monkeypatch.setattr(db, "execute", fake_execute)

    updated = db.mark_delivery_clicked(object(), "abc123", userid=42)

    assert updated == 1
    assert "AND userid = %s" in calls[0][0]
    assert calls[0][1] == ("abc123", 42)


def test_authenticated_click_endpoint_records_only_the_current_users_delivery(monkeypatch):
    conn = _Conn()
    recorded = []
    monkeypatch.setattr(db, "get_conn", lambda: _ConnContext(conn))
    monkeypatch.setattr(db, "init_nudge_tables", lambda _conn: None)
    monkeypatch.setattr(
        db,
        "mark_delivery_clicked",
        lambda _conn, group_id, *, userid=None: recorded.append((group_id, userid)) or 1,
    )

    result = asyncio.run(
        record_nudge_click(
            NudgeClickRequest(nudge_id="abc123"),
            User(userid=42, name="Asha", phone="9999999999", role="user"),
        )
    )

    assert result == {"ok": True, "recorded": True}
    assert recorded == [("abc123", 42)]
    assert conn.committed is True


def test_question_attribution_also_backfills_click_for_older_clients(monkeypatch):
    clicked = []
    monkeypatch.setattr(
        db,
        "find_primary_delivery_by_group",
        lambda *_args: {
            "userid": 42,
            "campaign_id": 12,
            "trigger_id": "campaign_12",
            "created_at": None,
        },
    )
    monkeypatch.setattr(
        db,
        "mark_delivery_clicked",
        lambda _conn, group_id, *, userid=None: clicked.append((group_id, userid)) or 1,
    )
    monkeypatch.setattr(db, "insert_conversion", lambda *_args, **_kwargs: True)

    assert record_nudge_conversion(
        object(),
        delivery_group_id="abc123",
        userid=42,
        question="What does this mean for me?",
    )
    assert clicked == [("abc123", 42)]
