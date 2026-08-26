#!/usr/bin/env python3
"""Validate and compile the shared 13-parent life-domain ontology."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from instant_chat_v2.question_taxonomy import LIFE_DOMAINS  # noqa: E402


TTL_PATH = ROOT / "knowledge_graph" / "core" / "astroroshni-life-domains.ttl"
RUNTIME_PATH = ROOT / "knowledge_graph" / "core" / "life-domain-runtime.json"
REPORT_PATH = ROOT / "knowledge_graph" / "core" / "life-domain-validation-report.md"


def _block(ttl: str, resource: str) -> str:
    match = re.search(rf"(?ms)^\s*{re.escape(resource)}\s+.*?\s\.\s*(?=\n|$)", ttl)
    if not match:
        raise AssertionError(f"Missing ontology resource: {resource}")
    return match.group(0)


def _objects(block: str, predicate: str) -> list[str]:
    match = re.search(rf"(?ms)\b{re.escape(predicate)}\s+(.+?)(?=\s*;|\s*\.\s*$)", block)
    return re.findall(r"domain:[A-Za-z0-9_]+", match.group(1)) if match else []


def _literal(block: str, predicate: str) -> str | None:
    match = re.search(rf'\b{re.escape(predicate)}\s+"([^"]*)"', block)
    return match.group(1) if match else None


def main() -> int:
    ttl = TTL_PATH.read_text(encoding="utf-8")
    parents = re.findall(
        r"(?m)^\s*(domain:[A-Za-z0-9_]+)\s+a\s+ar:LifeDomain\b",
        ttl,
    )
    if len(parents) != 13:
        raise AssertionError(f"Expected 13 parent life domains, found {len(parents)}")

    parent_rows: list[dict[str, object]] = []
    assigned_topics: list[str] = []
    runtime_to_parent: dict[str, str] = {}
    for parent in parents:
        block = _block(ttl, parent)
        topics = _objects(block, "ar:hasDomainTopic")
        if not topics:
            raise AssertionError(f"{parent} has no ar:hasDomainTopic children")
        topic_rows = []
        for topic in topics:
            topic_block = _block(ttl, topic)
            runtime_key = _literal(topic_block, "ar:runtimeKey")
            if not runtime_key:
                raise AssertionError(f"{topic} has no runtimeKey")
            assigned_topics.append(topic)
            runtime_to_parent[runtime_key] = parent
            topic_rows.append({
                "id": topic,
                "runtime_key": runtime_key,
                "label": _literal(topic_block, "skos:prefLabel") or topic.split(":")[-1],
            })
        parent_rows.append({
            "id": parent,
            "stable_id": _literal(block, "ar:stableId"),
            "label": _literal(block, "skos:prefLabel") or parent.split(":")[-1],
            "topics": topic_rows,
        })

    duplicate_topics = sorted(
        topic for topic, count in Counter(assigned_topics).items() if count > 1
    )
    if duplicate_topics:
        raise AssertionError(f"Topics assigned to multiple parents: {', '.join(duplicate_topics)}")

    expected_runtime_keys = set(LIFE_DOMAINS) - {"muhurat"}
    actual_runtime_keys = set(runtime_to_parent)
    if actual_runtime_keys != expected_runtime_keys:
        missing = sorted(expected_runtime_keys - actual_runtime_keys)
        extra = sorted(actual_runtime_keys - expected_runtime_keys)
        raise AssertionError(f"Domain topic mismatch; missing={missing}, extra={extra}")

    muhurat = _block(ttl, "domain:Muhurat")
    if "a ar:QuestionOperation" not in muhurat or _literal(muhurat, "ar:runtimeKey") != "muhurat":
        raise AssertionError("Muhurat must be a QuestionOperation, not a LifeDomain")

    version_match = re.search(r'owl:versionInfo\s+"([^"]+)"', ttl)
    version = version_match.group(1) if version_match else None
    runtime = {
        "ontology_version": version,
        "parent_domain_count": len(parent_rows),
        "topic_count": len(actual_runtime_keys),
        "parents": parent_rows,
        "runtime_key_to_parent": dict(sorted(runtime_to_parent.items())),
        "question_operations": [{
            "id": "domain:Muhurat",
            "runtime_key": "muhurat",
            "label": _literal(muhurat, "skos:prefLabel"),
        }],
    }
    RUNTIME_PATH.write_text(json.dumps(runtime, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = [
        "# Life-domain ontology validation report", "",
        f"- Ontology version: `{version}`",
        f"- Parent life domains: **{len(parent_rows)}**",
        f"- Mapped Instant taxonomy topics: **{len(actual_runtime_keys)}**",
        "- Muhurat modeled as QuestionOperation: **PASS**", "",
        "| Parent domain | Topic count | Topics |", "|---|---:|---|",
    ]
    for row in parent_rows:
        topics = row["topics"]
        report.append(
            f"| {row['label']} | {len(topics)} | "
            + ", ".join(f"`{topic['runtime_key']}`" for topic in topics)
            + " |"
        )
    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(
        f"Life-domain ontology valid: {len(parent_rows)} parents, "
        f"{len(actual_runtime_keys)} taxonomy topics, Muhurat separate"
    )
    print(f"Runtime bundle: {RUNTIME_PATH.relative_to(ROOT)}")
    print(f"Readable report: {REPORT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, json.JSONDecodeError) as exc:
        print(f"Life-domain ontology invalid: {exc}", file=sys.stderr)
        raise SystemExit(1)
