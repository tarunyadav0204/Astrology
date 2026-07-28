from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

from pydantic import ValidationError
import pytest
from fastapi import HTTPException

from prediction_engine.contracts import FomoPresentation, Polarity
from prediction_engine import routes as prediction_routes
from prediction_engine.fomo_repository import (
    birth_chart_hash,
    homepage_fomo_auto_eligible,
    rank_homepage_presentations,
    snapshot_cache_key,
)
from utils import admin_settings


@pytest.mark.parametrize(
    ("enabled", "allowlist", "user_id", "expected"),
    (
        ("false", "", 18, False),
        ("false", "18", 18, False),
        ("true", "", 18, True),
        ("true", "18, 73", 18, True),
        ("true", "18, 73", 19, False),
        ("true", "bad, -4, 73", 73, True),
    ),
)
def test_homepage_fomo_feature_flag_semantics(
    monkeypatch,
    enabled,
    allowlist,
    user_id,
    expected,
):
    values = {
        "homepage_fomo_enabled": enabled,
        "homepage_fomo_user_allowlist": allowlist,
    }
    monkeypatch.setattr(
        admin_settings,
        "get_setting",
        lambda key: values.get(key),
    )

    assert admin_settings.homepage_fomo_enabled_for_user(user_id) is expected


def test_disabled_homepage_fomo_does_not_enter_prediction_capacity(monkeypatch):
    admission_calls = 0

    async def fail_if_admitted():
        nonlocal admission_calls
        admission_calls += 1
        raise AssertionError("disabled FOMO must not enter prediction capacity")

    async def run_check():
        monkeypatch.setattr(
            prediction_routes,
            "homepage_fomo_enabled_for_user",
            lambda _user_id: False,
        )
        monkeypatch.setattr(
            prediction_routes,
            "_admit_homepage_fomo",
            fail_if_admitted,
        )
        result = await prediction_routes.get_homepage_fomo(
            request=None,
            language="en",
            limit=24,
            birth_chart_id=None,
            force_display=False,
            include_ineligible=True,
            current_user=SimpleNamespace(userid=18),
        )
        assert result == {"status": "disabled", "teasers": []}

    asyncio.run(run_check())
    assert admission_calls == 0


@pytest.mark.parametrize(
    ("last_signature", "age", "expected"),
    (
        ("old", timedelta(hours=47), False),
        ("old", timedelta(hours=48), True),
        ("current", timedelta(days=6, hours=23), False),
        ("current", timedelta(days=7), True),
    ),
)
def test_homepage_fomo_cadence(last_signature, age, expected):
    now = datetime(2026, 7, 28, 12, tzinfo=timezone.utc)
    assert homepage_fomo_auto_eligible(
        display_signature="current",
        last_display_signature=last_signature,
        last_displayed_at=now - age,
        now=now,
    ) is expected


def test_homepage_fomo_is_eligible_before_first_display():
    assert homepage_fomo_auto_eligible(
        display_signature="current",
        last_display_signature=None,
        last_displayed_at=None,
    )


def test_homepage_fomo_admission_fails_fast_when_optional_capacity_is_busy(
    monkeypatch,
):
    async def run_check():
        semaphore = asyncio.Semaphore(1)
        await semaphore.acquire()
        monkeypatch.setattr(
            prediction_routes,
            "_FOMO_REQUEST_SEMAPHORE",
            semaphore,
        )
        monkeypatch.setattr(
            prediction_routes,
            "_FOMO_ADMISSION_TIMEOUT_SECONDS",
            0.001,
        )
        try:
            with pytest.raises(HTTPException) as exc_info:
                await prediction_routes._admit_homepage_fomo()
            assert exc_info.value.status_code == 503
        finally:
            semaphore.release()

    asyncio.run(run_check())


