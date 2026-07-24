from credits.free_answer_funnel import VALID_EVENTS, _date_clause, get_funnel_analytics, record_funnel_event


def test_free_answer_funnel_valid_events():
    assert VALID_EVENTS == frozenset({"blur_shown", "reveal_clicked", "converted"})


def test_free_answer_funnel_record_invalid_event():
    try:
        record_funnel_event(userid=1, event_name="invalid")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_date_clause_ist_inclusive():
    clauses, params = _date_clause("2026-06-24", "2026-07-24", "s.created_at")
    assert len(clauses) == 2
    assert "Asia/Kolkata" in clauses[0]
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

    def fake_execute(conn, sql, params=None):
        return FakeCur()

    monkeypatch.setattr("credits.free_answer_funnel.get_conn", FakeConn)
    monkeypatch.setattr("credits.free_answer_funnel.execute", fake_execute)
    monkeypatch.setattr("credits.free_answer_funnel.ensure_free_answer_funnel_table", lambda conn: None)

    out = get_funnel_analytics(from_date="2026-06-24", to_date="2026-07-24")
    assert out["from_date"] == "2026-06-24"
    assert out["to_date"] == "2026-07-24"
    assert [s["event_name"] for s in out["steps"]] == [
        "blur_shown",
        "reveal_clicked",
        "converted",
    ]
    assert all(s["unique_users"] == 0 for s in out["steps"])
    assert out["reveal_to_purchase_pct"] is None
