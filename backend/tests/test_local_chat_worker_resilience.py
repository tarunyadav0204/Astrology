import chat_history.local_worker as local_worker


def test_worker_retries_when_database_poll_temporarily_fails(monkeypatch):
    calls = {"claim": 0, "sleep": 0}

    monkeypatch.setattr(local_worker, "chat_task_secret", lambda: "secret")
    monkeypatch.setattr(local_worker, "_poll_interval_seconds", lambda: 0.01)

    def claim():
        calls["claim"] += 1
        if calls["claim"] == 1:
            raise RuntimeError("database temporarily unavailable")
        raise KeyboardInterrupt

    monkeypatch.setattr(local_worker, "claim_next_local_chat_task", claim)
    monkeypatch.setattr(
        local_worker.time,
        "sleep",
        lambda _seconds: calls.__setitem__("sleep", calls["sleep"] + 1),
    )

    try:
        local_worker.run_forever()
    except KeyboardInterrupt:
        pass

    assert calls == {"claim": 2, "sleep": 1}
