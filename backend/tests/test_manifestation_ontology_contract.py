from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from manifestation_kg.store import ManifestationKnowledgeStore  # noqa: E402


def test_manifestation_ontology_compiles_and_validates() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_manifestation_ontology.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "58 manifestations, 58 patterns, 29 competency cases" in result.stdout


def test_runtime_bundle_has_versioned_isolated_contract() -> None:
    store = ManifestationKnowledgeStore()
    assert store.schema_version == "manifestation-runtime/v1"
    assert store.ontology_version == "0.3.2"
    assert store.core_domain_version == "1.0.0"
    assert len(store.manifestations) == 58
    assert len(store.patterns) == 58
    assert sum(len(values) for values in store.house_meanings.values()) == 76
    assert len(store.domain_lenses) == 13
    assert store.semantic_coverage["non_empty_house_combinations"] == 4095
    assert store.semantic_coverage["coverage_status"] == "complete"


def test_every_pattern_has_provenance_and_machine_readable_house_masks() -> None:
    store = ManifestationKnowledgeStore()
    for pattern in store.patterns:
        assert pattern.source_ids
        assert all(source_id in store.sources for source_id in pattern.source_ids)
        assert pattern.required_all or pattern.required_any
        for role in ("required_all", "required_any", "supporting", "outcome", "obstructing", "excluded"):
            houses = getattr(pattern, role)
            expected = sum(1 << (house - 1) for house in houses)
            assert pattern.masks[role] == expected, (pattern.stable_id, role)


def test_initial_seed_is_explicitly_provisional() -> None:
    store = ManifestationKnowledgeStore()
    assert store.review_summary == {"provisional": 58}
    assert {pattern.review_status for pattern in store.patterns} == {"provisional"}
    assert all(pattern.claim_basis != "classical_direct" for pattern in store.patterns)


def test_runtime_bundle_is_deterministic() -> None:
    path = ROOT / "knowledge_graph" / "manifestation" / "manifestation-runtime.json"
    catalog = ROOT / "knowledge_graph" / "manifestation" / "manifestation-review-catalog.md"
    before = path.read_bytes()
    catalog_before = catalog.read_bytes()
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_manifestation_ontology.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert path.read_bytes() == before
    assert catalog.read_bytes() == catalog_before


def test_review_catalog_exposes_every_pattern_and_review_dimension() -> None:
    store = ManifestationKnowledgeStore()
    catalog = (
        ROOT / "knowledge_graph" / "manifestation" / "manifestation-review-catalog.md"
    ).read_text(encoding="utf-8")
    for pattern in store.patterns:
        assert f"`{pattern.stable_id}`" in catalog
    assert "Review decision: ☐ Approve  ☐ Revise  ☐ Split  ☐ Reject" in catalog
    assert "## House meaning foundation" in catalog
    assert "## Domain lenses" in catalog
    assert "## Competency cases" in catalog


def test_reviewed_house_meaning_expansion_is_present_and_scoped() -> None:
    store = ManifestationKnowledgeStore()
    expected = {
        3: {"house.3.change"},
        4: {"house.4.vehicle"},
        5: {"house.5.postgraduate_depth", "house.5.first_child"},
        6: {"house.6.service_staff"},
        7: {"house.7.open_enemies", "house.7.second_child"},
        8: {"house.8.occult_sciences", "house.8.in_laws"},
        9: {"house.9.third_child", "house.9.second_marriage"},
        12: {"house.12.bed_pleasures"},
    }
    for house, stable_ids in expected.items():
        meanings = {row["stable_id"]: row for row in store.house_meanings[house]}
        assert stable_ids <= set(meanings)

    derived = (
        (5, "house.5.first_child"),
        (7, "house.7.second_child"),
        (8, "house.8.in_laws"),
        (9, "house.9.third_child"),
        (9, "house.9.second_marriage"),
    )
    for house, stable_id in derived:
        meaning = next(
            row for row in store.house_meanings[house]
            if row["stable_id"] == stable_id
        )
        assert meaning["meaning_scope"] == "derived_house"
        assert meaning["derivation_note"]


def test_store_fails_closed_for_unknown_schema(tmp_path: Path) -> None:
    source = ROOT / "knowledge_graph" / "manifestation" / "manifestation-runtime.json"
    document = json.loads(source.read_text(encoding="utf-8"))
    document["schema_version"] = "unknown/v99"
    invalid = tmp_path / "invalid.json"
    invalid.write_text(json.dumps(document), encoding="utf-8")
    try:
        ManifestationKnowledgeStore(invalid)
    except ValueError as exc:
        assert "Unsupported manifestation bundle schema" in str(exc)
    else:
        raise AssertionError("Unknown schemas must not load")


def test_only_event_timeline_imports_the_new_runtime() -> None:
    tracked = subprocess.run(
        ["git", "ls-files", "backend", "astroroshni_mobile", "frontend", "frontend-next"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    offenders: list[str] = []
    for relative in tracked:
        path = ROOT / relative
        if path.suffix not in {".py", ".js", ".jsx", ".ts", ".tsx"}:
            continue
        if "manifestation_kg" in path.parts or path.name.startswith("test_manifestation_"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if "manifestation_kg" in text:
            offenders.append(relative)
    assert offenders == ["backend/calculators/event_timeline_accuracy_v3.py"]
