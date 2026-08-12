from ai.intent_router import IntentRouter, _build_relative_date_prompt_contract
from daily.daily_schema import build_daily_prompt


def test_relative_date_prompt_contract_supplies_exact_user_local_dates():
    contract = _build_relative_date_prompt_contract("2026-12-31")

    assert "TODAY = 2026-12-31" in contract
    assert "YESTERDAY = 2026-12-30" in contract
    assert "TOMORROW = 2027-01-01" in contract
    assert "DAY AFTER TOMORROW = 2027-01-02" in contract
    assert "overrides your internal clock" in contract
    assert "specific_date_basis=\"relative_user_day\"" in contract


def test_instant_router_prompt_contains_authoritative_calendar_contract():
    prompt = IntentRouter.__new__(IntentRouter)._build_compact_instant_router_prompt(
        user_question="HOW WILL BE MY DAY TODAY",
        history_text="",
        app_language="english",
        current_date="2026-08-12",
        current_year=2026,
        current_month="August",
        clarification_limit_text="",
        force_ready_instruction="",
        force_clarify_instruction="",
    )

    assert "TODAY = 2026-08-12" in prompt
    assert "YESTERDAY = 2026-08-11" in prompt
    assert "TOMORROW = 2026-08-13" in prompt
    assert "today / aaj / आज all mean 2026-08-12" in prompt
    assert "Current question: \"HOW WILL BE MY DAY TODAY\"" in prompt


def test_daily_answer_prompt_locks_relative_day_to_resolved_date():
    prompt = build_daily_prompt(
        reduced_context={
            "target_date": "2026-08-12",
            "intent": {
                "specific_date": "2026-08-12",
                "specific_date_basis": "relative_user_day",
            },
        },
        user_question="How will be my day today?",
        language="english",
    )

    assert "DATE LOCK" in prompt
    assert "today/aaj/आज refers exactly to 2026-08-12" in prompt
    assert "never call it yesterday or tomorrow" in prompt
    assert "REQUESTED DATE: 2026-08-12" in prompt
