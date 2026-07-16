"""Unit tests for lifespan/career timing-contract anchors."""

from ai.prediction_anchor import (
    build_anchor_from_event_timing_verdict,
    build_anchor_from_meta,
    compare_verdict_to_anchor,
    extract_window1_label_from_answer,
    format_timing_contract_lock_block,
    get_locked_anchor,
    infer_topic_key,
    merge_anchor_candidates,
    parse_prediction_anchor_meta,
    upsert_anchor_into_extracted_context,
)


def test_infer_career_first_job_topic():
    assert infer_topic_key("When will I get my first job?") == "career_first_job"


def test_parse_prediction_anchor_meta_and_strip():
    raw = (
        "Window 1 is strong.\n"
        'PREDICTION_ANCHOR_META: {"topic_key":"career","confidence":"medium",'
        '"window_1_label":"Jul-Aug 2025","window_1_layer":"activation",'
        '"activation_window":"Jul-Aug 2025","offer_window":"Sep 2025","joining_window":"Oct 2025"}\n'
        'FAQ_META: {"category":"career","canonical_question":"First job timing"}'
    )
    cleaned, meta = parse_prediction_anchor_meta(raw)
    assert meta is not None
    assert meta["window_1_label"] == "Jul-Aug 2025"
    assert "PREDICTION_ANCHOR_META" not in cleaned
    assert "FAQ_META" in cleaned


def test_parse_prediction_anchor_meta_before_next_action_and_faq():
    """Model often emits PREDICTION then NEXT_ACTION then FAQ; old regex only allowed FAQ or EOS."""
    raw = (
        "Final verdict.</div>\n\n"
        'PREDICTION_ANCHOR_META: {"topic_key":"career","confidence":"high",'
        '"window_1_label":"August 2026 – October 2026","window_1_layer":"offer",'
        '"activation_window":"July 2026","offer_window":"August 2026","joining_window":"October 2026"}\n'
        'NEXT_ACTION_META: {"type":"none","follow_up_questions":[]}\n'
        'FAQ_META: {"category":"career","canonical_question":"First job timing"}'
    )
    cleaned, meta = parse_prediction_anchor_meta(raw)
    assert meta is not None
    assert meta["window_1_layer"] == "offer"
    assert "PREDICTION_ANCHOR_META" not in cleaned
    assert "NEXT_ACTION_META" in cleaned
    assert "FAQ_META" in cleaned


def test_build_anchor_from_verdict_and_lock():
    verdict = {
        "confidence": "medium",
        "comparison": "future_meaningfully_stronger",
        "score_delta": 12,
        "best_future_cluster": {
            "start": "2025-07-07",
            "end": "2025-08-28",
            "chain": "Saturn-Mercury-Mars",
            "score": 74,
            "why": ["10th activation"],
        },
        "current_window": {
            "start": "2025-05-01",
            "end": "2025-07-06",
            "chain": "Saturn-Mercury-Rahu",
            "score": 62,
        },
    }
    anchor = build_anchor_from_event_timing_verdict(
        verdict, topic_key="career_first_job", question="when first job?"
    )
    assert anchor is not None
    assert anchor["window_1"]["start"] == "2025-07-07"
    assert anchor["layers"]["activation"]

    ctx = upsert_anchor_into_extracted_context({}, anchor, replace_window1=True)
    locked = get_locked_anchor(ctx, "career_first_job")
    assert locked is not None
    block = format_timing_contract_lock_block(locked, rerank={"allows_rerank": False})
    assert "RE-RANK FORBIDDEN" in block
    assert "Activation" in block


def test_compare_verdict_blocks_silent_rerank():
    anchor = {
        "verdict_fingerprint": {
            "comparison": "future_meaningfully_stronger",
            "score_delta": 12,
            "best_future_chain": "Saturn-Mercury-Mars",
            "best_future_start": "2025-07-07",
        }
    }
    stable = {
        "comparison": "future_meaningfully_stronger",
        "score_delta": 13,
        "best_future_cluster": {
            "start": "2025-07-07",
            "chain": "Saturn-Mercury-Mars",
        },
    }
    decision = compare_verdict_to_anchor(anchor, stable)
    assert decision["allows_rerank"] is False

    flipped = {
        "comparison": "current_clearly_stronger",
        "score_delta": -10,
        "best_future_cluster": {
            "start": "2025-08-28",
            "chain": "Saturn-Mercury-Venus",
        },
    }
    decision2 = compare_verdict_to_anchor(anchor, flipped)
    assert decision2["allows_rerank"] is True


def test_extract_window1_and_merge_from_answer():
    answer = "**Window 1**: July–August 2025\n- Promise Window: 2025"
    assert "July" in extract_window1_label_from_answer(answer)
    anchor = merge_anchor_candidates(
        question="When will I get a job?",
        mode="LIFESPAN_EVENT_TIMING",
        category="career",
        faq_category="career",
        answer_text=answer,
        prediction_anchor_meta=None,
        event_timing_verdict=None,
    )
    assert anchor is not None
    assert "July" in anchor["window_1"]["label"]


def test_build_anchor_from_meta_career_layers():
    meta = {
        "topic_key": "career",
        "confidence": "high",
        "window_1_label": "Jul 2025",
        "window_1_layer": "activation",
        "activation_window": "Jul 2025",
        "offer_window": "Aug-Sep 2025",
        "joining_window": "Oct 2025",
    }
    anchor = build_anchor_from_meta(meta, question="job timing?")
    assert anchor["layers"]["offer"] == "Aug-Sep 2025"
    assert anchor["window_1"]["layer"] == "activation"
