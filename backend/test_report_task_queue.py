from reports import task_queue


def test_report_task_secret_prefers_dedicated_secret(monkeypatch):
    monkeypatch.setenv("REPORT_TASKS_SECRET", "report-secret")
    monkeypatch.setenv("CHAT_TASKS_SECRET", "chat-secret")
    monkeypatch.setenv("NUDGE_CRON_SECRET", "nudge-secret")

    assert task_queue.report_task_secret() == "report-secret"


def test_report_task_secret_falls_back_to_chat_secret(monkeypatch):
    monkeypatch.delenv("REPORT_TASKS_SECRET", raising=False)
    monkeypatch.setenv("CHAT_TASKS_SECRET", "chat-secret")
    monkeypatch.setenv("NUDGE_CRON_SECRET", "nudge-secret")

    assert task_queue.report_task_secret() == "chat-secret"


def test_report_target_falls_back_to_chat_target(monkeypatch):
    monkeypatch.delenv("REPORT_TASKS_TARGET_BASE_URL", raising=False)
    monkeypatch.setenv("CHAT_TASKS_TARGET_BASE_URL", "https://worker.example.com")
    monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.example.com")

    assert task_queue._target_base_url() == "https://worker.example.com"