def test_homepage_fomo_cleanup_is_throttled(monkeypatch):
    calls = 0

    async def fake_run_in_threadpool(_func, *args, **kwargs):
        nonlocal calls
        calls += 1
        return 0

    async def run_check():
        monkeypatch.setattr(
            prediction_routes,
            "_FOMO_CLEANUP_LOCK",
            asyncio.Lock(),
        )
        monkeypatch.setattr(prediction_routes, "_fomo_cleanup_next_at", 0.0)
        monkeypatch.setattr(
            prediction_routes,
            "run_in_threadpool",
            fake_run_in_threadpool,
        )
        await prediction_routes._cleanup_expired_fomo_if_due()
        await prediction_routes._cleanup_expired_fomo_if_due()

    asyncio.run(run_check())
    assert calls == 1


def test_homepage_fomo_duplicate_generation_is_rejected(monkeypatch):
    class BusyRepository:
        def load_cached(self, **_kwargs):
            return None

        def try_claim_generation(self, **_kwargs):
            return False

    monkeypatch.setattr(
        prediction_routes,
        "fomo_repository",
        BusyRepository(),
    )
    with pytest.raises(prediction_routes.FomoGenerationInProgress):
        prediction_routes._generate_homepage_fomo(
            userid=1,
            chart={
                "id": 7,
                "name": "Native",
                "date": "1980-04-02",
                "time": "14:55:00",
                "latitude": 29.1492,
                "longitude": 75.7217,
                "timezone": "Asia/Kolkata",
            },
            locale="en",
            limit=24,
        )


def _presentation(
    presentation_id: str,
    *,
    subject: str,
    domain: str,
    visible_copy: str | None = None,
) -> FomoPresentation:
    copy_key = visible_copy or presentation_id
    return FomoPresentation(
        presentation_id=presentation_id,
        manifestation_id=f"manifestation-{presentation_id}",
        locale="en",
        subject=subject,
        domain=domain,
        area_label=f"Area {copy_key}",
        tone=Polarity.MIXED,
        title=f"Safe title {copy_key}",
        teaser=f"Safe teaser {copy_key}",
        suggested_question=f"Safe question {copy_key}?",
        rule_id="test",
        template_version="1",
    )


def test_birth_chart_hash_is_stable_and_ignores_display_fields():
    chart = {
        "id": 7,
        "name": "First name",
        "date": "1980-04-02T00:00:00",
        "time": "14:55:00",
        "latitude": 29.1492,
        "longitude": 75.7217,
        "timezone": "Asia/Kolkata",
    }
    renamed = {**chart, "name": "Renamed chart"}

    assert birth_chart_hash(chart) == birth_chart_hash(renamed)
    assert birth_chart_hash(chart) != birth_chart_hash({
        **chart,
        "time": "14:56:00",
    })


def test_cache_key_changes_for_calculation_and_localization_versions():
    base = {
        "userid": 1,
        "birth_chart_id": 7,
        "chart_hash": "chart",
        "as_of": date(2026, 7, 26),
        "horizon_days": 90,
        "profile": "parashari_fomo_v1",
        "profile_version": "3.2.0",
        "engine_version": "5.5.0",
        "schema_version": "prediction_engine.v19",
        "locale": "en",
        "provider_versions": (("transit_house", "1.0.0"),),
        "ephemeris_settings": {"ayanamsha": "Lahiri"},
        "presentation_version": "1.0.0",
    }
    first = snapshot_cache_key(**base)

    assert first == snapshot_cache_key(**base)
    assert first != snapshot_cache_key(**{
        **base,
        "locale": "hi",
    })
    assert first != snapshot_cache_key(**{
        **base,
        "provider_versions": (("transit_house", "1.1.0"),),
    })
    assert first != snapshot_cache_key(**{
        **base,
        "ephemeris_settings": {"ayanamsha": "Raman"},
    })


def test_homepage_ranking_groups_non_overlapping_manifestations_by_subject():
    rows = (
        _presentation("mother-finance", subject="mother", domain="finance"),
        _presentation("self-finance-1", subject="self", domain="finance"),
        _presentation("self-finance-2", subject="self", domain="finance"),
        _presentation("self-career", subject="self", domain="career"),
        _presentation("spouse-property", subject="spouse", domain="property"),
    )

    ranked = rank_homepage_presentations(rows)

    assert [row.presentation_id for row in ranked] == [
        "self-finance-1",
        "self-career",
        "spouse-property",
        "mother-finance",
    ]


