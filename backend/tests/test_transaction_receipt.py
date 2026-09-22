from credits.transaction_receipt import (
    analysis_usage_metadata,
    ashtakavarga_life_usage_metadata,
    ashtakavarga_oracle_usage_metadata,
    chat_usage_metadata,
    event_timeline_usage_metadata,
    feature_link_from_usage,
    karma_usage_metadata,
    podcast_usage_metadata,
    prashna_usage_metadata,
    inclusive_tax_split,
    money_from_total,
    refund_money_from_original,
    transaction_payment_view,
)


def test_inclusive_gst_on_rupee_pack_adds_back_to_total():
    pretax, tax = inclusive_tax_split(99, 0.18)
    assert round((pretax + tax) * 100) == 9900
    assert tax > 0
    assert pretax > tax


def test_razorpay_inr_receipt_includes_gst_and_hides_payment_secrets():
    view = transaction_payment_view(
        "razorpay",
        '{"payment_id":"pay_123","amount_paise":9900,"currency":"INR","product_id":"credits_50","method":"upi"}',
        None,
    )
    assert view["payment_method"] == "razorpay"
    assert view["product_id"] == "credits_50"
    assert view["money"]["currency"] == "INR"
    assert view["money"]["amount_paid"] == 99.0
    assert view["money"]["tax_included"] is True
    assert view["money"]["tax_rate"] == 0.18
    assert "payment_id" not in view["money"]
    assert round((view["money"]["pretax_amount"] + view["money"]["tax_amount"]) * 100) == 9900


def test_google_play_non_inr_has_amount_without_tax():
    view = transaction_payment_view(
        "google_play",
        {"price_amount_micros": 4990000, "price_currency": "USD", "purchase_token": "secret"},
        None,
    )
    assert view["money"]["currency"] == "USD"
    assert view["money"]["amount_paid"] == 4.99
    assert "tax_amount" not in view["money"]
    assert "purchase_token" not in str(view)


def test_spend_has_no_payment_receipt():
    view = transaction_payment_view("feature_usage", None, None)
    assert view["payment_method"] is None
    assert view["money"] is None


def test_partial_refund_scales_original_inr_charge():
    view = refund_money_from_original(
        -10,
        50,
        "razorpay",
        {"amount_paise": 9900, "currency": "INR", "product_id": "credits_50"},
    )
    assert view["money"]["currency"] == "INR"
    assert view["money"]["amount_paid"] == 19.8
    assert view["money"]["tax_included"] is True
    assert view["product_id"] == "credits_50"


def test_chat_spend_metadata_round_trips_to_a_safe_link():
    raw = chat_usage_metadata("123e4567-e89b-12d3-a456-426614174000", 42)
    link = feature_link_from_usage("chat_question", raw)
    assert link == {
        "kind": "chat",
        "session_id": "123e4567-e89b-12d3-a456-426614174000",
        "message_id": 42,
    }


def test_existing_instant_minute_rows_link_to_the_chat_session():
    link = feature_link_from_usage(
        "instant_chat_minutes",
        {
            "billing_session_id": "bill-secret",
            "chat_session_id": "123e4567-e89b-12d3-a456-426614174000",
        },
    )
    assert link == {
        "kind": "chat",
        "session_id": "123e4567-e89b-12d3-a456-426614174000",
    }
    assert "billing_session_id" not in link


def test_event_timeline_metadata_keeps_yearly_and_monthly_apart():
    yearly = feature_link_from_usage(
        "event_timeline",
        event_timeline_usage_metadata(
            job_id="123e4567-e89b-12d3-a456-426614174000",
            year=2026,
            birth_chart_id=15,
        ),
    )
    monthly = feature_link_from_usage(
        "event_timeline",
        event_timeline_usage_metadata(
            job_id="123e4567-e89b-12d3-a456-426614174000",
            year=2026,
            month=3,
            birth_chart_id=15,
        ),
    )
    assert yearly == {
        "kind": "event_timeline",
        "scope": "yearly",
        "year": 2026,
        "job_id": "123e4567-e89b-12d3-a456-426614174000",
        "birth_chart_id": 15,
    }
    assert monthly["scope"] == "monthly"
    assert monthly["month"] == 3
    assert event_timeline_usage_metadata(job_id="job", year=2026, month=13) is None


