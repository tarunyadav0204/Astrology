from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from nudge_engine.campaigns import LANDING_SCREEN_TO_CTA, send_campaign_test
from nudge_engine.routes import CampaignUpsertRequest, _validate_campaign_payload


def _request(**overrides):
    values = {
        "name": "New article",
        "title_template": "Read this",
        "body_template": "A new article is ready.",
        "landing_screen": "blog",
        "landing_url": "https://astroroshni.com/blog/saturn-retrograde",
    }
    values.update(overrides)
    return CampaignUpsertRequest(**values)


def test_blog_campaign_requires_a_valid_https_link():
    with pytest.raises(HTTPException) as missing:
        _validate_campaign_payload(_request(landing_url=""))
    assert missing.value.detail == "Blog link is required"

    with pytest.raises(HTTPException) as invalid:
        _validate_campaign_payload(_request(landing_url="javascript:alert(1)"))
    assert invalid.value.detail == "Blog link must be a valid HTTPS URL"


def test_blog_campaign_retains_normalized_landing_data():
    fields = _validate_campaign_payload(_request())

    assert fields["landing_screen"] == "blog"
    assert fields["landing_url"] == "https://astroroshni.com/blog/saturn-retrograde"
    assert LANDING_SCREEN_TO_CTA["blog"] == "astroroshni://blog"


def test_blog_test_push_contains_the_article_link():
    campaign = {
        "id": 12,
        "landing_screen": "blog",
        "landing_url": "https://astroroshni.com/blog/saturn-retrograde",
        "channels": ["push"],
        "channel_policy": "push_only",
    }
    @contextmanager
    def fake_conn():
        yield MagicMock()

    with (
        patch("nudge_engine.campaigns.db.get_read_conn", side_effect=fake_conn),
        patch("nudge_engine.campaigns.db.get_conn", side_effect=fake_conn),
        patch("nudge_engine.campaigns.resolve_params_for_users", return_value={42: {}}),
        patch(
            "nudge_engine.campaigns._resolve_delivery_endpoints",
            return_value={42: {"email": "", "whatsapp": {}}},
        ),
        patch("nudge_engine.campaigns._resolve_push_endpoints", return_value={42: []}),
        patch(
            "nudge_engine.campaigns.render_campaign_for_user",
            return_value={"title": "Read this", "body": "New article", "question": ""},
        ),
        patch(
            "nudge_engine.campaigns._deliver_recipient_snapshots",
            return_value=[{"sent": ["push"], "attempts": [("push", True)]}],
        ) as deliver,
        patch("nudge_engine.campaigns.db.insert_delivery"),
    ):
        send_campaign_test(campaign, 42)

    recipient = deliver.call_args.args[0][0]
    assert recipient["data"]["cta"] == "astroroshni://blog"
    assert {key: recipient["data"][key] for key in ("landing_screen", "blog_url", "slug")} == {
        "landing_screen": "blog",
        "blog_url": "https://astroroshni.com/blog/saturn-retrograde",
        "slug": "saturn-retrograde",
    }
