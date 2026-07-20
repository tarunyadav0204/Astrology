from datetime import datetime, timezone

from nudge_engine import db


class _Cursor:
    def __init__(self, *, one=None, all_rows=None):
        self._one = one
        self._all = all_rows or []

    def fetchone(self):
        return self._one

    def fetchall(self):
        return self._all


def test_campaign_question_funnel_returns_summary_and_recipients(monkeypatch):
    sent_at = datetime(2026, 7, 20, 5, 30, tzinfo=timezone.utc)
    asked_at = datetime(2026, 7, 20, 7, 0, tzinfo=timezone.utc)
    calls = []
    cursors = iter(
        [
            _Cursor(one=(3, 2, 1, 1, 1, 2, 1)),
            _Cursor(one=(3,)),
            _Cursor(
                all_rows=[
                    (
                        101,
                        "Asha",
                        "9999999999",
                        sent_at,
                        "push",
                        True,
                        True,
                        asked_at,
                        2,
                        1.5,
                        True,
                    )
                ]
            ),
        ]
    )

    def fake_execute(_conn, sql, params):
        calls.append((sql, params))
        return next(cursors)

    monkeypatch.setattr(db, "execute", fake_execute)
    result = db.campaign_question_funnel(
        object(), 12, window_days=7, page=1, page_size=50
    )

    assert result["campaign_id"] == 12
    assert result["window_days"] == 7
    assert result["summary"]["targeted"] == 3
    assert result["summary"]["asked"] == 1
    assert result["summary"]["asked_rate"] == 0.3333
    assert result["summary"]["delivered_asked_rate"] == 0.5
    assert result["items"][0] == {
        "user_id": 101,
        "name": "Asha",
        "phone": "9999999999",
        "delivered_at": sent_at.isoformat(),
        "channel": "push",
        "channel_delivered": True,
        "clicked": True,
        "first_question_at": asked_at.isoformat(),
        "questions_in_window": 2,
        "hours_to_first_question": 1.5,
        "tap_attributed": True,
    }
    assert calls[0][1] == (12, "7")
    assert calls[2][1] == (12, "7", 50, 0)


def test_campaign_question_funnel_applies_not_asked_filter_and_limits(monkeypatch):
    calls = []
    cursors = iter(
        [
            _Cursor(one=(0, 0, 0, 0, 0, 0, 0)),
            _Cursor(one=(0,)),
            _Cursor(all_rows=[]),
        ]
    )

    def fake_execute(_conn, sql, params):
        calls.append((sql, params))
        return next(cursors)

    monkeypatch.setattr(db, "execute", fake_execute)
    result = db.campaign_question_funnel(
        object(), 5, window_days=90, page=2, page_size=500, asked=False
    )

    assert result["window_days"] == 30
    assert result["page_size"] == 200
    assert result["page"] == 2
    assert "WHERE first_question_at IS NULL" in calls[1][0]
    assert calls[2][1] == (5, "30", 200, 200)
