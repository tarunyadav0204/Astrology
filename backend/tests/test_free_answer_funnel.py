from credits.free_answer_funnel import (
    VALID_EVENTS,
    _inclusive_date_clause,
    get_funnel_analytics,
    mark_converted_after_purchase,
    record_funnel_event,
)


def test_free_answer_funnel_valid_events():
    assert VALID_EVENTS == frozenset({"blur_shown", "reveal_clicked", "converted"})


def test_free_answer_funnel_record_invalid_event():
    try:
        record_funnel_event(userid=1, event_name="invalid")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_inclusive_date_clause():
    clauses, params = _inclusive_date_clause("2026-06-24", "2026-07-24", "cm.completed_at")
    assert clauses == [
        "(cm.completed_at AT TIME ZONE 'Asia/Kolkata')::date >= ?::date",
        "(cm.completed_at AT TIME ZONE 'Asia/Kolkata')::date <= ?::date",
    ]
    assert params == ["2026-06-24", "2026-07-24"]


def test_get_funnel_analytics_shape_without_db(monkeypatch):
    class FakeCur:
        def fetchone(self):
            return (0, 0)

    class FakeConn:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def rollback(self):
            return None

    def fake_execute(conn, sql, params=None):
        assert "free_answer_funnel_events" in sql
        return FakeCur()

    monkeypatch.setattr("credits.free_answer_funnel.get_conn", FakeConn)
    monkeypatch.setattr("credits.free_answer_funnel.execute", fake_execute)
    monkeypatch.setattr("credits.free_answer_funnel.ensure_free_answer_funnel_table", lambda conn: None)

    out = get_funnel_analytics(from_date="2026-07-24", to_date="2026-07-24")
    assert out["from_date"] == "2026-07-24"
    assert out["to_date"] == "2026-07-24"
    assert out["timezone"] == "Asia/Kolkata"
    assert out["impression_source"] == "free_answer_funnel_events.blur_shown"
    assert [s["event_name"] for s in out["steps"]] == [
        "blur_shown",
        "reveal_clicked",
        "converted",
    ]


def test_purchase_converts_only_the_most_recent_reveal(monkeypatch):
    calls = []

    class FakeCur:
        def __init__(self, row=None):
            self.row = row

        def fetchone(self):
            return self.row

    class FakeConn:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def commit(self):
            calls.append(("commit",))

    def fake_execute(conn, sql, params=None):
        normalized = " ".join(sql.split())
        calls.append((normalized, params))
        if "ORDER BY created_at DESC" in normalized:
            return FakeCur(("latest-message",))
        if "SELECT 1 FROM free_answer_funnel_events" in normalized:
            return FakeCur(None)
        return FakeCur()

    monkeypatch.setattr("credits.free_answer_funnel.get_conn", FakeConn)
    monkeypatch.setattr("credits.free_answer_funnel.execute", fake_execute)
    monkeypatch.setattr("credits.free_answer_funnel.ensure_free_answer_funnel_table", lambda conn: None)

    inserted = mark_converted_after_purchase(73)

    assert inserted == 1
    insert_calls = [call for call in calls if call[0].startswith("INSERT INTO")]
    assert len(insert_calls) == 1
    assert insert_calls[0][1] == (73, "latest-message")
