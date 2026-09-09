"""Read-only policy store for the compiled Nakshatra Live ontology."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Mapping


DEFAULT_BUNDLE = Path(__file__).resolve().parents[2] / "knowledge_graph" / "nakshatra_poc" / "nakshatra-runtime-preview.json"


@dataclass(frozen=True)
class NakshatraGraphPolicy:
    runtime_key: str
    ontology_resource: str
    question_label: str
    graph_tree: Mapping | None
    answer_mode: str
    answer_contract: str
    evidence_policy: str
    required_factors: tuple[str, ...]
    default_exclusions: tuple[str, ...]
    required_capabilities: tuple[str, ...]
    guardrails: tuple[str, ...]
    decision_rules: tuple[str, ...]

    @classmethod
    def from_dict(cls, key: str, value: Mapping) -> "NakshatraGraphPolicy":
        return cls(
            runtime_key=key,
            ontology_resource=str(value["ontology_resource"]),
            question_label=str(value.get("question_label") or key.replace("_", " ").title()),
            graph_tree=dict(value["graph_tree"]) if isinstance(value.get("graph_tree"), Mapping) else None,
            answer_mode=str(value["answer_mode"]),
            answer_contract=str(value["answer_contract"]),
            evidence_policy=str(value["evidence_policy"]),
            required_factors=tuple(value.get("required_factors") or ()),
            default_exclusions=tuple(value.get("default_exclusions") or ()),
            required_capabilities=tuple(value.get("required_capabilities") or ()),
            guardrails=tuple(value.get("guardrails") or ()),
            decision_rules=tuple(value.get("decision_rules") or ()),
        )


class NakshatraGraphPolicyStore:
    def __init__(self, bundle_path: Path | str = DEFAULT_BUNDLE) -> None:
        document = json.loads(Path(bundle_path).read_text(encoding="utf-8"))
        self.ontology_version = str(document["ontology_version"])
        self._policies = {
            key: NakshatraGraphPolicy.from_dict(key, value)
            for key, value in document["topics"].items()
        }

    def resolve(self, key: str) -> NakshatraGraphPolicy | None:
        return self._policies.get(key)

    def runtime_keys(self) -> tuple[str, ...]:
        return tuple(sorted(self._policies))


@lru_cache(maxsize=1)
def default_nakshatra_graph_policy_store() -> NakshatraGraphPolicyStore:
    return NakshatraGraphPolicyStore()

