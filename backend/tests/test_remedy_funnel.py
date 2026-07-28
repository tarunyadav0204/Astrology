from credits.remedy_funnel import VALID_EVENTS, _inclusive_date_clause, get_funnel_analytics, record_funnel_event


def test_remedy_funnel_valid_events():
    assert VALID_EVENTS == frozenset({"card_shown", "card_clicked", "remedy_delivered"})


def test_remedy_funnel_record_invalid_event():
    try:
        record_funnel_event(userid=1, event_name="invalid")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_card_shown_is_normalized_to_one_user_day_and_runs_no_ddl(monkeypatch):
    statements = []
    inserted_params = []

    class FakeCur:
        def fetchone(self):
            return (123,)

    class FakeConn:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def commit(self):
            return None

        def rollback(self):
            return None

    def fake_execute(_conn, sql, params=None):
        statements.append(sql)
        inserted_params.append(tuple(params or ()))
        return FakeCur()

    monkeypatch.setattr("credits.remedy_funnel.get_conn", FakeConn)
    monkeypatch.setattr("credits.remedy_funnel.execute", fake_execute)

    assert record_funnel_event(
        userid=18,
        event_name="card_shown",
        message_id="answer-1",
        platform="web",
    )
    assert len(statements) == 1
    assert "CREATE TABLE" not in statements[0]
    assert "CREATE INDEX" not in statements[0]
    assert inserted_params[0][1].startswith("chat_screen:")


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
        assert "remedy_funnel_events" in sql
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
    assert out["timezone"] == "Asia/Kolkata"
    assert out["impression_source"] == "remedy_funnel_events.card_shown"
    assert [s["event_name"] for s in out["steps"]] == [
        "card_shown",
        "card_clicked",
        "remedy_delivered",
    ]
