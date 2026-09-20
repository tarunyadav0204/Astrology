import asyncio
from datetime import datetime, timezone

from engagement_suggestions.deterministic_copy import clean_question, normalize_locale, notification_copy, timeless_chat_question
from engagement_suggestions.manifestation_adapter import question_for_match, resolve_manifestations
from engagement_suggestions.service import EngagementSuggestionService, _aware, _now_for_chart


def test_clean_question_normalizes_and_adds_question_mark():
    assert clean_question("  Will   this move forward. ") == "Will this move forward?"


def test_chat_question_does_not_impose_today_scope():
    assert timeless_chat_question(
        "How could professional recognition or advancement become relevant today?"
    ) == "How could professional recognition or advancement develop in this period?"
    assert timeless_chat_question("What is changing in work today?") == "What is changing in work?"
    assert "today" not in timeless_chat_question("What should I focus on for today?").lower()


def test_shared_manifestation_kg_drives_house_combination_questions():
    matches = resolve_manifestations(
        {3, 9, 11}, method="kp", phase="developing", limit=20,
    )
    ids = {row["manifestation_id"] for row in matches}
    assert "travel.documentation" in ids
    assert "family.father_communication_support" in ids
    assert "guidance.mentor_guru_support" in ids
    assert all(row["ontology_version"] == "0.3.2" for row in matches)


def test_manifestation_question_copy_is_deterministic():
    match = {"label": "Visa, travel documentation or permission"}
    assert question_for_match(match, phase="developing") == (
        "How could visa, travel documentation or permission develop in this period?"
    )
    assert question_for_match(match, daily=True) == (
        "What does my chart show about visa, travel documentation or permission?"
    )
    assert question_for_match(match, phase="developing", subject="spouse") == (
        "Could my spouse experience visa, travel documentation or permission in this period?"
    )


def test_relative_question_rewrites_second_person_label():
    match = {"label": "A matter involving your spouse's family"}
    assert question_for_match(match, subject="mother") == (
        "Could my mother experience a matter involving her spouse's family in this period?"
    )


def test_notification_copy_names_the_chart():
    copy = notification_copy(
        chart_name="Tarun",
        question="What is changing in work today?",
        source_type="kp_daily",
    )
    assert "Tarun's chart" in copy["push_title"]
    assert "What is changing" in copy["sms_body"]


def test_notification_copy_names_chart_when_a_theme_title_is_supplied():
    copy = notification_copy(
        chart_name="Deepika",
        question="What is changing in work today?",
        source_type="kp_daily",
        title="Career change",
    )
    assert copy["push_title"] == "Deepika's chart: Career change"


def test_aware_date_ends_at_end_of_day():
    value = _aware("2026-09-20", end=True)
    assert value == datetime(2026, 9, 20, 23, 59, 59, 999999, tzinfo=timezone.utc)


def test_locale_aliases_are_canonical():
    assert normalize_locale("English") == "en"
    assert normalize_locale("fr-FR") == "fr"


def test_chart_now_supports_legacy_utc_offset_timezones():
    value = _now_for_chart({"timezone": "UTC+5:30", "latitude": 28.6, "longitude": 77.2})
    assert value.utcoffset().total_seconds() == 5.5 * 3600


def test_refresh_worker_can_claim_one_specific_user_chart():
    class Repository:
        def __init__(self):
            self.claim = None

        def claim_due_refreshes(self, **kwargs):
            self.claim = kwargs
            return []

    repository = Repository()
    result = asyncio.run(EngagementSuggestionService(repository).process_due_refreshes(
        limit=1,
        userid=33,
        birth_chart_id=10314,
    ))
    assert repository.claim == {"limit": 1, "userid": 33, "birth_chart_id": 10314}
    assert result == {"claimed": 0, "completed": 0, "failed": 0, "monthly": 0, "kp": 0}
