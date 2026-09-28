from copy import deepcopy

import pytest

from classical_rules.bphs.chapter_24 import evaluate_chapter_24
from classical_rules.reading import (
    READING_CONTRACT_VERSION,
    build_classical_reading,
    group_insights,
    normalize_insight,
)
from classical_rules.registry import PACKS, iter_packs
from tests.test_bphs_chapter_24_rules import _chart


def _raw_insight(insight_id="rule.a", dedupe_key="wealth.shared"):
    return {
        "insight_id": insight_id,
        "dedupe_key": dedupe_key,
        "area": {"key": "house_2", "house": 2, "order": 2, "label": "Wealth", "label_key": "area.wealth"},
        "subject": {"key": "wealth", "label": "Wealth", "label_key": "subject.wealth"},
        "kind": "natal_promise",
        "priority": 50,
        "title": "Wealth",
        "title_key": "area.wealth",
        "statements": [{"key": f"{insight_id}.statement", "text": "Wealth can grow", "parameters": {}}],
        "condition": "supported",
        "supports": ["strong lord"],
        "pressures": [],
        "evidence": {
            "summary": {"key": f"{insight_id}.evidence", "text": "The lord is strong", "parameters": {}},
            "facts": [{"key": f"{insight_id}.dignity", "label": "Dignity", "value": "own sign", "state": "support"}],
            "raw": {"test": True},
        },
        "sources": [{
            "rule_key": insight_id,
            "reference": "BPHS 1.1",
            "witness_url": "https://example.test/source",
        }],
        "controls": [],
    }


def test_registry_discovers_chapter_capabilities_without_central_chapter_switches():
    assert ("bphs", 3) in PACKS
    assert ("bphs", 24) in PACKS
    assert [key for key, _ in iter_packs(reading_only=True)] == [("bphs", 24)]


def test_corpus_reading_groups_chapter_24_into_twelve_stable_life_areas():
    result = build_classical_reading(_chart())
    assert result["contract_version"] == READING_CONTRACT_VERSION
    assert result["area_count"] == 12
    assert result["insight_count"] == 12
    assert result["fallback_used"] is False
    assert [area["house"] for area in result["areas"]] == list(range(1, 13))
    first = result["areas"][0]
    assert first["key"] == "house_1"
    assert first["insights"][0]["sources"][0]["reference"] == "BPHS 24.4"
    assert first["insights"][0]["contributions"][0]["evidence"]["summary"]["text"]


def test_corpus_reading_can_filter_areas_without_changing_pack_evaluation_contract():
    result = build_classical_reading(_chart(), area_keys=["house_7", "house_10"])
    assert [area["key"] for area in result["areas"]] == ["house_7", "house_10"]
    assert result["insight_count"] == 2


def test_legacy_chapter_response_remains_additive_and_compatible():
    result = evaluate_chapter_24(_chart())
    assert len(result["matches"]) == 12
    assert len(result["insights"]) == 12
    assert result["matches"][0]["outcomes"]


def test_author_declared_semantic_duplicates_merge_sources_and_testimony():
    first = normalize_insight(_raw_insight(), work_key="bphs", chapter=1, pack_title="One")
    second_raw = deepcopy(_raw_insight("rule.b"))
    second_raw["statements"] = [{"key": "rule.b.statement", "text": "Savings require care", "parameters": {}}]
    second_raw["supports"] = []
    second_raw["pressures"] = ["afflicted lord"]
    second_raw["condition"] = "under_pressure"
    second_raw["sources"][0].update({"reference": "BPHS 2.2", "rule_key": "rule.b"})
    second = normalize_insight(second_raw, work_key="bphs", chapter=2, pack_title="Two")
    area = group_insights([first, second])[0]
    merged = area["insights"][0]
    assert merged["condition"] == "mixed"
    assert len(merged["statements"]) == 2
    assert len(merged["sources"]) == 2
    assert len(merged["contributions"]) == 2


def test_malformed_published_insight_fails_loudly():
    broken = _raw_insight()
    broken.pop("evidence")
    with pytest.raises(ValueError, match="structured evidence"):
        normalize_insight(broken, work_key="bphs", chapter=1, pack_title="Broken")
