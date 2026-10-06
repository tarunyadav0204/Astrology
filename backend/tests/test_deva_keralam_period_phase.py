import pytest

from classical_rules.contextual import ContextualRuleSpec, build_contextual_rule
from classical_rules.deva_keralam.chart_facts import ChartFactInputError, compile_deva_keralam_chart_facts
from classical_rules.deva_keralam.period_phase import (
    period_junction_expression,
    period_phase_expression,
    period_proximity_expression,
)
from classical_rules.deva_keralam.service import match_deva_keralam_chart
from classical_rules.models import SourceProfile


SOURCE = SourceProfile(
    key="TEST.DK.PERIOD_PHASE.SOURCE",
    work="Deva Keralam test fixture",
    chapter=1,
    chapter_title="Period phase fixture",
    verse_start=1,
    verse_end=1,
    witness_url="local-source://test",
    witness_policy="test_only",
    numbering_note="Synthetic period-phase source.",
    reference_label="Synthetic period-phase fixture",
    edition_key="deva_keralam_volume_1_scan",
    pdf_pages=(1,),
    printed_pages=(1,),
    editorial_status="reviewed_clear",
)


def _selector(slot=1, system="reviewed_test_system", level="major", name="Saturn main period", lord="Saturn"):
    return {"slot": slot, "system": system, "level": level, "name": name, "lord": lord}


def _rule(expression):
    return build_contextual_rule(ContextualRuleSpec(
        key="TEST.DK.PERIOD_PHASE",
        title="Opt-in period-phase test rule",
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
        "start": "2026-01-01",
        "end_exclusive": "2026-01-11",
        "active": True,
    }
    row.update(changes)
    return row


def _facts(periods, as_of):
    return compile_deva_keralam_chart_facts(
        {"ascendant": 10.0, "planets": {}},
        timing_context={"as_of": as_of, "source_periods": periods},
    ).as_dict()["facts"]


def _match(expression, periods, as_of):
    return match_deva_keralam_chart(
        {"ascendant": 10.0, "planets": {}},
        birth_context={"as_of": as_of, "source_periods": periods},
        rules=(_rule(expression),),
    )["results"][0]["applicability"]


def test_phase_boundaries_use_half_open_period_and_exact_fractional_boundaries():
    row = _period()
    first = _facts([row], "2026-01-05")
    midpoint = _facts([row], "2026-01-06")
    assert first["deva_keralam.timing.period.1.half"]["value"] == "first"
    assert midpoint["deva_keralam.timing.period.1.half"]["value"] == "second"
    assert midpoint["deva_keralam.timing.period.1.third"]["value"] == "middle"
    assert midpoint["deva_keralam.timing.period.1.progress_fraction"]["value"] == 0.5

    ended = {**row, "active": False}
    end_facts = _facts([ended], "2026-01-11")
    assert end_facts["deva_keralam.timing.period.1.half"]["value"] == "outside"
    assert "deva_keralam.timing.period.1.progress_fraction" not in end_facts


def test_start_and_end_proximity_require_the_callers_exact_window():
    row = _period(phase_window={"start_proximity_days": 2, "end_proximity_days": 2})
    start_rule = period_proximity_expression(**_selector(), boundary="start", window_days=2)
    end_rule = period_proximity_expression(**_selector(), boundary="end", window_days=2)
    assert _match(start_rule, [row], "2026-01-03") == "matched"
    assert _match(start_rule, [row], "2026-01-04") == "not_matched"
    assert _match(end_rule, [row], "2026-01-09") == "matched"
    wrong_window = period_proximity_expression(**_selector(), boundary="start", window_days=3)
    assert _match(wrong_window, [row], "2026-01-03") == "not_matched"


def test_overlapping_boundary_windows_are_preserved_instead_of_resolved():
    row = _period(
        end_exclusive="2026-01-06",
        phase_window={"start_proximity_days": 3, "end_proximity_days": 3},
    )
    facts = _facts([row], "2026-01-03")
    prefix = "deva_keralam.timing.period.1"
    assert facts[f"{prefix}.near_start"]["value"] is True
    assert facts[f"{prefix}.near_end"]["value"] is True
    assert facts[f"{prefix}.proximity_overlap"]["value"] is True


def test_junction_tolerance_is_inclusive_and_does_not_imply_a_result_quality():
    row = _period(phase_window={"junction_tolerance_days": 1})
    rule = period_junction_expression(**_selector(), boundary="start", tolerance_days=1)
    assert _match(rule, [row], "2026-01-02") == "matched"
    assert _match(rule, [row], "2026-01-03") == "not_matched"
    facts = _facts([row], "2026-01-02")
    period_facts = {key: fact["value"] for key, fact in facts.items() if ".timing.period.1." in key}
    assert period_facts["deva_keralam.timing.period.1.junction_boundary"] == "start"
    assert not any("auspicious" in key or "inauspicious" in key for key in period_facts)


def test_nested_periods_keep_independent_phase_and_junction_windows():
    parent = _period(
        start="2020-01-01", end_exclusive="2040-01-01",
        phase_window={"junction_tolerance_days": 1},
    )
    child = _period(
        level="sub", name="Venus sub-period", lord="Venus",
        start="2026-01-01", end_exclusive="2027-01-01",
        phase_window={"start_proximity_days": 5},
    )
    child_selector = _selector(slot=2, level="sub", name="Venus sub-period", lord="Venus")
    child_rule = period_proximity_expression(**child_selector, boundary="start", window_days=5)
    assert _match(child_rule, [parent, child], "2026-01-05") == "matched"
    facts = _facts([parent, child], "2026-01-05")
    assert facts["deva_keralam.timing.period.2.near_start"]["value"] is True
    assert "deva_keralam.timing.period.1.start_proximity_days" not in facts


def test_missing_window_context_is_unavailable_while_fractional_phase_remains_available():
    row = _period()
    proximity = period_proximity_expression(**_selector(), boundary="start", window_days=2)
    phase = period_phase_expression(**_selector(), half="first")
    assert _match(proximity, [row], "2026-01-03") == "unavailable"
    assert _match(phase, [row], "2026-01-03") == "matched"


def test_system_isolation_prevents_cross_system_phase_match():
    rule = period_phase_expression(**_selector(system="another_system"), third="first")
    assert _match(rule, [_period()], "2026-01-02") == "not_matched"


@pytest.mark.parametrize(
    "phase_window, message",
    [
        ({"unknown_days": 1}, "unknown fields"),
        ({"start_proximity_days": -1}, "non-negative integer"),
        ({"junction_tolerance_days": True}, "non-negative integer"),
    ],
)
def test_invalid_caller_window_fails_closed(phase_window, message):
    with pytest.raises(ChartFactInputError, match=message):
        _facts([_period(phase_window=phase_window)], "2026-01-02")
