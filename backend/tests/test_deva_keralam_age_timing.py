from datetime import date

import pytest

from classical_rules.contextual import ContextualRuleSpec, build_contextual_rule
from classical_rules.deva_keralam.age_timing import (
    AgeTimingInputError,
    age_timing_expression,
    calculate_age_timing_window,
    completed_age_interval,
)
from classical_rules.deva_keralam.chart_facts import compile_deva_keralam_chart_facts
from classical_rules.deva_keralam.service import match_deva_keralam_chart
from classical_rules.models import SourceProfile


def _rule(kind="completed_age_equals", start=25, end=None):
    spec = ContextualRuleSpec(
        key=f"TEST.DK.AGE.{kind}.{start}.{end}",
        title="Opt-in explicit age test rule",
        source=SourceProfile(
            key="TEST.DK.AGE.SOURCE",
            work="Deva Keralam test fixture",
            chapter=1,
            chapter_title="Age timing test fixture",
            verse_start=1,
            verse_end=1,
            witness_url="local-source://test",
            witness_policy="test_only",
            numbering_note="Synthetic test source.",
            reference_label="Synthetic age fixture",
            edition_key="deva_keralam_volume_1_scan",
            pdf_pages=(1,),
            printed_pages=(1,),
            editorial_status="reviewed_clear",
        ),
        expression=age_timing_expression(kind, start, end),
        outcome={"topic": "test", "traditional_results": ["Synthetic result."], "timing": None},
        scope="Opt-in timing test",
    )
    return build_contextual_rule(spec)


def _match(rule, context):
    result = match_deva_keralam_chart(
        {"ascendant": 10.0, "planets": {}},
        birth_context=context,
        rules=(rule,),
    )
    return result["results"][0]


def test_completed_age_rule_matches_inside_and_not_outside_half_open_interval():
    rule = _rule()
    inside = _match(rule, {"birth_date": "2000-10-10", "as_of": "2026-10-09"})
    outside = _match(rule, {"birth_date": "2000-10-10", "as_of": "2026-10-10"})
    assert inside["applicability"] == "matched"
    assert outside["applicability"] == "not_matched"


def test_missing_birth_or_current_date_makes_guarded_rule_unavailable():
    rule = _rule()
    no_birth = _match(rule, {"as_of": "2026-10-05"})
    no_current = _match(rule, {"birth_date": "2000-10-10"})
    assert no_birth["applicability"] == "unavailable"
    assert no_current["applicability"] == "unavailable"


def test_birthday_and_calendar_year_boundaries_are_explicit():
    before = calculate_age_timing_window("2000-10-10", "2026-10-09")
    birthday = calculate_age_timing_window("2000-10-10", "2026-10-10")
    assert before.completed_age_years == 25
    assert before.completed_age_interval_start == date(2025, 10, 10)
    assert before.completed_age_interval_end_exclusive == date(2026, 10, 10)
    assert birthday.completed_age_years == 26
    assert birthday.running_year_number == 27
    assert birthday.completed_age_interval_start == date(2026, 10, 10)
    assert birthday.completed_age_interval_end_exclusive == date(2027, 10, 10)
    assert birthday.calendar_year == 2026
    assert birthday.calendar_year_interval_start == date(2026, 1, 1)
    assert birthday.calendar_year_interval_end_exclusive == date(2027, 1, 1)


def test_february_29_boundary_uses_declared_february_28_policy():
    start, end = completed_age_interval(date(2000, 2, 29), 25)
    assert start == date(2025, 2, 28)
    assert end == date(2026, 2, 28)
    assert calculate_age_timing_window("2000-02-29", "2025-02-27").completed_age_years == 24
    assert calculate_age_timing_window("2000-02-29", "2025-02-28").completed_age_years == 25


def test_age_grammar_requires_explicit_semantics_and_valid_bounds():
    assert age_timing_expression("completed_age_after", 30) == {
        "op": "fact",
        "key": "deva_keralam.timing.native.completed_age_years",
        "comparator": "gt",
        "value": 30,
    }
    assert age_timing_expression("completed_age_at_or_after", 30)["comparator"] == "gte"
    assert age_timing_expression("completed_age_between", 20, 25)["value"] == [20, 25]
    assert age_timing_expression("running_year_equals", 27)["key"].endswith("running_year_number")
    assert age_timing_expression("calendar_year_equals", 2026)["key"].endswith("calendar_year")
    with pytest.raises(AgeTimingInputError):
        age_timing_expression("completed_age_between", 25)
    with pytest.raises(AgeTimingInputError):
        age_timing_expression("completed_age_between", 25, 20)


def test_strict_after_and_inclusive_at_or_after_differ_on_the_boundary():
    strict = _rule("completed_age_after", 25)
    inclusive = _rule("completed_age_at_or_after", 25)
    context = {"birth_date": "2000-10-10", "as_of": "2026-10-09"}
    assert _match(strict, context)["applicability"] == "not_matched"
    assert _match(inclusive, context)["applicability"] == "matched"


def test_adapter_emits_new_age_facts_only_when_both_dates_are_supplied():
    chart = {"ascendant": 10.0, "planets": {}}
    without_timing = compile_deva_keralam_chart_facts(chart).as_dict()["facts"]
    partial_timing = compile_deva_keralam_chart_facts(
        chart, timing_context={"as_of": "2026-10-05"},
    ).as_dict()["facts"]
    complete = compile_deva_keralam_chart_facts(
        chart, timing_context={"birth_date": "2000-10-10", "as_of": "2026-10-05"},
    ).as_dict()["facts"]
    assert not any(key.startswith("deva_keralam.timing.native.") for key in without_timing)
    assert not any(key.startswith("deva_keralam.timing.native.") for key in partial_timing)
    assert complete["deva_keralam.timing.native.completed_age_years"]["value"] == 25
    assert complete["deva_keralam.timing.native.running_year_number"]["value"] == 26
    assert complete["deva_keralam.timing.native.calendar_year"]["value"] == 2026
    assert complete["deva_keralam.timing.native.completed_age_interval_end_exclusive"]["value"] == "2026-10-10"
