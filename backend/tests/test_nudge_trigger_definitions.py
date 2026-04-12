"""
Unit tests: admin-configurable nudge templates (layer A) and config validation (layer B).
"""
import pytest

from nudge_engine.config_validate import ConfigValidationError, validate_and_normalize_config
from nudge_engine.template_render import (
    TemplateRenderError,
    extract_placeholders,
    render_all,
    validate_templates,
)
from nudge_engine.trigger_defaults import get_spec
from nudge_engine.trigger_def_loader import merge_row


class TestTemplateRender:
    def test_render_all_success(self):
        spec = get_spec("natal_planet_return")
        assert spec is not None
        facts = {
            "planet": "Mars",
            "date_range": "3–9 Apr 2026",
            "window_start": "2026-04-03",
            "window_end": "2026-04-09",
        }
        title, body, q = render_all(
            "{planet} test title",
            "Body {date_range} {planet}",
            "Q {window_start} to {window_end}",
            facts,
            spec.allowed_placeholders,
        )
        assert title == "Mars test title"
        assert "3–9 Apr 2026" in body
        assert "2026-04-03" in q

    def test_disallowed_placeholder_in_title(self):
        spec = get_spec("natal_planet_return")
        assert spec is not None
        with pytest.raises(TemplateRenderError, match="Disallowed"):
            validate_templates(
                "{evil}",
                "body {planet}",
                None,
                spec.allowed_placeholders,
            )

    def test_missing_fact(self):
        spec = get_spec("natal_planet_return")
        assert spec is not None
        facts = {"planet": "Mars"}  # missing date_range, window_*
        with pytest.raises(TemplateRenderError, match="Missing"):
            render_all(
                "{planet}",
                "{planet} {date_range}",
                None,
                facts,
                spec.allowed_placeholders,
            )

    def test_value_with_braces_not_expanded(self):
        spec = get_spec("natal_planet_return")
        facts = {
            "planet": "a{b}c",
            "date_range": "x",
            "window_start": "2026-01-01",
            "window_end": "2026-01-02",
        }
        title, _, _ = render_all(
            "T {planet}",
            "B {date_range}",
            None,
            facts,
            spec.allowed_placeholders,
        )
        assert title == "T a{b}c"

    def test_optional_empty_question(self):
        spec = get_spec("natal_whole_sign_return")
        assert spec is not None
        facts = {
            "planet": "Venus",
            "sign": "Taurus",
            "date_range": "1–5 May 2026",
            "window_start": "2026-05-01",
            "window_end": "2026-05-05",
        }
        t, b, q = render_all("T {planet}", "B {sign}", "", facts, spec.allowed_placeholders)
        assert q is None
        validate_templates("T {planet}", "B {sign}", None, spec.allowed_placeholders)


class TestConfigValidate:
    def test_natal_planet_return_defaults(self):
        c = validate_and_normalize_config("natal_planet_return", {})
        assert c["orb_deg"] == 1.0
        assert c["advance_notice_days"] == 30
        assert "Mars" in c["planets"]

    def test_orb_out_of_range(self):
        with pytest.raises(ConfigValidationError):
            validate_and_normalize_config("natal_planet_return", {"orb_deg": 10})

    def test_planets_subset(self):
        c = validate_and_normalize_config(
            "natal_whole_sign_return",
            {"planets": ["Sun", "Moon"]},
        )
        assert c["planets"] == ["Sun", "Moon"]

    def test_unknown_planet(self):
        with pytest.raises(ConfigValidationError, match="Unknown planet"):
            validate_and_normalize_config(
                "natal_planet_return",
                {"planets": ["Pluto"]},
            )


class TestMergeRow:
    def test_merge_without_db_row(self):
        spec = get_spec("natal_planet_return")
        assert spec is not None
        m = merge_row(spec, None)
        assert m.enabled is True
        assert m.priority == spec.default_priority
        assert "{planet}" in m.title_template
        assert m.config["horizon_days"] == 800


def test_extract_placeholders():
    assert extract_placeholders("Hi {planet} {sign}") == frozenset({"planet", "sign"})
