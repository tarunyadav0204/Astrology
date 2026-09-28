"""Corpus-wide classical chart reading aggregation.

Chapter packs publish normalized insights.  This module validates, deduplicates
and groups those insights without knowing any chapter's private result shape.
Source testimony is retained verbatim as structured evidence; conflicts are
shown as support and pressure rather than resolved by an invented score.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .registry import iter_packs


READING_CONTRACT_VERSION = "classical-reading/1.0.0"
_ALLOWED_CONDITIONS = {"supported", "mixed", "under_pressure", "unqualified"}


def _nonempty(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"Classical insight requires {field}")
    return text


def _unique_strings(values: Iterable[Any]) -> List[str]:
    rows: List[str] = []
    seen = set()
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.add(text)
            rows.append(text)
    return rows


def _condition(supports: Sequence[str], pressures: Sequence[str]) -> str:
    if supports and pressures:
        return "mixed"
    if supports:
        return "supported"
    if pressures:
        return "under_pressure"
    return "unqualified"


def _normalize_evidence(raw: Any, insight_id: str) -> Dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise ValueError(f"Classical insight {insight_id} requires structured evidence")
    summary = raw.get("summary")
    facts = raw.get("facts")
    if not isinstance(summary, Mapping):
        raise ValueError(f"Classical insight {insight_id} requires evidence.summary")
    if not isinstance(facts, (list, tuple)):
        raise ValueError(f"Classical insight {insight_id} requires evidence.facts")
    normalized_facts = []
    for index, fact in enumerate(facts, start=1):
        if not isinstance(fact, Mapping):
            raise TypeError(f"Classical insight {insight_id} evidence fact {index} must be an object")
        state = str(fact.get("state") or "neutral")
        if state not in {"support", "pressure", "neutral"}:
            raise ValueError(f"Classical insight {insight_id} evidence fact {index} has invalid state")
        normalized_facts.append({
            "key": _nonempty(fact.get("key"), f"{insight_id}.evidence.facts[{index}].key"),
            "label": _nonempty(fact.get("label"), f"{insight_id}.evidence.facts[{index}].label"),
            "value": _nonempty(fact.get("value"), f"{insight_id}.evidence.facts[{index}].value"),
            "state": state,
        })
    return {
        "summary": {
            "key": _nonempty(summary.get("key"), f"{insight_id}.evidence.summary.key"),
            "text": _nonempty(summary.get("text"), f"{insight_id}.evidence.summary.text"),
            "parameters": dict(summary.get("parameters") or {}),
        },
        "facts": normalized_facts,
        "raw": deepcopy(dict(raw.get("raw") or {})),
    }


def normalize_insight(
    raw: Mapping[str, Any], *, work_key: str, chapter: int, pack_title: str,
) -> Dict[str, Any]:
    """Validate the stable contract at the pack boundary.

    A malformed published pack is a programming/publication error and fails
    loudly.  It is never converted into an empty result or fallback prose.
    """
    if not isinstance(raw, Mapping):
        raise TypeError("Published classical insight must be an object")
    insight_id = _nonempty(raw.get("insight_id"), "insight_id")
    area = raw.get("area")
    subject = raw.get("subject")
    if not isinstance(area, Mapping) or not isinstance(subject, Mapping):
        raise ValueError(f"Classical insight {insight_id} requires area and subject objects")
    area_key = _nonempty(area.get("key"), f"{insight_id}.area.key")
    subject_key = _nonempty(subject.get("key"), f"{insight_id}.subject.key")
    statements = raw.get("statements")
    if not isinstance(statements, (list, tuple)) or not statements:
        raise ValueError(f"Classical insight {insight_id} requires at least one statement")
    normalized_statements = []
    for index, statement in enumerate(statements, start=1):
        if not isinstance(statement, Mapping):
            raise TypeError(f"Classical insight {insight_id} statement {index} must be an object")
        normalized_statements.append({
            "key": _nonempty(statement.get("key"), f"{insight_id}.statements[{index}].key"),
            "text": _nonempty(statement.get("text"), f"{insight_id}.statements[{index}].text"),
            "parameters": dict(statement.get("parameters") or {}),
        })
    sources = raw.get("sources")
    if not isinstance(sources, (list, tuple)) or not sources:
        raise ValueError(f"Classical insight {insight_id} requires at least one source")
    normalized_sources = []
    for source in sources:
        if not isinstance(source, Mapping):
            raise TypeError(f"Classical insight {insight_id} source must be an object")
        normalized_sources.append({
            **dict(source),
            "rule_key": _nonempty(source.get("rule_key"), f"{insight_id}.source.rule_key"),
            "reference": _nonempty(source.get("reference"), f"{insight_id}.source.reference"),
            "witness_url": _nonempty(source.get("witness_url"), f"{insight_id}.source.witness_url"),
        })
    normalized_controls = []
    for control in raw.get("controls") or ():
        if not isinstance(control, Mapping):
            raise TypeError(f"Classical insight {insight_id} control must be an object")
        normalized_controls.append({
            "key": _nonempty(control.get("key"), f"{insight_id}.control.key"),
            "reference": _nonempty(control.get("reference"), f"{insight_id}.control.reference"),
            "text": _nonempty(control.get("text"), f"{insight_id}.control.text"),
            "witness_url": _nonempty(control.get("witness_url"), f"{insight_id}.control.witness_url"),
        })
    supports = _unique_strings(raw.get("supports") or ())
    pressures = _unique_strings(raw.get("pressures") or ())
    declared_condition = str(raw.get("condition") or _condition(supports, pressures))
    if declared_condition not in _ALLOWED_CONDITIONS:
        raise ValueError(f"Classical insight {insight_id} has unsupported condition {declared_condition!r}")
    # The visible condition is derived from the testimony arrays so a pack
    # cannot label pressure as support while returning contrary evidence.
    visible_condition = _condition(supports, pressures)
    evidence = _normalize_evidence(raw.get("evidence"), insight_id)
    normalized = {
        "insight_id": insight_id,
        "insight_ids": [insight_id],
        "dedupe_key": _nonempty(raw.get("dedupe_key") or insight_id, f"{insight_id}.dedupe_key"),
        "area": {
            "key": area_key,
            "house": int(area["house"]) if area.get("house") is not None else None,
            "order": int(area.get("order") or 999),
            "label": _nonempty(area.get("label"), f"{insight_id}.area.label"),
            "label_key": str(area.get("label_key") or ""),
        },
        "subject": {
            "key": subject_key,
            "label": _nonempty(subject.get("label"), f"{insight_id}.subject.label"),
            "label_key": str(subject.get("label_key") or ""),
        },
        "kind": _nonempty(raw.get("kind"), f"{insight_id}.kind"),
        "priority": int(raw.get("priority") or 0),
        "title": _nonempty(raw.get("title"), f"{insight_id}.title"),
        "title_key": str(raw.get("title_key") or ""),
        "statements": normalized_statements,
        "condition": visible_condition,
        "supports": supports,
        "pressures": pressures,
        "sources": normalized_sources,
        "controls": normalized_controls,
        "contributions": [{
            "insight_id": insight_id,
            "work_key": work_key,
            "chapter": chapter,
            "pack_title": pack_title,
            "evidence": evidence,
            "sources": deepcopy(normalized_sources),
        }],
    }
    return normalized


def _unique_dicts(rows: Iterable[Mapping[str, Any]], identity) -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    seen = set()
    for row in rows:
        key = identity(row)
        if key in seen:
            continue
        seen.add(key)
        output.append(dict(row))
    return output


def merge_insights(insights: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Merge only author-declared semantic duplicates.

    A shared ``dedupe_key`` is an explicit publication decision.  Unrelated
    rules in the same life area remain separate indications.
    """
    merged: Dict[str, Dict[str, Any]] = {}
    for incoming_raw in insights:
        incoming = deepcopy(dict(incoming_raw))
        key = incoming["dedupe_key"]
        current = merged.get(key)
        if current is None:
            merged[key] = incoming
            continue
        if current["area"]["key"] != incoming["area"]["key"] or current["subject"]["key"] != incoming["subject"]["key"]:
            raise ValueError(f"Classical dedupe key {key} spans different areas or subjects")
        current["insight_ids"] = _unique_strings((*current["insight_ids"], *incoming["insight_ids"]))
        current["statements"] = _unique_dicts(
            (*current["statements"], *incoming["statements"]),
            lambda row: (row.get("key"), row.get("text")),
        )
        current["supports"] = _unique_strings((*current["supports"], *incoming["supports"]))
        current["pressures"] = _unique_strings((*current["pressures"], *incoming["pressures"]))
        current["condition"] = _condition(current["supports"], current["pressures"])
        current["sources"] = _unique_dicts(
            (*current["sources"], *incoming["sources"]),
            lambda row: (row.get("rule_key"), row.get("reference"), row.get("witness_url")),
        )
        current["controls"] = _unique_dicts(
            (*current["controls"], *incoming["controls"]),
            lambda row: (row.get("key"), row.get("reference")),
        )
        current["contributions"].extend(incoming["contributions"])
        current["priority"] = max(int(current["priority"]), int(incoming["priority"]))
    return sorted(merged.values(), key=lambda row: (-int(row["priority"]), row["dedupe_key"]))


