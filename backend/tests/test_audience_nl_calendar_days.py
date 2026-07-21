import pytest

from nudge_engine.audience_nl import generate_audience_sql, validate_prompt_sql_alignment
from nudge_engine.audience_nl_schema import DISPLAY_COLUMNS


def test_paid_questions_yesterday_not_today_uses_exact_calendar_columns(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    result = generate_audience_sql("Users who asked paid questions yesterday but not today.")

    assert result["model_used"] == "deterministic-calendar-day"
    assert "paid_questions_yesterday > 0" in result["sql"]
    assert "paid_questions_today = 0" in result["sql"]
    assert "questions_asked_30d" not in result["sql"]
    assert "Asia/Kolkata" in result["explanation"]


def test_unpaid_wording_uses_all_question_calendar_columns(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    result = generate_audience_sql("Users who chatted yesterday but not today")

    assert "questions_asked_yesterday > 0" in result["sql"]
    assert "questions_asked_today = 0" in result["sql"]


def test_calendar_day_semantic_guard_rejects_rolling_count_proxy():
    with pytest.raises(ValueError, match="rolling-window count differences are not allowed"):
        validate_prompt_sql_alignment(
            "Users who asked paid questions yesterday but not today",
            "SELECT * FROM admin_audience_user_facts WHERE questions_asked_30d > 0",
        )


def test_calendar_day_counts_are_returned_for_admin_verification():
    assert {
        "questions_asked_yesterday",
        "questions_asked_today",
        "paid_questions_yesterday",
        "paid_questions_today",
    }.issubset(DISPLAY_COLUMNS)

