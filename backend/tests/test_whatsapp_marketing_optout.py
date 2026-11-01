from unittest.mock import patch

from whatsapp.handlers import (
    _set_whatsapp_marketing_preference,
    _whatsapp_marketing_preference_command,
)


class _Connection:
    def __init__(self):
        self.commits = 0

    def commit(self):
        self.commits += 1


def test_stop_and_start_commands_are_exact_but_tolerate_common_punctuation():
    assert _whatsapp_marketing_preference_command(" STOP! ") is True
    assert _whatsapp_marketing_preference_command("opt out") is True
    assert _whatsapp_marketing_preference_command("START") is False
    assert _whatsapp_marketing_preference_command("please stop sending these") is None


def test_stop_persists_against_linked_whatsapp_user():
    conn = _Connection()
    with (
        patch("whatsapp.handlers._find_user_by_wa_id", return_value=(42,)),
        patch("whatsapp.handlers.execute") as execute,
    ):
        assert _set_whatsapp_marketing_preference(conn, "919900000000", None, True) is True

    assert "whatsapp_marketing_opted_out_at = CURRENT_TIMESTAMP" in execute.call_args.args[1]
    assert execute.call_args.args[2] == (42,)
    assert conn.commits == 1


def test_start_clears_existing_preference():
    conn = _Connection()
    with patch("whatsapp.handlers.execute") as execute:
        assert _set_whatsapp_marketing_preference(conn, "919900000000", 42, False) is True

    assert "whatsapp_marketing_opted_out_at = NULL" in execute.call_args.args[1]
    assert execute.call_args.args[2] == (42,)
