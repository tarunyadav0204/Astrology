from credits.remedy_funnel import VALID_EVENTS, _inclusive_date_clause, get_funnel_analytics, record_funnel_event


def test_remedy_funnel_valid_events():
    assert VALID_EVENTS == frozenset({"card_shown", "card_clicked", "remedy_delivered"})


def test_remedy_funnel_record_invalid_event():
    try:
        record_funnel_event(userid=1, event_name="invalid")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_inclusive_date_clause():
    clauses, params = _inclusive_date_clause("2026-06-24", "2026-07-24", "cm.completed_at")
    assert clauses == ["date(cm.completed_at) >= ?", "date(cm.completed_at) <= ?"]
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
        assert "chat_messages" in sql
        assert "from_date" not in sql  # params, not interpolated
        if params:
            assert "2026-07-24" in params or "card_clicked" in params or "remedy_delivered" in params
        return FakeCur()

    monkeypatch.setattr("credits.remedy_funnel.get_conn", FakeConn)
    monkeypatch.setattr("credits.remedy_funnel.execute", fake_execute)
    monkeypatch.setattr("credits.remedy_funnel.ensure_remedy_funnel_table", lambda conn: None)

    out = get_funnel_analytics(from_date="2026-07-24", to_date="2026-07-24")
    assert out["from_date"] == "2026-07-24"
    assert out["to_date"] == "2026-07-24"
    assert out["impression_source"] == "chat_messages.next_action"
    assert [s["event_name"] for s in out["steps"]] == [
        "card_shown",
        "card_clicked",
        "remedy_delivered",
    ]
