import base64
import os

from utils.account_deletion_bigquery import (
    decode_backup_payload,
    merge_account_deletion_payloads,
    split_account_deletion_backup_rows,
)


def _snapshot(message_count, message_size):
    return {
        "schema_version": 1,
        "userid": 33,
        "row_counts": {"users": 1, "chat_messages": message_count},
        "tables": {
            "users": [{"userid": 33, "phone": "999", "name": "Ada", "email": "ada@example.com", "signup_client": "android"}],
            "chat_messages": [
                {"message_id": index, "content": "x" * message_size}
                for index in range(message_count)
            ],
        },
    }


def test_small_account_backup_stays_one_row():
    rows = split_account_deletion_backup_rows(
        _snapshot(2, 20),
        deletion_id="acctdel_33_test",
        deleted_at="2026-09-23T00:00:00+00:00",
        deleted_by_userid=33,
        deletion_source="self_service",
        max_bytes=50_000,
    )
    assert len(rows) == 1
    assert "_use_load_job" not in rows[0]
    assert rows[0]["user_phone"] == "999"


def test_repetitive_chat_backup_stays_one_compressed_row():
    rows = split_account_deletion_backup_rows(
        _snapshot(8, 4000),
        deletion_id="acctdel_33_test",
        deleted_at="2026-09-23T00:00:00+00:00",
        deleted_by_userid=33,
        deletion_source="self_service",
        max_bytes=8_500_000,
    )
    assert len(rows) == 1
    assert rows[0]["backup_payload"].startswith("gz1:")
    assert len(rows[0]["backup_payload"]) < 8_500_000


def test_large_account_backup_splits_under_streaming_limit_and_rejoins():
    noisy = _snapshot(4, 20)
    noisy["tables"]["chat_messages"] = [
        {"message_id": index, "content": base64.b64encode(os.urandom(700)).decode("ascii")}
        for index in range(4)
    ]
    rows = split_account_deletion_backup_rows(
        noisy,
        deletion_id="acctdel_33_test",
        deleted_at="2026-09-23T00:00:00+00:00",
        deleted_by_userid=33,
        deletion_source="self_service",
        max_bytes=2200,
    )
    assert len(rows) > 1
    for row in rows:
        assert len(row["backup_payload"].encode("utf-8")) < 2200 or row.get("_use_load_job")
        assert row["deletion_id"] == "acctdel_33_test"
        assert row["user_phone"] == "999"
        assert row["userid"] == 33

    merged = merge_account_deletion_payloads([
        decode_backup_payload(row["backup_payload"]) for row in reversed(rows)
    ])
    assert "_part" not in merged
    assert [item["message_id"] for item in merged["tables"]["chat_messages"]] == list(range(4))
    assert merged["tables"]["users"][0]["phone"] == "999"
    assert merged["row_counts"]["chat_messages"] == 4
