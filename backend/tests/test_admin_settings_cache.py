from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from utils import admin_settings


def _reset_cache() -> None:
    with admin_settings._ADMIN_SETTINGS_REFRESH_LOCK:
        with admin_settings._ADMIN_SETTINGS_CACHE_LOCK:
            admin_settings._ADMIN_SETTINGS_CACHE.clear()
            admin_settings._ADMIN_SETTINGS_CACHE_EXPIRES_AT = 0.0
            admin_settings._ADMIN_SETTINGS_CACHE_LOADED = False
        admin_settings._LAST_ADMIN_SETTINGS_VERSION = None
        admin_settings._LAST_CREDITS_SETTINGS_VERSION = None


@pytest.fixture(autouse=True)
def reset_admin_settings_cache(monkeypatch):
    _reset_cache()
    monkeypatch.setattr(admin_settings, "ADMIN_SETTINGS_CACHE_TTL_SECONDS", 60)
    monkeypatch.setattr(admin_settings, "ADMIN_SETTINGS_CACHE_RETRY_SECONDS", 5)
    yield
    _reset_cache()


def test_multiple_keys_share_one_bulk_database_read(monkeypatch):
    reads = 0

    def read_rows():
        nonlocal reads
        reads += 1
        return [
            ("feature_a", "true", "A"),
            ("feature_b", "18,73", "B"),
        ]

    monkeypatch.setattr(
        admin_settings,
        "_read_admin_settings_rows_from_db",
        read_rows,
    )

    assert admin_settings.get_setting("feature_a") == "true"
    assert admin_settings.get_setting("feature_b") == "18,73"
    assert admin_settings.get_setting("missing") is None
    assert reads == 1


def test_snapshot_refresh_is_single_flight_across_threads(monkeypatch):
    reads = 0
    count_lock = threading.Lock()

    def read_rows():
        nonlocal reads
        with count_lock:
            reads += 1
        time.sleep(0.03)
        return [("feature_a", "true", "A")]

    monkeypatch.setattr(
        admin_settings,
        "_read_admin_settings_rows_from_db",
        read_rows,
    )

    with ThreadPoolExecutor(max_workers=8) as executor:
        values = list(
            executor.map(
                lambda _index: admin_settings.get_setting("feature_a"),
                range(16),
            )
        )

    assert values == ["true"] * 16
    assert reads == 1


def test_expired_snapshot_refreshes_all_keys_atomically(monkeypatch):
    snapshots = iter(
        [
            [("feature_a", "old-a", "A"), ("feature_b", "old-b", "B")],
            [("feature_a", "new-a", "A"), ("feature_b", "new-b", "B")],
        ]
    )
    reads = 0

    def read_rows():
        nonlocal reads
        reads += 1
        return next(snapshots)

    monkeypatch.setattr(
        admin_settings,
        "_read_admin_settings_rows_from_db",
        read_rows,
    )

    assert admin_settings.get_setting("feature_a") == "old-a"
    admin_settings.invalidate_setting_cache("feature_a")
    assert admin_settings.get_setting("feature_a") == "new-a"
    assert admin_settings.get_setting("feature_b") == "new-b"
    assert reads == 2


def test_stale_values_survive_temporary_database_failure(monkeypatch):
    reads = 0

    def read_rows():
        nonlocal reads
        reads += 1
        if reads == 1:
            return [("feature_a", "safe-current-value", "A")]
        raise RuntimeError("database temporarily unavailable")

    monkeypatch.setattr(
        admin_settings,
        "_read_admin_settings_rows_from_db",
        read_rows,
    )

    assert admin_settings.get_setting("feature_a") == "safe-current-value"
    admin_settings.invalidate_setting_cache()
    assert admin_settings.get_setting("feature_a") == "safe-current-value"
    assert reads == 2


def test_initial_database_failure_is_backed_off(monkeypatch):
    reads = 0

    def read_rows():
        nonlocal reads
        reads += 1
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(
        admin_settings,
        "_read_admin_settings_rows_from_db",
        read_rows,
    )

    assert admin_settings.get_setting("feature_a") is None
    assert admin_settings.get_setting("feature_b") is None
    assert reads == 1


def test_admin_metadata_read_primes_typed_getters(monkeypatch):
    reads = 0

    def read_rows():
        nonlocal reads
        reads += 1
        return [("homepage_fomo_enabled", "true", "Homepage flag")]

    monkeypatch.setattr(
        admin_settings,
        "_read_admin_settings_rows_from_db",
        read_rows,
    )

    rows = admin_settings.get_admin_settings_rows(refresh=True)

    assert rows == [
        {
            "key": "homepage_fomo_enabled",
            "value": "true",
            "description": "Homepage flag",
        }
    ]
    assert admin_settings.is_homepage_fomo_enabled() is True
    assert reads == 1


def test_committed_write_updates_loaded_snapshot_without_reread(monkeypatch):
    reads = 0

    def read_rows():
        nonlocal reads
        reads += 1
        return [("feature_a", "old", "A")]

    monkeypatch.setattr(
        admin_settings,
        "_read_admin_settings_rows_from_db",
        read_rows,
    )

    assert admin_settings.get_setting("feature_a") == "old"
    admin_settings.update_setting_cache(
        "feature_a",
        "new",
        settings_version="12",
    )

    assert admin_settings.get_setting("feature_a") == "new"
    assert admin_settings.get_setting(admin_settings.ADMIN_SETTINGS_VERSION_KEY) == "12"
    assert admin_settings._LAST_ADMIN_SETTINGS_VERSION == "12"
    assert reads == 1


def test_changed_global_version_expires_other_worker_snapshot(monkeypatch):
    snapshots = iter(
        [
            [("feature_a", "old", "A")],
            [("feature_a", "new", "A")],
        ]
    )
    reads = 0

    def read_rows():
        nonlocal reads
        reads += 1
        return next(snapshots)

    monkeypatch.setattr(
        admin_settings,
        "_read_admin_settings_rows_from_db",
        read_rows,
    )
    monkeypatch.setattr(
        admin_settings,
        "get_raw_settings_no_cache",
        lambda _keys: {
            admin_settings.ADMIN_SETTINGS_VERSION_KEY: "2",
            admin_settings.CREDITS_SETTINGS_VERSION_KEY: "0",
        },
    )

    assert admin_settings.get_setting("feature_a") == "old"
    admin_settings._LAST_ADMIN_SETTINGS_VERSION = "1"
    admin_settings._LAST_CREDITS_SETTINGS_VERSION = "0"

    admin_settings.poll_admin_settings_version_once()

    assert admin_settings.get_setting("feature_a") == "new"
    assert reads == 2
