import os
import sys

_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)


def test_chart_focus_schema_uses_unified_chart_reading_sections():
    from ai.output_schema import get_response_schema_for_mode

    schema = get_response_schema_for_mode(
        "ANALYZE_TOPIC_POTENTIAL",
        chart_focus={"kind": "chart_specific", "primary": "D10", "label": "D10"},
    )

    assert "### Vocation, Status, and Work Function" in schema
    assert "### Career and Work Interpretation" in schema
    assert "### Current Activation" in schema
    assert "#### The Jaimini View" not in schema
    assert "#### Nadi Interpretation" not in schema


def test_normal_schema_still_uses_multi_school_deep_dive():
    from ai.output_schema import get_response_schema_for_mode

    schema = get_response_schema_for_mode("ANALYZE_TOPIC_POTENTIAL")

    assert "#### The Jaimini View" in schema
    assert "#### Nadi Interpretation" in schema


def test_lagna_chart_focus_schema_gets_identity_framing():
    from ai.output_schema import get_response_schema_for_mode

    schema = get_response_schema_for_mode(
        "ANALYZE_TOPIC_POTENTIAL",
        chart_focus={"kind": "chart_specific", "primary": "D1", "label": "Lagna"},
    )

    assert "### Identity, Body, and Life Direction" in schema
    assert "### Life Path Interpretation" in schema


def test_d9_chart_focus_schema_gets_marriage_dharma_framing():
    from ai.output_schema import get_response_schema_for_mode

    schema = get_response_schema_for_mode(
        "ANALYZE_TOPIC_POTENTIAL",
        chart_focus={"kind": "chart_specific", "primary": "D9", "label": "D9"},
    )

    assert "### Marriage, Dharma, and Maturity" in schema
    assert "### Marriage and Dharma Interpretation" in schema


def test_d10_chart_focus_schema_gets_career_framing():
    from ai.output_schema import get_response_schema_for_mode

    schema = get_response_schema_for_mode(
        "ANALYZE_TOPIC_POTENTIAL",
        chart_focus={"kind": "chart_specific", "primary": "D10", "label": "D10"},
    )

    assert "### Vocation, Status, and Work Function" in schema
    assert "### Career and Work Interpretation" in schema
