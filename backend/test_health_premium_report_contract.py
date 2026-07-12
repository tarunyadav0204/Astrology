"""Contract tests for Health premium PDF report structure (no live LLM)."""

from __future__ import annotations

from reports.assembly.health_page_assembler import HEALTH_PAGE_BLUEPRINT, assemble_health_pages
from reports.constants import MEDICAL_DISCLAIMER
from reports.llm.health_premium_report import HEALTH_CHAPTER_GROUPS, build_static_health_report
from reports.report_types import HEALTH_REPORT_CONFIG


def test_health_report_config_enabled_and_depth():
    assert HEALTH_REPORT_CONFIG.enabled is True
    assert HEALTH_REPORT_CONFIG.page_count == 27
    assert "d30" in HEALTH_REPORT_CONFIG.required_branches
    assert "d6" not in HEALTH_REPORT_CONFIG.required_branches


def test_health_chapter_groups_cover_exactly_27_sections():
    keys = []
    for chapter in HEALTH_CHAPTER_GROUPS:
        keys.extend(chapter["section_keys"])
    assert len(keys) == 27
    assert len(set(keys)) == 27
    blueprint_keys = [page["key"] for page in HEALTH_PAGE_BLUEPRINT]
    assert keys == blueprint_keys


def test_health_page_blueprint_has_disclaimer_pages_and_d30_chart():
    assert HEALTH_PAGE_BLUEPRINT[0]["key"] == "cover"
    assert HEALTH_PAGE_BLUEPRINT[-1]["key"] == "safety_and_next_steps"
    assert any(page["key"] == "d30_confirmation" for page in HEALTH_PAGE_BLUEPRINT)
    assert any("native_d30" in (page.get("charts") or []) for page in HEALTH_PAGE_BLUEPRINT)


def test_static_health_report_embeds_medical_disclaimer():
    context = {
        "person": {"name": "Test Native"},
        "health": {"health_score": 72, "constitution_type": "Pitta", "yoga_analysis": {}},
        "medical_disclaimer": MEDICAL_DISCLAIMER,
        "current_dashas": {},
        "twelve_month_dasha": [],
        "summaries": {},
    }
    static = build_static_health_report(context)
    assert MEDICAL_DISCLAIMER in static["medical_disclaimer"]
    assert len(static["sections"]) == 27
    assert all(section["facts"].get("medical_disclaimer") for section in static["sections"])


def test_assemble_health_pages_attaches_disclaimer_on_safety_pages():
    context = {
        "person": {"name": "Test Native"},
        "health": {"health_score": 70, "constitution_type": "Vata"},
        "medical_disclaimer": MEDICAL_DISCLAIMER,
        "current_dashas": {"mahadasha": {"planet": "Jupiter"}, "antardasha": {"planet": "Saturn"}},
        "twelve_month_dasha": [
            {"label": "Jan 2026", "mahadasha": "Jupiter", "antardasha": "Saturn", "pratyantardasha": "Mercury"}
            for _ in range(12)
        ],
        "lords_nakshatra": {},
        "planet_system_ranks": [],
        "attention_houses": [],
        "health_agent": {},
    }
    premium = {
        "medical_disclaimer": MEDICAL_DISCLAIMER,
        "health_verdict": "Balanced vitality with timed caution windows.",
        "sections": [
            {
                "key": key,
                "opening_summary": f"Summary for {key}",
                "astrological_basis": "Chart basis",
                "interpretation": "Interpretation",
                "practical_guidance": "Guidance",
                "key_takeaways": ["A", "B", "C"],
            }
            for key in [page["key"] for page in HEALTH_PAGE_BLUEPRINT]
        ],
    }
    pages = assemble_health_pages(context, premium)
    assert len(pages) == 27
    cover = pages[0]
    safety = pages[-1]
    assert any(MEDICAL_DISCLAIMER[:40] in (note or "") for note in (cover.get("notes") or []))
    assert any(MEDICAL_DISCLAIMER[:40] in (note or "") for note in (safety.get("notes") or []))
    overview = next(page for page in pages if page["title"] == "Next 12 Months Overview")
    assert overview.get("tables")
