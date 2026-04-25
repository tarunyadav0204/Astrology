from ai.intent_router import _extract_specific_date_from_question, apply_transit_timing_guards


def test_extract_specific_date_from_relative_day():
    now = __import__("datetime").datetime(2026, 4, 22, 12, 0, 0)
    assert _extract_specific_date_from_question("How is tomorrow for me?", now=now) == "2026-04-23"
    assert _extract_specific_date_from_question("What about day after tomorrow?", now=now) == "2026-04-24"


def test_extract_specific_date_from_explicit_month_day():
    now = __import__("datetime").datetime(2026, 4, 22, 12, 0, 0)
    assert _extract_specific_date_from_question("What happens on March 16th?", now=now) == "2026-03-16"
    assert _extract_specific_date_from_question("What happens on 16 March 2027?", now=now) == "2027-03-16"


def test_apply_transit_timing_guards_sets_exact_day_fields():
    now = __import__("datetime").datetime(2026, 4, 22, 12, 0, 0)
    result = {
        "category": "general",
        "mode": "ANALYZE_PERSONALITY",
        "extracted_context": {},
        "needs_transits": False,
    }
    apply_transit_timing_guards(result, "How is tomorrow?", current_year=2026, now=now)
    assert result["mode"] == "PREDICT_DAILY"
    assert result["context_type"] == "birth"
    assert result["analysis_type"] == "DAILY_PREDICTION"
    assert result["needs_transits"] is True
    assert result["dasha_as_of"] == "2026-04-23"
    assert result["transit_request"]["startYear"] == 2026
    assert result["transit_request"]["yearMonthMap"] == {"2026": ["April"]}
