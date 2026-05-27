from chat_history import task_queue


def test_chat_tasks_disabled_by_default(monkeypatch):
    monkeypatch.delenv("CHAT_TASKS_ENABLED", raising=False)

    assert task_queue.chat_tasks_enabled() is False
    assert task_queue.enqueue_chat_processing_task(message_id=1, payload={}) is False


def test_chat_task_secret_prefers_dedicated_secret(monkeypatch):
    monkeypatch.setenv("CHAT_TASKS_SECRET", "chat-secret")
    monkeypatch.setenv("NUDGE_CRON_SECRET", "nudge-secret")

    assert task_queue.chat_task_secret() == "chat-secret"


def test_chat_task_secret_falls_back_to_nudge_secret(monkeypatch):
    monkeypatch.delenv("CHAT_TASKS_SECRET", raising=False)
    monkeypatch.setenv("NUDGE_CRON_SECRET", "nudge-secret")

    assert task_queue.chat_task_secret() == "nudge-secret"
