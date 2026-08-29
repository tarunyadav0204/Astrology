from credits.instant_billing import (
    LOW_BALANCE_MINUTES,
    _payload,
    _settlement_billable_seconds,
)


def _session_row(*, billed_minutes=1, billable_seconds=0):
    return (
        "instant_test", 30, "chat_test", "client_test", "active",
        2, 2, 0, 3, 3, 20, 3 + max(0, billed_minutes - 1) * 2,
        billed_minutes, billable_seconds, "2026-08-15 10:00:00", None, None,
        0, billable_seconds,
    )


def test_payload_counts_paid_minute_and_wallet_time():
    state = _payload(_session_row(billed_minutes=1, billable_seconds=10), balance=8)

    assert state["remaining_seconds"] == 50 + (4 * 60)
    assert state["balance"] == 8
    assert state["billed_minutes"] == 1
    assert state["first_minute_cost"] == 3
    assert state["following_minute_cost"] == 2


def test_low_balance_only_below_five_minutes_worth():
    threshold_seconds = LOW_BALANCE_MINUTES * 60
    at_threshold = _payload(
        _session_row(billed_minutes=1, billable_seconds=60),
        balance=LOW_BALANCE_MINUTES * 2,
    )
    below_threshold = _payload(
        _session_row(billed_minutes=1, billable_seconds=1),
        balance=(LOW_BALANCE_MINUTES - 1) * 2,
    )

    assert at_threshold["remaining_seconds"] == threshold_seconds
    assert at_threshold["low_balance"] is False
    assert below_threshold["remaining_seconds"] < threshold_seconds
    assert below_threshold["low_balance"] is True


def test_disconnected_session_does_not_bill_reconnect_grace():
    assert _settlement_billable_seconds(
        prior=58,
        total=140,
        disconnected=True,
    ) == 58


def test_connected_session_uses_server_elapsed_time():
    assert _settlement_billable_seconds(
        prior=58,
        total=68,
        disconnected=False,
    ) == 68