def group_insights(insights: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    areas: Dict[str, Dict[str, Any]] = {}
    for insight in merge_insights(insights):
        area_meta = insight["area"]
        area = areas.setdefault(area_meta["key"], {
            **deepcopy(area_meta),
            "insights": [],
        })
        if any(area[field] != area_meta[field] for field in ("house", "order", "label", "label_key")):
            raise ValueError(f"Conflicting classical area metadata for {area_meta['key']}")
        area["insights"].append(insight)

    output = []
    for area in areas.values():
        area["insights"].sort(key=lambda row: (-int(row["priority"]), row["dedupe_key"]))
        area["supports"] = _unique_strings(
            value for insight in area["insights"] for value in insight["supports"]
        )
        area["pressures"] = _unique_strings(
            value for insight in area["insights"] for value in insight["pressures"]
        )
        area["condition"] = _condition(area["supports"], area["pressures"])
        area["sources"] = _unique_dicts(
            (source for insight in area["insights"] for source in insight["sources"]),
            lambda row: (row.get("rule_key"), row.get("reference"), row.get("witness_url")),
        )
        area["subjects"] = [
            {
                "key": subject_key,
                "label": subject_rows[0]["subject"]["label"],
                "label_key": subject_rows[0]["subject"]["label_key"],
                "insight_ids": [row["insight_id"] for row in subject_rows],
            }
            for subject_key, subject_rows in _group_by_subject(area["insights"])
        ]
        area["insight_count"] = len(area["insights"])
        area["source_count"] = len(area["sources"])
        output.append(area)
    return sorted(output, key=lambda row: (int(row["order"]), row["key"]))


def _group_by_subject(insights: Sequence[Mapping[str, Any]]) -> List[Tuple[str, List[Mapping[str, Any]]]]:
    grouped: Dict[str, List[Mapping[str, Any]]] = {}
    for insight in insights:
        grouped.setdefault(str(insight["subject"]["key"]), []).append(insight)
    return list(grouped.items())


def build_classical_reading(
    chart: Mapping[str, Any],
    birth_data: Optional[Mapping[str, Any]] = None,
    area_keys: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    requested_areas = {str(key) for key in (area_keys or ()) if str(key)}
    normalized: List[Dict[str, Any]] = []
    evaluated_packs = []
    for (work_key, chapter), pack in iter_packs(reading_only=True):
        result = pack["evaluator"](chart, birth_data)
        raw_insights = result.get("insights")
        if not isinstance(raw_insights, list):
            raise ValueError(f"Published reading pack {work_key} Chapter {chapter} did not return insights")
        pack_rows = [
            normalize_insight(row, work_key=work_key, chapter=chapter, pack_title=str(pack["title"]))
            for row in raw_insights
        ]
        if requested_areas:
            pack_rows = [row for row in pack_rows if row["area"]["key"] in requested_areas]
        normalized.extend(pack_rows)
        evaluated_packs.append({
            "work_key": work_key,
            "work": pack["work"],
            "chapter": chapter,
            "title": pack["title"],
            "source_profile": pack["source_profile"],
            "pack_version": result.get("pack_version"),
            "insight_count": len(pack_rows),
        })
    areas = group_insights(normalized)
    return {
        "contract_version": READING_CONTRACT_VERSION,
        "engine_version": "classical-rule-engine/1.0.0",
        "method": "All published reading-capable classical packs; grouped by life area and subject",
        "areas": areas,
        "area_count": len(areas),
        "insight_count": sum(area["insight_count"] for area in areas),
        "source_count": len({
            (source.get("rule_key"), source.get("reference"), source.get("witness_url"))
            for area in areas for source in area["sources"]
        }),
        "packs_evaluated": evaluated_packs,
        "fallback_used": False,
    }
