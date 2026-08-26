"""Read-only adapter for the compiled Career ontology policy bundle.

The production request path must never query WebProtege. The authoring graph is
validated and compiled ahead of time; this adapter provides deterministic,
constant-time lookup for the live Instant Career graph contract.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping


DEFAULT_BUNDLE = (
    Path(__file__).resolve().parents[2]
    / "knowledge_graph"
    / "career_poc"
    / "career-runtime-preview.json"
)


@dataclass(frozen=True)
class CareerGraphPolicy:
    runtime_key: str
    ontology_resource: str
    question_label: str
    graph_tree: Mapping[str, Any] | None
    answer_mode: str
    answer_contract: str
    evidence_policy: str
    required_factors: tuple[str, ...]
    default_exclusions: tuple[str, ...]
    required_capabilities: tuple[str, ...]
    guardrails: tuple[str, ...]
    decision_rules: tuple[str, ...]
    calculator_bindings: Mapping[str, str]
    override_condition: str | None = None

    @classmethod
    def from_dict(cls, runtime_key: str, value: Mapping[str, Any]) -> "CareerGraphPolicy":
        return cls(
            runtime_key=runtime_key,
            ontology_resource=str(value["ontology_resource"]),
            question_label=str(value.get("question_label") or value["ontology_resource"]),
            graph_tree=(
                dict(value["graph_tree"])
                if isinstance(value.get("graph_tree"), Mapping)
                else None
            ),
            answer_mode=str(value["answer_mode"]),
            answer_contract=str(value["answer_contract"]),
            evidence_policy=str(value["evidence_policy"]),
            required_factors=tuple(value.get("required_factors", ())),
            default_exclusions=tuple(value.get("default_exclusions", ())),
            required_capabilities=tuple(value.get("required_capabilities", ())),
            guardrails=tuple(value.get("guardrails", ())),
            decision_rules=tuple(value.get("decision_rules", ())),
            calculator_bindings=dict(value.get("calculator_bindings", {})),
            override_condition=value.get("override_condition"),
        )


class CareerGraphPolicyStore:
    def __init__(self, bundle_path: Path | str = DEFAULT_BUNDLE) -> None:
        self.bundle_path = Path(bundle_path)
        document = json.loads(self.bundle_path.read_text(encoding="utf-8"))
        self.ontology_version = str(document["ontology_version"])
        self._policies = {
            key: CareerGraphPolicy.from_dict(key, value)
            for key, value in document["topics"].items()
        }

    def resolve(self, runtime_key: str) -> CareerGraphPolicy | None:
        return self._policies.get(runtime_key)

    def require(self, runtime_key: str) -> CareerGraphPolicy:
        policy = self.resolve(runtime_key)
        if policy is None:
            raise KeyError(f"Unknown Career ontology runtime key: {runtime_key}")
        return policy

    def runtime_keys(self) -> tuple[str, ...]:
        return tuple(sorted(self._policies))


@lru_cache(maxsize=1)
def default_career_graph_policy_store() -> CareerGraphPolicyStore:
    return CareerGraphPolicyStore()
