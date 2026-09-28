"""Discovery registry and coverage ledger for certified classical rule packs.

Every chapter owns its evaluator and capabilities. The registry discovers
``CHAPTER_*`` packs from work packages, which keeps product orchestration free
of chapter-specific imports and switches.
"""

from __future__ import annotations

from dataclasses import asdict
from importlib import import_module
from pkgutil import iter_modules
from types import ModuleType
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple


WORK_PACKAGES = ("classical_rules.bphs",)


def _chapter_packs(module: ModuleType) -> Iterable[Mapping[str, Any]]:
    for name, value in vars(module).items():
        if name.startswith("CHAPTER_") and isinstance(value, Mapping):
            yield value


def _validate_pack(pack: Mapping[str, Any], module_name: str) -> Tuple[str, int]:
    required = {
        "work_key", "work", "chapter", "title", "source_profile",
        "witness_url", "passage_groups", "rules", "coverage_provider",
        "evaluator", "contributes_reading_insights",
    }
    missing = sorted(required - set(pack))
    if missing:
        raise ValueError(f"Classical pack {module_name} is missing: {', '.join(missing)}")
    if not callable(pack["coverage_provider"]) or not callable(pack["evaluator"]):
        raise TypeError(f"Classical pack {module_name} providers must be callable")
    return str(pack["work_key"]).lower(), int(pack["chapter"])


def _discover_packs() -> Dict[Tuple[str, int], Mapping[str, Any]]:
    discovered: Dict[Tuple[str, int], Mapping[str, Any]] = {}
    for package_name in WORK_PACKAGES:
        package = import_module(package_name)
        for module_info in sorted(iter_modules(package.__path__), key=lambda row: row.name):
            if not module_info.name.startswith("chapter_") or module_info.name.endswith("_data"):
                continue
            module_name = f"{package_name}.{module_info.name}"
            module = import_module(module_name)
            for pack in _chapter_packs(module):
                key = _validate_pack(pack, module_name)
                if key in discovered:
                    raise ValueError(f"Duplicate classical pack registration for {key[0]} Chapter {key[1]}")
                discovered[key] = pack
    return dict(sorted(discovered.items()))


PACKS = _discover_packs()


def _coverage(pack: Mapping[str, Any]) -> Dict[str, Any]:
    return dict(pack["coverage_provider"]())


def iter_packs(*, reading_only: bool = False) -> Tuple[Tuple[Tuple[str, int], Mapping[str, Any]], ...]:
    rows = PACKS.items()
    if reading_only:
        rows = ((key, pack) for key, pack in rows if pack["contributes_reading_insights"])
    return tuple(rows)


def list_packs() -> Tuple[Dict[str, Any], ...]:
    return tuple({
        "work_key": work_key,
        "chapter": chapter,
        "title": pack["title"],
        "source_profile": pack["source_profile"],
        "rule_count": len(pack["rules"]),
        "contributes_reading_insights": bool(pack["contributes_reading_insights"]),
        "coverage": _coverage(pack),
    } for (work_key, chapter), pack in iter_packs())


def get_pack(work_key: str, chapter: int) -> Dict[str, Any]:
    key = (str(work_key).lower(), int(chapter))
    pack = PACKS.get(key)
    if not pack:
        raise KeyError(f"No certified classical rule pack is registered for {key[0]} Chapter {key[1]}")
    passage_groups = []
    for group in pack["passage_groups"]:
        row = asdict(group)
        if group.executable:
            row.update({
                "use_key": "rule_engine",
                "use_label": "Used by the rule engine",
                "usage_explanation": "The engine calculates this rule against a chart and returns its exact evidence.",
            })
        elif group.classification == "foundation":
            row.update({
                "use_key": "methodological_foundation",
                "use_label": "Methodological foundation",
                "usage_explanation": "This establishes how a valid chart must be constructed or interpreted. It does not produce a chart match or prediction by itself.",
            })
        elif group.classification == "doctrine_table":
            row.update({
                "use_key": "reference_knowledge",
                "use_label": "Reference knowledge",
                "usage_explanation": "This supplies classical meanings that another reviewed rule may use. It is not independently treated as a chart result.",
            })
        else:
            row.update({
                "use_key": "awaiting_operationalization",
                "use_label": "Not active yet",
                "usage_explanation": "The passage is source-mapped, but no reviewed deterministic rule currently uses it.",
            })
        passage_groups.append(row)
    return {
        "work_key": key[0],
        "work": pack["work"],
        "chapter": pack["chapter"],
        "title": pack["title"],
        "source_profile": pack["source_profile"],
        "witness_url": pack["witness_url"],
        "contributes_reading_insights": bool(pack["contributes_reading_insights"]),
        "coverage": _coverage(pack),
        "passage_groups": passage_groups,
        "rules": [rule.public_definition() for rule in pack["rules"]],
    }


def evaluate_pack(
    work_key: str,
    chapter: int,
    chart: Mapping[str, Any],
    birth_data: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    key = (str(work_key).lower(), int(chapter))
    pack = PACKS.get(key)
    if not pack:
        raise KeyError(f"No certified classical rule pack is registered for {key[0]} Chapter {key[1]}")
    return dict(pack["evaluator"](chart, birth_data))
