from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from acquisition_routes import normalize_appsflyer_attribution
from credits.buyer_analytics import _CHANNEL_SQL


def test_appsflyer_attribution_maps_campaign_and_utm_fallback():
    parsed = normalize_appsflyer_attribution(
        af_status="Non-organic",
        media_source="appvestor",
        campaign="ua_in_android_q3",
        campaign_id="c-123",
        adset="lookalike",
        ad="video_a",
        channel="googleadwords_int",
        attribution_raw={"idfa": "should-drop", "af_status": "Non-organic"},
    )
    assert parsed["af_status"] == "Non-organic"
    assert parsed["af_media_source"] == "appvestor"
    assert parsed["af_campaign"] == "ua_in_android_q3"
    assert parsed["af_campaign_id"] == "c-123"
    assert parsed["utm_source"] == "appvestor"
    assert parsed["utm_medium"] == "googleadwords_int"
    assert parsed["utm_campaign"] == "ua_in_android_q3"
    assert "idfa" not in parsed["af_attribution_raw"]


def test_appsflyer_organic_does_not_invent_cpc_medium():
    parsed = normalize_appsflyer_attribution(
        af_status="Organic",
        attribution_raw={"af_status": "Organic"},
    )
    assert parsed["af_status"] == "Organic"
    assert parsed["utm_source"] is None
    assert parsed["utm_medium"] is None
    assert parsed["utm_campaign"] is None


def test_buyer_analysis_includes_appsflyer_group_keys():
    assert "media_source" in _CHANNEL_SQL
    assert "af_campaign" in _CHANNEL_SQL
    assert "paid_status" in _CHANNEL_SQL
