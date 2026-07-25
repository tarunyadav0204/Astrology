from unittest.mock import patch

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
    with (
        patch("nudge_engine.campaigns.resolve_params_for_users", return_value={42: {}}),
        patch(
            "nudge_engine.campaigns.render_campaign_for_user",
            return_value={"title": "Read this", "body": "New article", "question": ""},
        ),
        patch("nudge_engine.campaigns.deliver_nudge", return_value={"channel": "push"}) as deliver,
    ):
        send_campaign_test(object(), campaign, 42)

    kwargs = deliver.call_args.kwargs
    assert kwargs["cta_deep_link"] == "astroroshni://blog"
    assert kwargs["data_extra"] == {
        "landing_screen": "blog",
        "blog_url": "https://astroroshni.com/blog/saturn-retrograde",
        "slug": "saturn-retrograde",
    }
