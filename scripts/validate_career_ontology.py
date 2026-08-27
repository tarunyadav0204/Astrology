#!/usr/bin/env python3
"""Compile and validate the Career ontology proof of concept.

This dependency-free validator is deliberately stricter than a syntax smoke
test: it verifies executable bindings, graph references, stable identifiers,
competency-question contracts and static/timing separation. WebProtege remains
the visual authoring tool; this script is the release gate and compiler.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE_PATH = ROOT / "knowledge_graph" / "core" / "astroroshni-life-domains.ttl"
POC = ROOT / "knowledge_graph" / "career_poc"
TTL_PATH = POC / "astroroshni-career-poc.ttl"
CASES_PATH = POC / "competency-questions.json"
PREVIEW_PATH = POC / "career-runtime-preview.json"
REPORT_PATH = POC / "career-validation-report.md"


def block_for(ttl: str, resource: str) -> str:
    pattern = rf"(?ms)^\s*{re.escape(resource)}\s+.*?\s\.\s*(?=\n|$)"
    match = re.search(pattern, ttl)
    if not match:
        raise AssertionError(f"Missing ontology resource: {resource}")
    return match.group(0)


def objects(block: str, predicate: str) -> list[str]:
    match = re.search(rf"(?ms)\b{re.escape(predicate)}\s+(.+?)(?=\s*;|\s*\.\s*$)", block)
    return re.findall(r"(?:career|health|marriage|wealth|domain|ar):[A-Za-z0-9_]+", match.group(1)) if match else []


def literal(block: str, predicate: str) -> str | None:
    match = re.search(rf'\b{re.escape(predicate)}\s+"([^"]*)"', block)
    return match.group(1) if match else None


def resource_label(ttl: str, resource: str) -> str:
    block = block_for(ttl, resource)
    return (
        literal(block, "skos:prefLabel")
        or literal(block, "rdfs:label")
        or re.sub(r"(?<!^)(?=[A-Z])", " ", resource.split(":")[-1]).strip()
    )


def graph_node(ttl: str, resource: str, children: list[dict[str, object]] | None = None) -> dict[str, object]:
    node: dict[str, object] = {"id": resource, "label": resource_label(ttl, resource)}
    if children:
        node["children"] = children
    return node


def compile_question_tree(ttl: str, question_resource: str) -> dict[str, object]:
    """Compile a bounded, label-preserving view of the authored ontology."""
    question_block = block_for(ttl, question_resource)
    relations = (
        "ar:inDomain", "ar:evaluatesStage", "ar:requiresFactor",
        "ar:requiresCapability", "ar:allowedAnswerMode", "ar:usesAnswerContract",
        "ar:hasEvidencePolicy", "ar:evaluatesRule", "ar:hasGuardrail",
        "ar:defaultExcludesFactor",
    )
    relation_nodes: list[dict[str, object]] = []
    for predicate in relations:
        targets = objects(question_block, predicate)
        if not targets:
            continue
        target_nodes: list[dict[str, object]] = []
        for target in targets:
            nested: list[dict[str, object]] = []
            display_target = target
            if predicate == "ar:inDomain":
                target_block = block_for(ttl, target)
                canonical = objects(target_block, "owl:sameAs")
                if canonical:
                    display_target = canonical[0]
                topics = objects(block_for(ttl, display_target), "ar:hasDomainTopic")
                if topics:
                    nested.append(graph_node(
                        ttl,
                        "ar:hasDomainTopic",
                        [graph_node(ttl, topic) for topic in topics],
                    ))
            elif predicate == "ar:evaluatesStage":
                factors = objects(block_for(ttl, target), "ar:stageRequiresFactor")
                if factors:
                    nested.append(graph_node(
                        ttl,
                        "ar:stageRequiresFactor",
                        [graph_node(ttl, factor) for factor in factors],
                    ))
            elif predicate == "ar:usesAnswerContract":
                sections = objects(block_for(ttl, target), "ar:hasOutputSection")
                if sections:
                    nested.append(graph_node(
                        ttl,
                        "ar:hasOutputSection",
                        [graph_node(ttl, section) for section in sections],
                    ))
            target_nodes.append(graph_node(ttl, display_target, nested))
        relation_nodes.append(graph_node(ttl, predicate, target_nodes))
    return graph_node(
        ttl,
        "ar:QuestionType",
        [graph_node(ttl, question_resource, relation_nodes)],
    )


def expect_members(actual: list[str], expected: list[str], label: str) -> None:
    missing = sorted(set(expected) - set(actual))
    if missing:
        raise AssertionError(f"{label}: missing {', '.join(missing)}")


def declared_resources(ttl: str) -> set[str]:
    return set(re.findall(r"(?m)^\s*((?:career|health|marriage|wealth|domain|ar):[A-Za-z0-9_]+)\s+", ttl))


def ontology_version(ttl: str) -> str:
    match = re.search(r'owl:versionInfo\s+"([^"]+)"', ttl)
    if not match:
        raise AssertionError("Ontology has no owl:versionInfo")
    return match.group(1)


def validate_integrity(ttl: str, question_resources: list[str]) -> None:
    declared = declared_resources(ttl)
    stable_ids: list[str] = []
    runtime_keys: list[str] = []

    for resource in declared:
        block = block_for(ttl, resource)
        if value := literal(block, "ar:stableId"):
            stable_ids.append(value)
        if resource in question_resources:
            runtime = literal(block, "ar:runtimeKey")
            if not runtime:
                raise AssertionError(f"{resource} has no runtimeKey")
            runtime_keys.append(runtime)
            for predicate in (
                "ar:inDomain", "ar:requiresFactor", "ar:requiresCapability",
                "ar:allowedAnswerMode", "ar:usesAnswerContract",
                "ar:hasEvidencePolicy", "ar:hasGuardrail", "ar:evaluatesStage",
            ):
                if not objects(block, predicate):
                    raise AssertionError(f"{resource} has no {predicate}")
            for stage in objects(block, "ar:evaluatesStage"):
                if stage not in declared:
                    raise AssertionError(f"{resource} references undeclared decision stage {stage}")
                stage_block = block_for(ttl, stage)
                if not re.search(r"\ba\s+ar:DecisionStage\b", stage_block):
                    raise AssertionError(f"{stage} is not declared as ar:DecisionStage")
                factors = objects(stage_block, "ar:stageRequiresFactor")
                if not factors:
                    raise AssertionError(f"{stage} has no ar:stageRequiresFactor children")
                for factor in factors:
                    if factor not in declared:
                        raise AssertionError(f"{stage} references undeclared factor {factor}")
            for reference in re.findall(r"(?:career|health|marriage|wealth|domain):[A-Za-z0-9_]+", block):
                if reference not in declared:
                    raise AssertionError(f"{resource} references undeclared {reference}")

    duplicates = [value for value, count in Counter(stable_ids).items() if count > 1]
    if duplicates:
        raise AssertionError(f"Duplicate stableId(s): {', '.join(sorted(duplicates))}")
    duplicates = [value for value, count in Counter(runtime_keys).items() if count > 1]
    if duplicates:
        raise AssertionError(f"Duplicate QuestionType runtimeKey(s): {', '.join(sorted(duplicates))}")

    capability_resources = re.findall(r"(?m)^\s*((?:career|health|marriage|wealth):[A-Za-z0-9_]+)\s+a\s+ar:CalculatorCapability\b", ttl)
    for resource in capability_resources:
        if not literal(block_for(ttl, resource), "ar:calculatorBinding"):
            raise AssertionError(f"{resource} has no executable calculatorBinding")


def main() -> int:
    domain_label = {
        "career_poc": "Career",
        "health_poc": "Health",
        "marriage_poc": "Marriage and Relationship",
        "wealth_poc": "Wealth and Finance",
    }.get(POC.name, POC.name)
    source_ttl = TTL_PATH.read_text(encoding="utf-8")
    core_ttl = CORE_PATH.read_text(encoding="utf-8")
    ttl = source_ttl + "\n" + core_ttl
    case_document = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    cases = case_document["cases"]
    version = ontology_version(source_ttl)
    if version != case_document["ontology_version"]:
        raise AssertionError(
            f"Version mismatch: TTL {version}, competency matrix {case_document['ontology_version']}"
        )
    domain_prefix = {
        "career_poc": "career",
        "health_poc": "health",
        "marriage_poc": "marriage",
        "wealth_poc": "wealth",
    }.get(POC.name)
    if not domain_prefix:
        raise AssertionError(f"Unsupported ontology module: {POC.name}")
    for prefix in ("ar", domain_prefix, "domain", "owl", "rdf", "rdfs", "skos", "xsd"):
        if f"@prefix {prefix}:" not in source_ttl:
            raise AssertionError(f"Missing Turtle prefix: {prefix}")

    validate_integrity(ttl, [case["expected_topic"] for case in cases])
    preview: dict[str, object] = {
        "ontology_version": version,
        "generated_from": TTL_PATH.name,
        "purpose": f"Compiled {domain_label} policy bundle for shadow-mode runtime evaluation",
        "topics": {},
    }
    report_rows: list[str] = []

    for case in cases:
        block = block_for(ttl, case["expected_topic"])
        fields = {
            "required_factors": objects(block, "ar:requiresFactor"),
            "default_exclusions": objects(block, "ar:defaultExcludesFactor"),
            "required_capabilities": objects(block, "ar:requiresCapability"),
            "answer_modes": objects(block, "ar:allowedAnswerMode"),
            "answer_contracts": objects(block, "ar:usesAnswerContract"),
            "evidence_policies": objects(block, "ar:hasEvidencePolicy"),
            "guardrails": objects(block, "ar:hasGuardrail"),
            "decision_rules": objects(block, "ar:evaluatesRule"),
            "decision_stages": objects(block, "ar:evaluatesStage"),
        }
        checks = (
            ("factors", fields["required_factors"], case["must_require_factors"]),
            ("exclusions", fields["default_exclusions"], case["must_exclude_factors"]),
            ("capabilities", fields["required_capabilities"], case["must_require_capabilities"]),
            ("mode", fields["answer_modes"], [case["expected_mode"]]),
            ("contract", fields["answer_contracts"], [case["expected_contract"]]),
            ("evidence policy", fields["evidence_policies"], [case["expected_evidence_policy"]]),
            ("guardrails", fields["guardrails"], case["must_have_guardrails"]),
            ("decision rules", fields["decision_rules"], case["must_evaluate_rules"]),
            ("decision stages", fields["decision_stages"], case.get("must_evaluate_stages", [])),
        )
        for label, actual, expected in checks:
            expect_members(actual, expected, f"{case['id']} {label}")

        runtime_key = literal(block, "ar:runtimeKey")
        if runtime_key != case["expected_runtime_key"]:
            raise AssertionError(f"{case['id']} runtime key: expected {case['expected_runtime_key']}, got {runtime_key}")
        if "career:NoUnrequestedTiming" in fields["guardrails"]:
            forbidden = {"career:CapDashaActivation", "career:CapTransitActivation"}
            if forbidden.intersection(fields["required_capabilities"]):
                raise AssertionError(f"{case['id']} is static but requires a timing calculator")

        bindings = {}
        for capability in fields["required_capabilities"]:
            bindings[capability] = literal(block_for(ttl, capability), "ar:calculatorBinding")
        topic = {
            "competency_id": case["id"], "question_example": case["question"],
            "ontology_resource": case["expected_topic"], **fields,
            "question_label": resource_label(ttl, case["expected_topic"]),
            "graph_tree": compile_question_tree(ttl, case["expected_topic"]),
            "answer_mode": fields["answer_modes"][0],
            "answer_contract": fields["answer_contracts"][0],
            "evidence_policy": fields["evidence_policies"][0],
            "calculator_bindings": bindings,
            "override_condition": literal(block, "ar:overrideCondition"),
        }
        del topic["answer_modes"], topic["answer_contracts"], topic["evidence_policies"]
        preview["topics"][runtime_key] = topic
        report_rows.append(
            f"| `{case['id']}` | {case['question']} | `{runtime_key}` | "
            f"`{topic['answer_mode'].split(':')[-1]}` | {len(fields['required_factors'])} | "
            f"{len(fields['required_capabilities'])} | PASS |"
        )

    PREVIEW_PATH.write_text(json.dumps(preview, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = [
        f"# {domain_label} ontology validation report", "", f"- Ontology version: `{version}`",
        f"- Competency questions: **{len(cases)}**", "- Result: **PASS**", "",
        "| Test | Human question | Runtime key | Answer mode | Factors | Calculators | Result |",
        "|---|---|---|---|---:|---:|---|", *report_rows, "",
        "## Release checks", "", "- All graph references resolve.",
        "- Stable IDs and QuestionType runtime keys are unique.",
        "- Every required calculator capability has an executable binding.",
        "- Evidence policies, answer contracts and guardrails are present for every route.",
        f"- Every {domain_label} QuestionType has decision-stage children, and every decision stage has astrology-factor children.",
        "- Static routes exclude timing and do not invoke dasha/transit calculators.", "",
        "This report validates policy completeness, not astrological correctness. Calculator fixtures and domain-expert verdicts are the next gate.", "",
    ]
    REPORT_PATH.write_text("\n".join(report), encoding="utf-8")
    print(f"{domain_label} ontology PoC valid: {len(cases)} competency questions")
    print(f"Runtime bundle: {PREVIEW_PATH.relative_to(ROOT)}")
    print(f"Readable report: {REPORT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, json.JSONDecodeError) as exc:
        domain_label = "Health" if POC.name == "health_poc" else "Career"
        print(f"{domain_label} ontology PoC invalid: {exc}", file=sys.stderr)
        raise SystemExit(1)