def test_homepage_ranking_removes_semantically_overlapping_domains_per_subject():
    rows = (
        _presentation("combined", subject="self", domain="combined"),
        _presentation("career", subject="self", domain="career"),
        _presentation("finance", subject="self", domain="finance"),
    )
    ranked = rank_homepage_presentations(
        rows,
        manifestation_domains={
            "manifestation-combined": ("career", "health"),
        },
    )

    assert [row.presentation_id for row in ranked] == ["combined", "finance"]


def test_homepage_ranking_applies_only_an_explicit_safety_limit():
    rows = tuple(
        _presentation(
            f"self-{index}",
            subject="self",
            domain=f"domain-{index}",
        )
        for index in range(5)
    )

    assert len(rank_homepage_presentations(rows)) == 5
    assert len(rank_homepage_presentations(rows, maximum=4)) == 4


def test_homepage_ranking_collapses_visibly_identical_cards_per_subject():
    rows = (
        _presentation(
            "highest-ranked",
            subject="self",
            domain="finance",
            visible_copy="same",
        ),
        _presentation(
            "duplicate-internal-manifestation",
            subject="self",
            domain="relationship",
            visible_copy="same",
        ),
        _presentation(
            "same-copy-different-subject",
            subject="mother",
            domain="finance",
            visible_copy="same",
        ),
    )

    ranked = rank_homepage_presentations(rows)

    assert [row.presentation_id for row in ranked] == [
        "highest-ranked",
        "same-copy-different-subject",
    ]


def test_homepage_ranking_removes_repeated_anchor_area_but_keeps_new_area():
    rows = (
        _presentation("finance-relationship", subject="self", domain="combined"),
        _presentation("finance-property", subject="self", domain="combined"),
        _presentation("property-only", subject="self", domain="property"),
        _presentation("mother-finance", subject="mother", domain="finance"),
    )

    ranked = rank_homepage_presentations(
        rows,
        manifestation_domains={
            "manifestation-finance-relationship": ("finance", "relationship"),
            "manifestation-finance-property": ("finance", "property"),
        },
    )

    assert [row.presentation_id for row in ranked] == [
        "finance-relationship",
        "property-only",
        "mother-finance",
    ]


def test_fomo_event_batch_is_bounded():
    event = {
        "event_id": "fomo:event:123",
        "presentation_id": "presentation-1",
        "event_type": "shown",
        "metadata": {},
    }
    payload = prediction_routes.FomoEventBatchRequest(
        snapshot_id="snapshot-1",
        events=[event] * 50,
    )
    assert len(payload.events) == 50

    with pytest.raises(ValidationError):
        prediction_routes.FomoEventBatchRequest(
            snapshot_id="snapshot-1",
            events=[event] * 51,
        )


def test_legacy_single_fomo_event_writes_are_serialized(monkeypatch):
    active = 0
    maximum_active = 0

    async def fake_run_in_threadpool(_func, **_kwargs):
        nonlocal active, maximum_active
        active += 1
        maximum_active = max(maximum_active, active)
        await asyncio.sleep(0.005)
        active -= 1
        return True

    monkeypatch.setattr(
        prediction_routes,
        "run_in_threadpool",
        fake_run_in_threadpool,
    )

    async def run_requests():
        await asyncio.gather(*(
            prediction_routes.record_homepage_fomo_event(
                prediction_routes.FomoEventRequest(
                    event_id=f"fomo:event:{index}",
                    snapshot_id="snapshot-1",
                    presentation_id="presentation-1",
                    event_type="shown",
                    metadata={},
                ),
                current_user=SimpleNamespace(userid=1),
            )
            for index in range(10)
        ))

    asyncio.run(run_requests())
    assert maximum_active == 1
