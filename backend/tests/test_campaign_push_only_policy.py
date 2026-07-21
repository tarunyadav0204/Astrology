from unittest.mock import patch

from nudge_engine.campaigns import ALLOWED_POLICIES, filter_push_reachable_user_ids
from nudge_engine.delivery import deliver_nudge


class _Rows:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


def test_push_only_is_a_supported_campaign_policy():
    assert "push_only" in ALLOWED_POLICIES


def test_push_only_audience_keeps_only_users_with_device_tokens():
    with patch("nudge_engine.campaigns.execute", return_value=_Rows([(2,), (4,)])):
        assert filter_push_reachable_user_ids(object(), [1, 2, 3, 4]) == [2, 4]


def test_push_only_delivery_never_attempts_whatsapp_or_email():
    inserted = []
    with (
        patch("nudge_engine.delivery._attempt_push", return_value=True) as push,
        patch("nudge_engine.delivery._attempt_whatsapp") as whatsapp,
        patch("nudge_engine.delivery._attempt_email") as email,
        patch(
            "nudge_engine.delivery.db.insert_delivery",
            side_effect=lambda *_args, **kwargs: inserted.append(kwargs),
        ),
    ):
        result = deliver_nudge(
            object(),
            userid=42,
            trigger_id="campaign_7",
            title="Title",
            body="Body",
            policy="push_only",
            channels=["push", "whatsapp", "email"],
            campaign_id=7,
        )

    push.assert_called_once()
    whatsapp.assert_not_called()
    email.assert_not_called()
    assert result["channels_sent"] == ["push"]
    assert [row["channel"] for row in inserted] == ["push"]

