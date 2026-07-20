from nudge_engine import db


class _Cursor:
    def __init__(self, *, one=None, all_rows=None):
        self._one = one
        self._all = all_rows or []

    def fetchone(self):
        return self._one

    def fetchall(self):
        return self._all


def test_delivery_channel_counts_escapes_literal_percent_for_psycopg(monkeypatch):
    calls = []

    def fake_execute(_conn, sql, params):
        calls.append((sql, params))
        return _Cursor(one=(4, 3, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0))

    monkeypatch.setattr(db, "execute", fake_execute)
    counts = db._delivery_channel_counts(
        object(),
        "sent_at >= %s AND sent_at <= %s",
        ("2026-07-20", "2026-07-20"),
    )

    sql, params = calls[0]
    assert 'LIKE \'%%"from_template_continue": true%%\'' in sql
    assert 'NOT LIKE \'%%"from_template_continue": true%%\'' in sql
    assert params == ("2026-07-20", "2026-07-20")
    assert counts["targeted"] == 4
    assert counts["push"] == 3


def test_overview_stats_shapes_today_results(monkeypatch):
    monkeypatch.setattr(
        db,
        "_delivery_channel_counts",
        lambda *_args: {"targeted": 3, "push": 3},
    )
    monkeypatch.setattr(
        db,
        "_conversion_summary",
        lambda *_args: {
            "conversions": 1,
            "time_buckets": {"under_5m": 1},
            "median_seconds": 120,
        },
    )
    monkeypatch.setattr(db, "_conversions_by_channel", lambda *_args: {"push": 1})
    cursors = iter(
        [
            _Cursor(all_rows=[("campaign_12", 12, 3, 3, 0, 0)]),
            _Cursor(all_rows=[("campaign_12", 12, 1)]),
        ]
    )
    monkeypatch.setattr(db, "execute", lambda *_args: next(cursors))

    result = db.overview_stats(object(), "2026-07-20", "2026-07-20")

    assert result["conversion_rate"] == 0.3333
    assert result["by_source"] == [
        {
            "trigger_id": "campaign_12",
            "campaign_id": 12,
            "targeted": 3,
            "push": 3,
            "whatsapp": 0,
            "email": 0,
            "conversions": 1,
        }
    ]
