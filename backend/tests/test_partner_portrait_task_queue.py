from partner_profile import task_queue


def _clear_task_env(monkeypatch):
    for name in (
        "PARTNER_PORTRAIT_TASKS_ENABLED",
        "PARTNER_PORTRAIT_TASKS_PROJECT",
        "PARTNER_PORTRAIT_TASKS_LOCATION",
        "PARTNER_PORTRAIT_TASKS_QUEUE",
        "PARTNER_PORTRAIT_TASKS_TARGET_BASE_URL",
        "PARTNER_PORTRAIT_TASKS_SECRET",
        "REPORT_TASKS_PROJECT",
        "REPORT_TASKS_LOCATION",
        "REPORT_TASKS_QUEUE",
        "REPORT_TASKS_TARGET_BASE_URL",
        "REPORT_TASKS_SECRET",
        "CHAT_TASKS_PROJECT",
        "CHAT_TASKS_LOCATION",
        "CHAT_TASKS_QUEUE",
        "CHAT_TASKS_TARGET_BASE_URL",
        "CHAT_TASKS_SECRET",
        "GOOGLE_CLOUD_PROJECT",
        "GCP_PROJECT_ID",
        "PUBLIC_API_BASE_URL",
    ):
        monkeypatch.delenv(name, raising=False)


def test_disabled_queue_reports_configuration_error(monkeypatch):
    _clear_task_env(monkeypatch)

    assert task_queue.task_configuration_error() == "worker queue is not enabled"


def test_queue_uses_existing_chat_settings_as_safe_fallback(monkeypatch):
    _clear_task_env(monkeypatch)
    monkeypatch.setenv("PARTNER_PORTRAIT_TASKS_ENABLED", "true")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "project-1")
    monkeypatch.setenv("CHAT_TASKS_LOCATION", "asia-south1")
    monkeypatch.setenv("CHAT_TASKS_QUEUE", "chat-standard-queue")
    monkeypatch.setenv("CHAT_TASKS_TARGET_BASE_URL", "https://example.test")
    monkeypatch.setenv("CHAT_TASKS_SECRET", "secret")

    assert task_queue.task_configuration_error() is None
    assert task_queue._task_settings() == {
        "project": "project-1",
        "location": "asia-south1",
        "queue": "chat-standard-queue",
        "target": "https://example.test",
        "secret": "secret",
    }


def test_default_location_is_a_supported_cloud_tasks_region(monkeypatch):
    _clear_task_env(monkeypatch)
    monkeypatch.setenv("PARTNER_PORTRAIT_TASKS_ENABLED", "true")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "project-1")
    monkeypatch.setenv("PARTNER_PORTRAIT_TASKS_SECRET", "secret")

    assert task_queue._task_settings()["location"] == "asia-south1"
    assert task_queue.task_configuration_error() is None
