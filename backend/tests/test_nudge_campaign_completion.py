"""Campaign completion must be serialized across concurrent batch workers."""
from unittest.mock import patch

from nudge_engine import db


class _Cursor:
    def __init__(self, row):
        self._row = row

    def fetchone(self):
        return self._row


def test_refresh_campaign_status_locks_before_counting_progress():
    calls = []

    def fake_execute(_conn, sql, _params=()):
        calls.append(" ".join(sql.split()))
        return _Cursor((12, "sending"))

    progress = {
        "processed": 12,
        "delivered": 12,
        "undelivered": 0,
        "failed_attempts": 0,
    }
    with (
        patch.object(db, "execute", side_effect=fake_execute),
        patch.object(db, "campaign_delivery_progress", return_value=progress),
        patch.object(db, "update_campaign") as update_campaign,
    ):
        assert db.refresh_campaign_delivery_status(object(), 63) == progress

    assert calls[0].endswith("WHERE id = %s FOR UPDATE")
    update_campaign.assert_called_once()
    assert update_campaign.call_args.args[1] == 63
    assert update_campaign.call_args.kwargs["status"] == "sent"
