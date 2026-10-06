import pytest

from classical_rules.contextual import ContextualRuleSpec, build_contextual_rule
from classical_rules.deva_keralam.chart_facts import (
    ChartFactInputError,
    compile_deva_keralam_chart_facts,
)
from classical_rules.deva_keralam.period_timing import (
    PeriodTimingInputError,
    named_period_chain_expression,
    named_period_expression,
)
from classical_rules.deva_keralam.service import match_deva_keralam_chart
from classical_rules.models import SourceProfile


SOURCE = SourceProfile(
    key="TEST.DK.PERIOD.SOURCE",
    work="Deva Keralam test fixture",
    chapter=1,
    chapter_title="Named period test fixture",
    verse_start=1,
    verse_end=1,
    witness_url="local-source://test",
    witness_policy="test_only",
    numbering_note="Synthetic test source.",
    reference_label="Synthetic named-period fixture",
    edition_key="deva_keralam_volume_1_scan",
    pdf_pages=(1,),
    printed_pages=(1,),
    editorial_status="reviewed_clear",
)


def _selector(slot=1, lord="Saturn", level="major", name="Saturn main period"):
    return {
        "slot": slot,
        "system": "reviewed_test_system",
        "level": level,
        "name": name,
        "lord": lord,
    }


def _rule(expression):
    return build_contextual_rule(ContextualRuleSpec(
        key="TEST.DK.NAMED_PERIOD",
        title="Opt-in named-period test rule",
        source=SOURCE,
        expression=expression,
        outcome={"topic": "test", "traditional_results": ["Synthetic result."], "timing": None},
        scope="Opt-in timing test",
    ))


def _period(**changes):
    row = {
        "system": "reviewed_test_system",
        "level": "major",
        "name": "Saturn main period",
        "lord": "Saturn",
        "start": "2020-01-01",
        "end_exclusive": "2040-01-01",
        "active": True,
    }
    row.update(changes)
    return row


def _match(rule, periods, as_of="2026-10-05"):
    return match_deva_keralam_chart(
        {"ascendant": 10.0, "planets": {}},
        birth_context={"as_of": as_of, "source_periods": periods},
        rules=(rule,),
    )["results"][0]


def test_named_period_requires_explicit_system_and_missing_chain_is_unavailable():
    with pytest.raises(PeriodTimingInputError, match="system is required"):
        named_period_expression(slot=1, system="", level="major", name="Saturn", lord="Saturn")
    missing = _period()
    missing.pop("system")
    with pytest.raises(ChartFactInputError, match="system is required"):
        _match(_rule(named_period_expression(**_selector())), [missing])
    unavailable = match_deva_keralam_chart(
        {"ascendant": 10.0, "planets": {}},
        birth_context={"as_of": "2026-10-05"},
        rules=(_rule(named_period_expression(**_selector())),),
    )["results"][0]
    assert unavailable["applicability"] == "unavailable"


def test_named_period_wrong_lord_is_not_a_partial_match():
    rule = _rule(named_period_expression(**_selector(lord="Venus")))
    assert _match(rule, [_period()])["applicability"] == "not_matched"


def test_period_boundaries_are_half_open_and_active_status_is_validated():
    rule = _rule(named_period_expression(**_selector()))
    short = _period(start="2026-10-05", end_exclusive="2026-10-10")
    assert _match(rule, [short], as_of="2026-10-05")["applicability"] == "matched"
    ended = {**short, "active": False}
    assert _match(rule, [ended], as_of="2026-10-10")["applicability"] == "not_matched"
    with pytest.raises(ChartFactInputError, match="active contradicts"):
        _match(rule, [short], as_of="2026-10-10")


def test_nested_period_levels_must_share_system_and_fit_parent_interval():
    expression = named_period_chain_expression(
        _selector(),
        _selector(slot=2, lord="Venus", level="sub", name="Venus sub-period"),
    )
    rule = _rule(expression)
    child = _period(
        level="sub", name="Venus sub-period", lord="Venus",
        start="2025-01-01", end_exclusive="2028-01-01",
    )
    assert _match(rule, [_period(), child])["applicability"] == "matched"
    outside = {**child, "start": "2019-01-01"}
    with pytest.raises(ChartFactInputError, match="contained within its parent"):
        _match(rule, [_period(), outside])
    other_system = {**child, "system": "another_system"}
    with pytest.raises(ChartFactInputError, match="same period system"):
        _match(rule, [_period(), other_system])


def test_source_neutral_period_facts_preserve_existing_dasha_facts():
    facts = compile_deva_keralam_chart_facts(
        {"ascendant": 10.0, "planets": {}},
        timing_context={
            "as_of": "2026-10-05",
            "source_periods": [_period()],
            "dasha": {
                "MD": {
                    "lord": "Saturn", "start": "2020-01-01",
                    "end": "2039-01-01", "active": True,
                },
            },
        },
    ).as_dict()["facts"]
    assert facts["deva_keralam.timing.period.1.system"]["value"] == "reviewed_test_system"
    assert facts["deva_keralam.timing.period.1.end_exclusive"]["value"] == "2040-01-01"
    assert facts["deva_keralam.timing.dasha.mahadasha.lord"]["value"] == "Saturn"
    assert facts["deva_keralam.timing.dasha.mahadasha.end"]["value"] == "2039-01-01"

