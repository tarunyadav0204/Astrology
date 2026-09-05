"""Read-only adapter for the compiled Travel, Relocation and Foreign Life policy."""
from __future__ import annotations
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Mapping

DEFAULT_BUNDLE = Path(__file__).resolve().parents[2] / "knowledge_graph" / "foreign_life_poc" / "foreign-life-runtime-preview.json"

@dataclass(frozen=True)
class ForeignGraphPolicy:
    runtime_key: str; ontology_resource: str; question_label: str; graph_tree: Mapping | None; answer_mode: str; answer_contract: str; evidence_policy: str; required_factors: tuple[str, ...]; default_exclusions: tuple[str, ...]; required_capabilities: tuple[str, ...]; guardrails: tuple[str, ...]; decision_rules: tuple[str, ...]; calculator_bindings: Mapping[str, str]
    @classmethod
    def from_dict(cls, key: str, value: Mapping) -> "ForeignGraphPolicy":
        return cls(key, str(value["ontology_resource"]), str(value.get("question_label") or value["ontology_resource"]), dict(value["graph_tree"]) if isinstance(value.get("graph_tree"), Mapping) else None, str(value["answer_mode"]), str(value["answer_contract"]), str(value["evidence_policy"]), tuple(value.get("required_factors", ())), tuple(value.get("default_exclusions", ())), tuple(value.get("required_capabilities", ())), tuple(value.get("guardrails", ())), tuple(value.get("decision_rules", ())), dict(value.get("calculator_bindings", {})))

class ForeignGraphPolicyStore:
    def __init__(self, bundle_path: Path | str = DEFAULT_BUNDLE) -> None:
        doc=json.loads(Path(bundle_path).read_text(encoding="utf-8")); self.ontology_version=str(doc["ontology_version"]); self._policies={k:ForeignGraphPolicy.from_dict(k,v) for k,v in doc["topics"].items()}
    def resolve(self, key: str) -> ForeignGraphPolicy | None: return self._policies.get(key)
    def runtime_keys(self) -> tuple[str, ...]: return tuple(sorted(self._policies))

@lru_cache(maxsize=1)
def default_foreign_graph_policy_store() -> ForeignGraphPolicyStore: return ForeignGraphPolicyStore()
