from chat_history import routes


class _Cursor:
    def __init__(self, rowcount=0):
        self.rowcount = rowcount


def test_delete_all_chat_history_is_scoped_to_authenticated_user(monkeypatch):
    statements = []

    def fake_execute(_conn, sql, params=None):
        normalized = " ".join(sql.split())
        statements.append((normalized, params))
        if normalized.startswith(("SAVEPOINT", "RELEASE SAVEPOINT", "ROLLBACK TO SAVEPOINT")):
            return _Cursor()
        if normalized.startswith("DELETE FROM chat_messages"):
            return _Cursor(8)
        if normalized.startswith("DELETE FROM chat_sessions"):
            return _Cursor(3)
        if normalized.startswith("DELETE FROM conversation_state"):
            return _Cursor(3)
        return _Cursor(1)

    monkeypatch.setattr(routes, "execute", fake_execute)

    result = routes._delete_all_chat_history_tx(object(), 42)

    assert result["deleted_messages"] == 8
    assert result["deleted_sessions"] == 3
    assert result["deleted_conversation_states"] == 3

    delete_statements = [
        (sql, params)
        for sql, params in statements
        if sql.startswith("DELETE FROM")
    ]
    assert delete_statements
    assert all(params == (42,) for _, params in delete_statements)
    assert any(
        sql == "DELETE FROM chat_sessions WHERE user_id = %s"
        for sql, _ in delete_statements
    )
    assert any(
        "DELETE FROM chat_messages WHERE session_id IN "
        "(SELECT session_id FROM chat_sessions WHERE user_id = %s)" in sql
        for sql, _ in delete_statements
    )


def test_missing_optional_history_table_does_not_block_core_deletion(monkeypatch):
    statements = []

    def fake_execute(_conn, sql, params=None):
        normalized = " ".join(sql.split())
        statements.append(normalized)
        if normalized.startswith("DELETE FROM podcast_history"):
            raise RuntimeError("relation does not exist")
        if normalized.startswith("DELETE FROM chat_messages"):
            return _Cursor(4)
        if normalized.startswith("DELETE FROM chat_sessions"):
            return _Cursor(2)
        return _Cursor()

    monkeypatch.setattr(routes, "execute", fake_execute)

    result = routes._delete_all_chat_history_tx(object(), 7)

    assert "ROLLBACK TO SAVEPOINT sp_clear_chat_podcasts" in statements
    assert result["deleted_podcast_history"] == 0
    assert result["deleted_messages"] == 4
    assert result["deleted_sessions"] == 2
