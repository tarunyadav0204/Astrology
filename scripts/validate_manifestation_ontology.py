#!/usr/bin/env python3
"""Validate and compile the isolated manifestation knowledge graph.

The live application never reads Turtle. This release tool verifies the
authored graph and emits a deterministic, immutable runtime bundle.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "knowledge_graph" / "manifestation"
TTL_PATH = MODULE / "manifestation-ontology.ttl"
CASES_PATH = MODULE / "competency-cases.json"
RUNTIME_PATH = MODULE / "manifestation-runtime.json"
REPORT_PATH = MODULE / "manifestation-validation-report.md"
REVIEW_CATALOG_PATH = MODULE / "manifestation-review-catalog.md"
CORE_RUNTIME_PATH = ROOT / "knowledge_graph" / "core" / "life-domain-runtime.json"

CLAIM_BASES = {"classical_direct", "traditional_derived", "modern_mapping", "product_heuristic"}
REVIEW_STATUSES = {"provisional", "approved", "rejected", "deprecated"}
PHASES = {"background", "preparatory", "developing", "result_window"}
SYSTEM_SCOPES = {"shared_semantics", "parashari", "kp", "daily"}
MEANING_SCOPES = {"direct", "contextual", "derived_house"}


def block_for(ttl: str, resource: str) -> str:
    match = re.search(rf"(?ms)^\s*{re.escape(resource)}\s+.*?\s\.\s*(?=\n|$)", ttl)
    if not match:
        raise AssertionError(f"Missing ontology resource: {resource}")
    return match.group(0)


def objects(block: str, predicate: str) -> list[str]:
    match = re.search(rf"(?ms)\b{re.escape(predicate)}\s+(.+?)(?=\s*;|\s*\.\s*$)", block)
    if not match:
        return []
    return re.findall(r"(?:ar|domain|manifestation|source):[A-Za-z0-9_]+", match.group(1))


def literal(block: str, predicate: str) -> str | None:
    match = re.search(rf'\b{re.escape(predicate)}\s+"([^"]*)"', block)
    return match.group(1) if match else None


def resources_of_type(ttl: str, class_name: str) -> list[str]:
    return re.findall(
        rf"(?m)^((?:ar|manifestation|source):[A-Za-z0-9_]+)\s+a\s+ar:{re.escape(class_name)}\b",
        ttl,
    )


def version(ttl: str) -> str:
    match = re.search(r'owl:versionInfo\s+"([^"]+)"', ttl)
    if not match:
        raise AssertionError("Manifestation ontology has no owl:versionInfo")
    return match.group(1)


def house_number(resource: str) -> int:
    match = re.fullmatch(r"ar:H(\d{1,2})", resource)
    if not match or not 1 <= int(match.group(1)) <= 12:
        raise AssertionError(f"Invalid house resource: {resource}")
    return int(match.group(1))


def csv_values(value: str | None) -> list[str]:
    return [item.strip() for item in str(value or "").split(",") if item.strip()]


def bool_literal(value: str | None) -> bool:
    normalized = str(value or "false").strip().lower()
    if normalized not in {"true", "false"}:
        raise AssertionError(f"Expected true or false, got {value!r}")
    return normalized == "true"


def domain_maps(core: dict[str, Any]) -> tuple[dict[str, dict[str, str]], dict[str, str]]:
    topics: dict[str, dict[str, str]] = {}
    parents: dict[str, str] = {}
    for parent in core["parents"]:
        parents[parent["id"]] = parent["stable_id"]
        for topic in parent["topics"]:
            topics[topic["id"]] = {
                "runtime_key": topic["runtime_key"],
                "parent_domain": parent["stable_id"],
            }
    return topics, parents


def english_label(block: str, resource: str) -> str:
    match = re.search(r'skos:prefLabel\s+"([^"]+)"@en', block)
    if not match:
        raise AssertionError(f"{resource} has no English prefLabel")
    return match.group(1)


def mask(houses: list[int]) -> int:
    value = 0
    for house in houses:
        value |= 1 << (house - 1)
    return value


def compile_bundle(ttl: str, core: dict[str, Any]) -> dict[str, Any]:
    topic_domains, parent_domains = domain_maps(core)
    house_resources = set(resources_of_type(ttl, "House"))
    expected_houses = {f"ar:H{i}" for i in range(1, 13)}
    if house_resources != expected_houses:
        raise AssertionError(f"House node mismatch: expected 12 canonical houses, got {sorted(house_resources)}")

    source_resources = resources_of_type(ttl, "SourceRecord")
    meaning_resources = resources_of_type(ttl, "HouseMeaning")
    lens_resources = resources_of_type(ttl, "DomainLens")
    manifestation_resources = resources_of_type(ttl, "Manifestation")
    pattern_resources = resources_of_type(ttl, "ActivationPattern")
    declared = (
        house_resources | set(source_resources) | set(meaning_resources) |
        set(lens_resources) | set(manifestation_resources) | set(pattern_resources)
    )

    all_stable_ids: list[str] = []
    sources: dict[str, dict[str, Any]] = {}
    source_by_resource: dict[str, str] = {}
    for resource in source_resources:
        block = block_for(ttl, resource)
        stable_id = literal(block, "ar:stableId")
        if not stable_id:
            raise AssertionError(f"{resource} has no stableId")
        all_stable_ids.append(stable_id)
        source_by_resource[resource] = stable_id
        sources[stable_id] = {
            "resource_id": resource,
            "source_path": literal(block, "ar:sourcePath"),
            "source_note": literal(block, "ar:sourceNote"),
        }
        if not sources[stable_id]["source_path"] or not sources[stable_id]["source_note"]:
            raise AssertionError(f"{resource} has incomplete provenance")

    meaning_source_ids = sorted(
        source_by_resource[resource]
        for resource in source_resources
        if "ar:HouseMeaning" in objects(block_for(ttl, resource), "ar:defaultSourceFor")
    )
    lens_source_ids = sorted(
        source_by_resource[resource]
        for resource in source_resources
        if "ar:DomainLens" in objects(block_for(ttl, resource), "ar:defaultSourceFor")
    )
    if not meaning_source_ids or not lens_source_ids:
        raise AssertionError("House meanings and domain lenses require default provenance")

    domain_index = {
        data["runtime_key"]: data["parent_domain"]
        for data in topic_domains.values()
    }
    house_meanings: dict[str, list[dict[str, Any]]] = {str(house): [] for house in range(1, 13)}
    for resource in meaning_resources:
        block = block_for(ttl, resource)
        stable_id = literal(block, "ar:stableId")
        house_refs = objects(block, "ar:meaningOfHouse")
        domain_refs = objects(block, "ar:inDomain")
        if not stable_id or len(house_refs) != 1 or not domain_refs:
            raise AssertionError(f"{resource} needs one stableId, one house and at least one domain")
        unknown_domains = set(domain_refs) - set(topic_domains)
        if unknown_domains:
            raise AssertionError(f"{resource} uses unknown topic domains {sorted(unknown_domains)}")
        house = house_number(house_refs[0])
        domains = sorted(topic_domains[item]["runtime_key"] for item in domain_refs)
        meaning_scope = literal(block, "ar:meaningScope") or "direct"
        if meaning_scope not in MEANING_SCOPES:
            raise AssertionError(f"{resource} has invalid meaningScope {meaning_scope!r}")
        derivation_note = literal(block, "ar:derivationNote")
        if meaning_scope == "derived_house" and not derivation_note:
            raise AssertionError(f"{resource} needs a derivationNote for derived-house scope")
        explicit_sources = objects(block, "ar:hasSource")
        unknown_sources = set(explicit_sources) - set(source_by_resource)
        if unknown_sources:
            raise AssertionError(f"{resource} uses unknown sources {sorted(unknown_sources)}")
        source_ids = sorted(source_by_resource[item] for item in explicit_sources) or meaning_source_ids
        all_stable_ids.append(stable_id)
        house_meanings[str(house)].append({
            "resource_id": resource,
            "stable_id": stable_id,
            "label": english_label(block, resource),
            "label_key": f"manifestation.{stable_id}.label",
            "domains": domains,
            "parent_domains": sorted({domain_index[item] for item in domains}),
            "meaning_scope": meaning_scope,
            "derivation_note": derivation_note,
            "review_status": "provisional",
            "source_ids": source_ids,
        })
    for house, meanings in house_meanings.items():
        if len(meanings) < 3:
            raise AssertionError(f"House {house} needs at least three contextual meanings")
        meanings.sort(key=lambda row: row["stable_id"])

    domain_lenses: dict[str, dict[str, Any]] = {}
    for resource in lens_resources:
        block = block_for(ttl, resource)
        stable_id = literal(block, "ar:stableId")
        domain_refs = objects(block, "ar:inDomain")
        if not stable_id or len(domain_refs) != 1 or domain_refs[0] not in parent_domains:
            raise AssertionError(f"{resource} needs one canonical parent domain")
        parent_domain = parent_domains[domain_refs[0]]
        roles = {
            "anchor": sorted(house_number(value) for value in objects(block, "ar:anchorHouse")),
            "pathway": sorted(house_number(value) for value in objects(block, "ar:pathwayHouse")),
            "result": sorted(house_number(value) for value in objects(block, "ar:resultHouse")),
            "pressure": sorted(house_number(value) for value in objects(block, "ar:pressureHouse")),
        }
        if not roles["anchor"]:
            raise AssertionError(f"{resource} has no anchor houses")
        all_stable_ids.append(stable_id)
        domain_lenses[parent_domain] = {
            "resource_id": resource,
            "stable_id": stable_id,
            "label": english_label(block, resource),
            "parent_domain": parent_domain,
            **roles,
            "source_ids": lens_source_ids,
            "masks": {key: mask(value) for key, value in roles.items()},
        }
    expected_parent_domains = set(parent_domains.values())
    if set(domain_lenses) != expected_parent_domains:
        raise AssertionError(
            f"Domain lens mismatch: missing={sorted(expected_parent_domains - set(domain_lenses))} "
            f"extra={sorted(set(domain_lenses) - expected_parent_domains)}"
        )

    manifestations: dict[str, dict[str, Any]] = {}
    manifestation_by_resource: dict[str, str] = {}
    for resource in manifestation_resources:
        block = block_for(ttl, resource)
        stable_id = literal(block, "ar:stableId")
        domains = objects(block, "ar:inDomain")
        if not stable_id or len(domains) != 1:
            raise AssertionError(f"{resource} needs one stableId and one domain")
        domain_resource = domains[0]
        if domain_resource not in topic_domains and domain_resource not in parent_domains:
            raise AssertionError(f"{resource} references unknown domain {domain_resource}")
        label_key = literal(block, "ar:labelKey")
        prompt_key = literal(block, "ar:promptKey")
        if not label_key or not prompt_key:
            raise AssertionError(f"{resource} has incomplete presentation metadata")
        all_stable_ids.append(stable_id)
        manifestation_by_resource[resource] = stable_id
        domain_data = topic_domains.get(domain_resource)
        manifestations[stable_id] = {
            "resource_id": resource,
            "label": english_label(block, resource),
            "label_key": label_key,
            "prompt_key": prompt_key,
            "domain": domain_data["runtime_key"] if domain_data else parent_domains[domain_resource],
            "parent_domain": domain_data["parent_domain"] if domain_data else parent_domains[domain_resource],
        }

    patterns: list[dict[str, Any]] = []
    for resource in pattern_resources:
        block = block_for(ttl, resource)
        stable_id = literal(block, "ar:stableId")
        target_refs = objects(block, "ar:mayManifestAs")
        domains = objects(block, "ar:inDomain")
        sources_for_pattern = objects(block, "ar:hasSource")
        if not stable_id or len(target_refs) != 1 or len(domains) != 1:
            raise AssertionError(f"{resource} needs one stableId, manifestation and domain")
        target_ref = target_refs[0]
        if target_ref not in manifestation_by_resource:
            raise AssertionError(f"{resource} references unknown manifestation {target_ref}")
        domain_resource = domains[0]
        domain_data = topic_domains.get(domain_resource)
        if not domain_data:
            raise AssertionError(f"{resource} must use a canonical topic domain, got {domain_resource}")
        if not sources_for_pattern:
            raise AssertionError(f"{resource} has no provenance source")
        unknown_sources = set(sources_for_pattern) - set(source_by_resource)
        if unknown_sources:
            raise AssertionError(f"{resource} references unknown sources {sorted(unknown_sources)}")

        roles = {
            "required_all": sorted(house_number(v) for v in objects(block, "ar:requiresAllHouse")),
            "required_any": sorted(house_number(v) for v in objects(block, "ar:requiresAnyHouse")),
            "supporting": sorted(house_number(v) for v in objects(block, "ar:supportingHouse")),
            "outcome": sorted(house_number(v) for v in objects(block, "ar:outcomeHouse")),
            "obstructing": sorted(house_number(v) for v in objects(block, "ar:obstructingHouse")),
            "excluded": sorted(house_number(v) for v in objects(block, "ar:excludesHouse")),
        }
        if not roles["required_all"] and not roles["required_any"]:
            raise AssertionError(f"{resource} has no required house condition")
        required = set(roles["required_all"]) | set(roles["required_any"])
        if required.intersection(roles["excluded"]):
            raise AssertionError(f"{resource} both requires and excludes the same house")

        minimum_any = int(literal(block, "ar:minimumAny") or (1 if roles["required_any"] else 0))
        if minimum_any < 0 or minimum_any > len(roles["required_any"]):
            raise AssertionError(f"{resource} has invalid minimumAny {minimum_any}")
        phases = csv_values(literal(block, "ar:allowedPhase"))
        if not phases or set(phases) - PHASES:
            raise AssertionError(f"{resource} has invalid allowedPhase {phases}")
        claim_basis = literal(block, "ar:claimBasis")
        review_status = literal(block, "ar:reviewStatus")
        system_scope = literal(block, "ar:systemScope")
        if claim_basis not in CLAIM_BASES:
            raise AssertionError(f"{resource} has invalid claimBasis {claim_basis}")
        if review_status not in REVIEW_STATUSES:
            raise AssertionError(f"{resource} has invalid reviewStatus {review_status}")
        if system_scope not in SYSTEM_SCOPES:
            raise AssertionError(f"{resource} has invalid systemScope {system_scope}")
        priority = int(literal(block, "ar:priority") or "0")
        if not 0 <= priority <= 100:
            raise AssertionError(f"{resource} priority must be 0..100")

        timeline_enabled = bool_literal(literal(block, "ar:timelineEnabled"))
        timeline = {
            "enabled": timeline_enabled,
            "profile": literal(block, "ar:timelineProfile"),
            "varga": literal(block, "ar:timelineVarga"),
            "anchor": sorted(house_number(v) for v in objects(block, "ar:timelineAnchorHouse")),
            "transition": sorted(house_number(v) for v in objects(block, "ar:timelineTransitionHouse")),
            "outcome": sorted(house_number(v) for v in objects(block, "ar:timelineOutcomeHouse")),
            "varga_houses": sorted(house_number(v) for v in objects(block, "ar:timelineVargaHouse")),
            "outcome_required": bool_literal(literal(block, "ar:timelineOutcomeRequired")),
            "outcome_require_all": bool_literal(literal(block, "ar:timelineOutcomeRequireAll")),
            "transition_require_all": bool_literal(literal(block, "ar:timelineTransitionRequireAll")),
            "required_context": literal(block, "ar:timelineRequiredContext"),
        }
        if timeline_enabled:
            if not timeline["profile"] or not timeline["varga"]:
                raise AssertionError(f"{resource} timeline integration needs profile and varga")
            if not timeline["anchor"] or not timeline["transition"] or not timeline["varga_houses"]:
                raise AssertionError(f"{resource} timeline integration needs anchor, transition and varga houses")
            if timeline["outcome_required"] and not timeline["outcome"]:
                raise AssertionError(f"{resource} requires a timeline outcome but has no outcome houses")
            if timeline["required_context"] and not re.fullmatch(
                r"[a-z_]+=[a-z_]+(?:\|[a-z_]+)*", str(timeline["required_context"])
            ):
                raise AssertionError(f"{resource} has invalid timelineRequiredContext")

        all_stable_ids.append(stable_id)
        target_id = manifestation_by_resource[target_ref]
        pattern = {
            "resource_id": resource,
            "stable_id": stable_id,
            "manifestation_id": target_id,
            "domain": domain_data["runtime_key"],
            "parent_domain": domain_data["parent_domain"],
            **roles,
            "minimum_any": minimum_any,
            "allowed_phases": phases,
            "system_scope": system_scope,
            "claim_basis": claim_basis,
            "review_status": review_status,
            "priority": priority,
            "sensitive": bool_literal(literal(block, "ar:sensitive")),
            "source_ids": sorted(source_by_resource[item] for item in sources_for_pattern),
            "timeline": timeline,
        }
        pattern["masks"] = {key: mask(value) for key, value in roles.items()}
        patterns.append(pattern)

    duplicates = sorted(value for value, count in Counter(all_stable_ids).items() if count > 1)
    if duplicates:
        raise AssertionError(f"Duplicate stableId(s): {', '.join(duplicates)}")

    # Every possible non-empty set of the twelve houses must have semantic
    # coverage. This proves representational coverage without manufacturing a
    # concrete event for every one of the 4,095 subsets.
    for combination_mask in range(1, 1 << 12):
        active = {house for house in range(1, 13) if combination_mask & (1 << (house - 1))}
        if any(not house_meanings[str(house)] for house in active):
            raise AssertionError(f"Semantic coverage missing for mask {combination_mask}")
        candidates = [
            lens for lens in domain_lenses.values()
            if active.intersection(
                set(lens["anchor"]) | set(lens["pathway"]) |
                set(lens["result"]) | set(lens["pressure"])
            )
        ]
        if not candidates:
            raise AssertionError(f"No domain lens covers mask {combination_mask}")

    patterns.sort(key=lambda row: row["stable_id"])
    return {
        "schema_version": "manifestation-runtime/v1",
        "ontology_version": version(ttl),
        "core_domain_version": core["ontology_version"],
        "generated_from": TTL_PATH.name,
        "purpose": "Isolated activation-pattern to manifestation runtime bundle; no product is integrated by default.",
        "houses": list(range(1, 13)),
        "house_meanings": house_meanings,
        "domain_index": dict(sorted(domain_index.items())),
        "domain_lenses": dict(sorted(domain_lenses.items())),
        "semantic_coverage": {
            "non_empty_house_combinations": 4095,
            "coverage_status": "complete",
            "claim_boundary": "Semantic coverage does not imply a specific event claim.",
        },
        "sources": dict(sorted(sources.items())),
        "manifestations": dict(sorted(manifestations.items())),
        "patterns": patterns,
        "review_summary": dict(sorted(Counter(row["review_status"] for row in patterns).items())),
    }


def matches(pattern: dict[str, Any], houses: set[int], domain: str | None, phase: str | None) -> bool:
    if domain and domain not in {pattern["domain"], pattern["parent_domain"].removeprefix("domain.")}:
        return False
    if phase and phase not in pattern["allowed_phases"]:
        return False
    if not set(pattern["required_all"]).issubset(houses):
        return False
    if len(set(pattern["required_any"]) & houses) < pattern["minimum_any"]:
        return False
    if set(pattern["excluded"]) & houses:
        return False
    return True


def validate_competency_cases(bundle: dict[str, Any], cases: dict[str, Any]) -> None:
    if cases["ontology_version"] != bundle["ontology_version"]:
        raise AssertionError("Competency cases and ontology versions differ")
    known = set(bundle["manifestations"])
    for case in cases["cases"]:
        requested = set(case["must_include"]) | set(case["must_exclude"])
        unknown = requested - known
        if unknown:
            raise AssertionError(f"{case['id']} references unknown manifestations {sorted(unknown)}")
        active = set(case["active_houses"])
        resolved = {
            row["manifestation_id"]
            for row in bundle["patterns"]
            if matches(row, active, case.get("domain"), case.get("phase"))
        }
        missing = set(case["must_include"]) - resolved
        unexpected = set(case["must_exclude"]) & resolved
        if missing or unexpected:
            raise AssertionError(
                f"{case['id']}: missing={sorted(missing)} unexpected={sorted(unexpected)} resolved={sorted(resolved)}"
            )


def _houses_text(values: list[int]) -> str:
    return ", ".join(f"H{value}" for value in values) if values else "—"


def build_review_catalog(bundle: dict[str, Any], cases: dict[str, Any]) -> str:
    lines = [
        "# Manifestation knowledge review catalog",
        "",
        f"Ontology version: `{bundle['ontology_version']}`  ",
        f"Review queue: **{len(bundle['patterns'])} patterns**  ",
        f"Current states: `{json.dumps(bundle['review_summary'], sort_keys=True)}`",
        "",
        "## How to review",
        "",
        "For any rule, quote its stable pattern ID and choose one decision:",
        "",
        "- **Approve** — the meanings, house roles, phase and scope are acceptable after source review.",
        "- **Revise** — state which houses, wording, phase, domain or sensitivity flag should change.",
        "- **Split** — one rule contains meanings that should become separate manifestations.",
        "- **Reject** — the mapping should not be part of the knowledge base.",
        "",
        "A rule should not become `approved` merely because it sounds plausible. Check its traditional basis, modern translation, counterexamples and the evidence required before a client can use it.",
        "",
        "## House meaning foundation",
        "",
    ]
    for house in range(1, 13):
        lines.extend([f"### House {house}", ""])
        for meaning in bundle["house_meanings"][str(house)]:
            domains = ", ".join(f"`{value}`" for value in meaning["domains"])
            sources = ", ".join(f"`{value}`" for value in meaning["source_ids"])
            lines.append(
                f"- **{meaning['label']}** — `{meaning['stable_id']}` · domains: {domains} · "
                f"scope: `{meaning['meaning_scope']}` · review: `{meaning['review_status']}` · source: {sources}"
            )
            if meaning.get("derivation_note"):
                lines.append(f"  - Context rule: {meaning['derivation_note']}")
        lines.append("")

    lines.extend(["## Domain lenses", ""])
    for domain, lens in sorted(bundle["domain_lenses"].items()):
        lines.extend([
            f"### {lens['label']}",
            "",
            f"- ID: `{lens['stable_id']}`",
            f"- Anchor houses: {_houses_text(lens['anchor'])}",
            f"- Pathway houses: {_houses_text(lens['pathway'])}",
            f"- Result houses: {_houses_text(lens['result'])}",
            f"- Pressure houses: {_houses_text(lens['pressure'])}",
            f"- Source: {', '.join(f'`{value}`' for value in lens['source_ids'])}",
            "",
        ])

    lines.extend(["## Curated manifestation rules", ""])
    manifestations = bundle["manifestations"]
    sources = bundle["sources"]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for pattern in bundle["patterns"]:
        grouped.setdefault(pattern["parent_domain"], []).append(pattern)
    for parent_domain, patterns in sorted(grouped.items()):
        label = bundle["domain_lenses"][parent_domain]["label"]
        lines.extend([f"## {label}", ""])
        for pattern in sorted(patterns, key=lambda row: (-row["priority"], row["stable_id"])):
            manifestation = manifestations[pattern["manifestation_id"]]
            lines.extend([
                f"### {manifestation['label']}",
                "",
                f"- Pattern ID: `{pattern['stable_id']}`",
                f"- Manifestation ID: `{pattern['manifestation_id']}`",
                f"- Topic domain: `{pattern['domain']}`",
                f"- Review status: **{pattern['review_status']}**",
                f"- Claim basis: `{pattern['claim_basis']}`",
                f"- Required houses: {_houses_text(pattern['required_all'])}",
                f"- Alternative required houses: {_houses_text(pattern['required_any'])} (minimum {pattern['minimum_any']})",
                f"- Supporting houses: {_houses_text(pattern['supporting'])}",
                f"- Result houses: {_houses_text(pattern['outcome'])}",
                f"- Pressure houses: {_houses_text(pattern['obstructing'])}",
                f"- Excluded houses: {_houses_text(pattern['excluded'])}",
                f"- Allowed phases: {', '.join(f'`{value}`' for value in pattern['allowed_phases'])}",
                f"- Sensitive: `{'yes' if pattern['sensitive'] else 'no'}`",
                f"- Internal priority: `{pattern['priority']}` (ordering only; not probability)",
                f"- Event Timeline enabled: `{'yes' if pattern['timeline']['enabled'] else 'no'}`",
                "- Provenance:",
            ])
            if pattern["timeline"]["enabled"]:
                timeline = pattern["timeline"]
                lines.extend([
                    f"- Timeline profile: `{timeline['profile']}` · varga: `{timeline['varga']}`",
                    f"- Timeline anchor: {_houses_text(timeline['anchor'])}",
                    f"- Timeline pathway: {_houses_text(timeline['transition'])}",
                    f"- Timeline outcome: {_houses_text(timeline['outcome'])} "
                    f"(required: `{'yes' if timeline['outcome_required'] else 'no'}`)",
                    f"- Timeline context gate: `{timeline['required_context'] or 'none'}`",
                ])
            for source_id in pattern["source_ids"]:
                source = sources[source_id]
                lines.append(
                    f"  - `{source_id}` — `{source['source_path']}` — {source['source_note']}"
                )
            lines.extend([
                "- Review decision: ☐ Approve  ☐ Revise  ☐ Split  ☐ Reject",
                "- Reviewer notes:",
                "",
            ])

    lines.extend(["## Competency cases", ""])
    for case in cases["cases"]:
        lines.extend([
            f"### {case['id']}",
            "",
            f"- Houses: {_houses_text(sorted(case['active_houses']))}",
            f"- Domain: `{case.get('domain') or 'unbounded'}`",
            f"- Phase: `{case.get('phase') or 'unspecified'}`",
            f"- Must include: {', '.join(f'`{value}`' for value in case['must_include']) or '—'}",
            f"- Must exclude: {', '.join(f'`{value}`' for value in case['must_exclude']) or '—'}",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    ttl = TTL_PATH.read_text(encoding="utf-8")
    core = json.loads(CORE_RUNTIME_PATH.read_text(encoding="utf-8"))
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    bundle = compile_bundle(ttl, core)
    validate_competency_cases(bundle, cases)
    RUNTIME_PATH.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REVIEW_CATALOG_PATH.write_text(build_review_catalog(bundle, cases), encoding="utf-8")
    report = [
        "# Manifestation ontology validation report",
        "",
        f"- Ontology version: `{bundle['ontology_version']}`",
        f"- Manifestations: **{len(bundle['manifestations'])}**",
        f"- Activation patterns: **{len(bundle['patterns'])}**",
        f"- Contextual house meanings: **{sum(len(v) for v in bundle['house_meanings'].values())}**",
        f"- Parent-domain lenses: **{len(bundle['domain_lenses'])}**",
        f"- Non-empty house combinations with semantic coverage: **{bundle['semantic_coverage']['non_empty_house_combinations']} / 4095**",
        f"- Competency cases: **{len(cases['cases'])}**",
        f"- Review states: `{json.dumps(bundle['review_summary'], sort_keys=True)}`",
        "- Result: **PASS**",
        "",
        "## Release boundary",
        "",
        "No existing application client imports this module. All seed patterns remain provisional and are excluded by the runtime resolver unless a caller explicitly opts into provisional knowledge.",
        "",
        "This validates structural and behavioral consistency. It does not certify classical provenance; that requires source-specific scholarly review before patterns can be marked approved.",
        "",
    ]
    REPORT_PATH.write_text("\n".join(report), encoding="utf-8")
    print(
        f"Manifestation ontology valid: {len(bundle['manifestations'])} manifestations, "
        f"{len(bundle['patterns'])} patterns, {len(cases['cases'])} competency cases"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"Manifestation ontology invalid: {exc}", file=sys.stderr)
        raise SystemExit(1)
