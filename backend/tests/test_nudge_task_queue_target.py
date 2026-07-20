from nudge_engine import task_queue


def test_https_worker_target_is_preserved(monkeypatch):
    monkeypatch.setenv("NUDGE_TASKS_TARGET_BASE_URL", "https://worker.example.com/")
    monkeypatch.delenv("NUDGE_CLOUD_RUN_WORKER_URL", raising=False)

    assert task_queue.nudge_tasks_target_base_url() == "https://worker.example.com"


def test_legacy_http_target_uses_cloud_run_fallback(monkeypatch):
    monkeypatch.setenv("NUDGE_TASKS_TARGET_BASE_URL", "http://34.131.10.82:8001")
    monkeypatch.setenv(
        "NUDGE_CLOUD_RUN_WORKER_URL",
        "https://current-worker.example.com/",
    )

    assert task_queue.nudge_tasks_target_base_url() == "https://current-worker.example.com"
    assert task_queue.nudge_tasks_are_isolated() is True


def test_missing_target_uses_stable_cloud_run_worker(monkeypatch):
    monkeypatch.delenv("NUDGE_TASKS_TARGET_BASE_URL", raising=False)
    monkeypatch.delenv("CHAT_TASKS_TARGET_BASE_URL", raising=False)
    monkeypatch.delenv("NUDGE_CLOUD_RUN_WORKER_URL", raising=False)

    assert (
        task_queue.nudge_tasks_target_base_url()
        == task_queue.DEFAULT_NUDGE_WORKER_TARGET_BASE_URL
    )
