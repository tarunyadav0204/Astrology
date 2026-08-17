from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from nudge_engine.routes import (
    CampaignBulkCreateRequest,
    CampaignUpsertRequest,
    _validate_campaign_payload,
    admin_create_campaigns_bulk,
)


def _scheduled_request(index: int) -> CampaignUpsertRequest:
    hour = ("07", "12", "16", "22")[index % 4]
    return CampaignUpsertRequest(
        name=f"Daily PN {index}",
        title_template=f"Title {index}",
        body_template=f"Body {index}",
        question_template=f"Question {index}",
        channel_policy="push_only",
        channels=["push"],
        scheduled_at=f"2026-08-20T{hour}:00:00+05:30",
        status="scheduled",
    )


def test_campaign_schedule_keeps_explicit_ist_offset():
    fields = _validate_campaign_payload(_scheduled_request(0))

    assert fields["scheduled_at"].utcoffset().total_seconds() == 5.5 * 60 * 60
    assert fields["channel_policy"] == "push_only"
    assert fields["channels_json"] == '["push"]'


def test_bulk_request_accepts_one_hundred_campaigns():
    body = CampaignBulkCreateRequest(campaigns=[_scheduled_request(index) for index in range(100)])

    assert len(body.campaigns) == 100


@pytest.mark.asyncio
async def test_bulk_campaign_create_commits_all_items_once():
    connection = MagicMock()

    @contextmanager
    def fake_connection():
        yield connection

    requests = [_scheduled_request(index) for index in range(4)]
    body = CampaignBulkCreateRequest(campaigns=requests)
    with (
        patch("nudge_engine.routes.db.get_conn", side_effect=fake_connection),
        patch("nudge_engine.routes.db.init_nudge_tables"),
        patch("nudge_engine.routes.db.create_campaign", side_effect=[101, 102, 103, 104]) as create,
    ):
        result = await admin_create_campaigns_bulk(
            body,
            current_user=SimpleNamespace(role="admin", userid=7),
        )

    assert result["count"] == 4
    assert result["campaign_ids"] == [101, 102, 103, 104]
    assert create.call_count == 4
    connection.commit.assert_called_once_with()