def test_analysis_metadata_links_hub_reports_by_chart():
    health = feature_link_from_usage(
        "health_analysis",
        analysis_usage_metadata(analysis="health", birth_chart_id=42),
    )
    assert health == {"kind": "analysis", "analysis": "health", "birth_chart_id": 42}

    progeny = feature_link_from_usage(
        "progeny_analysis",
        analysis_usage_metadata(
            analysis="progeny",
            birth_chart_id=7,
            analysis_focus="next_child",
            children_count=2,
        ),
    )
    assert progeny == {
        "kind": "analysis",
        "analysis": "progeny",
        "birth_chart_id": 7,
        "analysis_focus": "next_child",
        "children_count": 2,
    }
    assert analysis_usage_metadata(analysis="karma", birth_chart_id=1) is None
    assert analysis_usage_metadata(analysis="wealth", birth_chart_id=0) is None
    assert feature_link_from_usage(
        "wealth_analysis",
        {"feature_link": {"kind": "analysis", "analysis": "wealth"}},
    ) is None


def test_podcast_metadata_links_one_episode():
    link = feature_link_from_usage(
        "podcast",
        podcast_usage_metadata(
            message_id=2329,
            lang="hindi",
            session_id="123e4567-e89b-12d3-a456-426614174000",
            birth_chart_id=15,
        ),
    )
    assert link == {
        "kind": "podcast",
        "message_id": "2329",
        "lang": "hi",
        "session_id": "123e4567-e89b-12d3-a456-426614174000",
        "birth_chart_id": 15,
    }
    assert podcast_usage_metadata(message_id="", lang="en") is None
    assert feature_link_from_usage(
        "podcast",
        {"feature_link": {"kind": "podcast", "message_id": "2329", "lang": "fr"}},
    ) is None


def test_saved_reading_links_for_speech_prashna_karma_and_ashtakavarga():
    speech = feature_link_from_usage(
        "speech_chat_minutes",
        {"feature_link": {"kind": "speech", "session_id": "123e4567-e89b-12d3-a456-426614174000"}},
    )
    assert speech == {
        "kind": "speech",
        "session_id": "123e4567-e89b-12d3-a456-426614174000",
    }
    assert feature_link_from_usage("prashna_analysis", prashna_usage_metadata(18)) == {
        "kind": "prashna",
        "reading_id": 18,
    }
    assert feature_link_from_usage("karma_analysis", karma_usage_metadata("44")) == {
        "kind": "karma",
        "birth_chart_id": 44,
    }
    assert feature_link_from_usage(
        "ashtakavarga_oracle_insight",
        ashtakavarga_oracle_usage_metadata(9),
    )["analysis_id"] == 9
    life = feature_link_from_usage(
        "ashtakavarga_life_predictions",
        ashtakavarga_life_usage_metadata(
            date="1990-01-02",
            time="06:30",
            latitude=28.6139,
            longitude=77.209,
        ),
    )
    assert life["scope"] == "life"
    assert life["time"] == "06:30"
    assert life["latitude"] == 28.6139
    assert prashna_usage_metadata(0) is None
    assert karma_usage_metadata("not-a-chart") is None
    assert ashtakavarga_life_usage_metadata(
        date="1990-01-02",
        time="bad",
        latitude=1,
        longitude=1,
    ) is None


def test_non_chat_metadata_does_not_become_a_feature_link():
    assert feature_link_from_usage("wealth_analysis", {"chat_session_id": "123e4567-e89b-12d3-a456-426614174000"}) is None
    assert feature_link_from_usage("chat_question", {"feature_link": {"kind": "report", "session_id": "123e4567-e89b-12d3-a456-426614174000"}}) is None
    assert chat_usage_metadata("not a session", 1) is None


def test_zero_tax_rate_omits_tax_lines(monkeypatch):
    monkeypatch.setenv("RAZORPAY_GST_RATE", "0")
    money = money_from_total("INR", 99)
    assert money["amount_paid"] == 99
    assert "tax_amount" not in money
