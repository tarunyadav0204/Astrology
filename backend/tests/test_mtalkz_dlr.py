from unittest.mock import Mock

from nudge_engine import mtalkz_dlr


def test_parse_direct_mtalkz_failure_report():
    assert mtalkz_dlr.parse_mtalkz_dlr({
        "messageId": "mtalkz-123",
        "deliveryStatus": "PREFERENCE_NOT_MATCHED",
        "reason": "DND preference does not allow this message",
    }) == [{
        "message_id": "mtalkz-123",
        "status": "failed",
        "error": "DND preference does not allow this message",
    }]


def test_parse_wrapped_mtalkz_delivered_reports():
    assert mtalkz_dlr.parse_mtalkz_dlr({"data": [
        {"id": "mtalkz-1", "status": "DELIVERED"},
        {"id": "mtalkz-2", "status": "submitted"},
    ]}) == [
        {"message_id": "mtalkz-1", "status": "delivered", "error": ""},
        {"message_id": "mtalkz-2", "status": "sent", "error": ""},
    ]


def test_apply_matches_only_the_provider_message_id(monkeypatch):
    cursor = Mock(rowcount=1)
    execute = Mock(return_value=cursor)
    monkeypatch.setattr(mtalkz_dlr, "execute", execute)

    assert mtalkz_dlr.apply_mtalkz_dlr(Mock(), {
        "message_id": "mtalkz-123", "status": "failed", "error": "PREFERENCE_NOT_MATCHED",
    }) == 1

    sql, params = execute.call_args.args[1], execute.call_args.args[2]
    assert "WHERE channel = 'sms' AND meta_message_id = %s" in sql
    assert params[-1] == "mtalkz-123"
    assert "PREFERENCE_NOT_MATCHED" in params
