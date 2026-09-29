"""Deterministic synthesis of classical partner descriptors."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, Mapping

from .rules import PLANET_RULES, SIGN_RULES, SOURCES


CHANNELS = {
    "d1_seventh_sign": {"weight": 4.0, "independence": "d1_house"},
    "d1_occupant": {"weight": 4.5, "independence": "d1_occupant"},
    "d1_aspect": {"weight": 2.5, "independence": "d1_aspect"},
    "d1_seventh_lord": {"weight": 3.5, "independence": "d1_lord"},
    "d9_seventh_sign": {"weight": 2.5, "independence": "d9_house"},
    "d9_occupant": {"weight": 3.0, "independence": "d9_occupant"},
    "d9_aspect": {"weight": 1.75, "independence": "d9_aspect"},
    "d9_seventh_lord": {"weight": 2.5, "independence": "d9_lord"},
    "d9_d1_seventh_lord": {"weight": 2.5, "independence": "d9_d1_lord"},
    "darakaraka": {"weight": 2.0, "independence": "jaimini_dk"},
    "venus": {"weight": 1.5, "independence": "venus_karaka"},
}

# Source translations often use different English phrases for the same broad
# visual quality. These aliases prevent exact wording from blocking genuine
# repetition while retaining the original source-derived phrase for display.
APPEARANCE_CONCEPTS = {
    "square and structured": "structured_build",
    "rounded and soft": "soft_rounded_build",
    "rounded or substantial": "soft_rounded_build",
    "medium and soft": "soft_rounded_build",
    "lean and wiry": "lean_build",
    "lean and elongated": "lean_build",
    "slender and compact": "lean_build",
    "well-proportioned and youthful": "balanced_build",
    "graceful and well-proportioned": "balanced_build",
    "even and well-proportioned": "balanced_build",
    "medium and balanced": "balanced_build",
    "broad or substantial": "substantial_build",
    "prominent and substantial": "substantial_build",
    "large or commanding": "substantial_build",
    "large or strongly framed": "substantial_build",
    "solid and grounded": "substantial_build",
    "long or taller": "tall_stature",
    "taller or long-limbed": "tall_stature",
    "attractive and animated": "animated_presence",
    "lively and mobile": "animated_presence",
    "dignified and noticeable": "dignified_presence",
    "open and dignified": "dignified_presence",
    "warm and dignified": "dignified_presence",
    "graceful and socially polished": "polished_presence",
    "polished and attractive": "polished_presence",
    "serious and restrained": "restrained_presence",
    "restrained and grounded": "restrained_presence",
    "unusual or difficult to place": "distinctive_presence",
    "unusual or immediately distinctive": "distinctive_presence",
    "distinctive and self-contained": "distinctive_presence",
}


def _add_rule_signals(
    ledger: list[Dict[str, Any]], *, channel: str, factor: str, rule: Mapping[str, Any]
) -> None:
    channel_meta = CHANNELS[channel]
    for attribute, value in (rule.get("appearance") or {}).items():
        ledger.append({
            "attribute": attribute,
            "value": value,
            "concept": APPEARANCE_CONCEPTS.get(value, value),
            "weight": channel_meta["weight"],
            "independence": channel_meta["independence"],
            "channel": channel,
            "factor": factor,
            "source_id": rule.get("source_id"),
            "verse": rule.get("verse"),
        })


def _personality_signals(ledger: list[Dict[str, Any]], *, channel: str, factor: str, rule: Mapping[str, Any]) -> None:
    channel_meta = CHANNELS[channel]
    for value in (rule.get("personality") or rule.get("temperament") or []):
        ledger.append({
            "value": value,
            "weight": channel_meta["weight"],
            "independence": channel_meta["independence"],
            "channel": channel,
            "factor": factor,
            "source_id": rule.get("source_id"),
            "verse": rule.get("verse"),
        })


def _rank_appearance(ledger: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    by_attribute: dict[str, dict[str, list[Dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in ledger:
        by_attribute[row["attribute"]][row.get("concept") or row["value"]].append(row)
    result: Dict[str, Any] = {}
    for attribute, values in by_attribute.items():
        ranked = sorted(
            values.items(),
            key=lambda item: (
                len({r["independence"] for r in item[1]}),
                sum(float(r["weight"]) for r in item[1]),
            ),
            reverse=True,
        )
        candidates = []
        for _concept, evidence in ranked[:2]:
            independent = len({row["independence"] for row in evidence})
            # Keep the strongest original wording visible; the normalized concept
            # is only used to establish repetition across equivalent translations.
            display_row = max(evidence, key=lambda row: float(row["weight"]))
            candidates.append({
                "value": display_row["value"],
                "concept": display_row.get("concept") or display_row["value"],
                "confidence": "strong" if independent >= 3 else "moderate" if independent >= 2 else "suggestive",
                "independent_repetitions": independent,
                "evidence": evidence,
            })
        if candidates:
            result[attribute] = {
                "primary": candidates[0],
                "alternatives": candidates[1:],
            }
    return result


def _rank_personality(ledger: Iterable[Dict[str, Any]]) -> list[Dict[str, Any]]:
    grouped: dict[str, list[Dict[str, Any]]] = defaultdict(list)
    for row in ledger:
        grouped[row["value"]].append(row)
    ranked = sorted(
        grouped.items(),
        key=lambda item: (len({r["independence"] for r in item[1]}), sum(r["weight"] for r in item[1])),
        reverse=True,
    )
    return [
        {
            "trait": value,
            "confidence": "strong" if len({r["independence"] for r in rows}) >= 3 else "moderate" if len({r["independence"] for r in rows}) >= 2 else "suggestive",
            "independent_repetitions": len({r["independence"] for r in rows}),
            "evidence": rows,
        }
        for value, rows in ranked[:8]
    ]


def _factor_readings(
    appearance_ledger: Iterable[Dict[str, Any]],
    personality_ledger: Iterable[Dict[str, Any]],
) -> list[Dict[str, Any]]:
    """Expose the actual BPHS meaning contributed by every chart factor.

    The ranked result intentionally resolves competing descriptions.  This
    companion view retains the complete rule contribution so the UI can
    explain what a sign or graha gives instead of showing a bare placement.
    """
    grouped: dict[tuple[str, str, str | None, str | None], Dict[str, Any]] = {}

    def reading_for(row: Dict[str, Any]) -> Dict[str, Any]:
        key = (row["channel"], row["factor"], row.get("source_id"), row.get("verse"))
        if key not in grouped:
            grouped[key] = {
                "channel": row["channel"],
                "factor": row["factor"],
                "factor_type": "sign" if row["factor"] in SIGN_RULES else "planet",
                "appearance": [],
                "personality": [],
                "source_id": row.get("source_id"),
                "verse": row.get("verse"),
            }
        return grouped[key]

    for row in appearance_ledger:
        reading = reading_for(row)
        contribution = {"attribute": row["attribute"], "value": row["value"]}
        if contribution not in reading["appearance"]:
            reading["appearance"].append(contribution)

    for row in personality_ledger:
        reading = reading_for(row)
        if row["value"] not in reading["personality"]:
            reading["personality"].append(row["value"])

    return list(grouped.values())


def synthesize_partner_profile(evidence: Mapping[str, Any]) -> Dict[str, Any]:
    appearance_ledger: list[Dict[str, Any]] = []
    personality_ledger: list[Dict[str, Any]] = []
    d1 = evidence.get("d1") if isinstance(evidence.get("d1"), dict) else {}
    d9 = evidence.get("d9") if isinstance(evidence.get("d9"), dict) else {}

    def add_sign(channel: str, sign: Any) -> None:
        name = str(sign or "")
        rule = SIGN_RULES.get(name)
        if rule:
            _add_rule_signals(appearance_ledger, channel=channel, factor=name, rule=rule)
            _personality_signals(personality_ledger, channel=channel, factor=name, rule=rule)

    def add_planet(channel: str, row: Any) -> None:
        if not isinstance(row, dict):
            return
        planet = str(row.get("planet") or "")
        rule = PLANET_RULES.get(planet)
        if rule:
            _add_rule_signals(appearance_ledger, channel=channel, factor=planet, rule=rule)
            _personality_signals(personality_ledger, channel=channel, factor=planet, rule=rule)

    def add_planet_and_placement_sign(channel: str, row: Any) -> None:
        add_planet(channel, row)
        if isinstance(row, dict):
            add_sign(channel, row.get("sign"))

    add_sign("d1_seventh_sign", (d1.get("seventh_house") or {}).get("sign"))
    for row in d1.get("seventh_house_occupants") or []:
        add_planet("d1_occupant", row)
    for row in d1.get("seventh_house_aspectors") or []:
        add_planet("d1_aspect", row)
    add_planet_and_placement_sign("d1_seventh_lord", d1.get("seventh_lord"))
    add_sign("d9_seventh_sign", (d9.get("seventh_house") or {}).get("sign"))
    for row in d9.get("seventh_house_occupants") or []:
        add_planet("d9_occupant", row)
    for row in d9.get("seventh_house_aspectors") or []:
        add_planet("d9_aspect", row)
    add_planet_and_placement_sign("d9_seventh_lord", d9.get("seventh_lord"))
    add_planet_and_placement_sign("d9_d1_seventh_lord", d9.get("d1_seventh_lord"))
    add_planet_and_placement_sign("darakaraka", d1.get("darakaraka"))
    add_planet_and_placement_sign("venus", d1.get("venus"))

    appearance = _rank_appearance(appearance_ledger)
    personality = _rank_personality(personality_ledger)
    factor_readings = _factor_readings(appearance_ledger, personality_ledger)
    references = []
    used_sources = {row.get("source_id") for row in appearance_ledger + personality_ledger if row.get("source_id")}
    used_sources.add("bphs.seventh_house")
    used_sources.add("bphs.navamsa_scope")
    used_sources.add("bphs.chara_karakas")
    for source_id in sorted(used_sources):
        source = SOURCES.get(source_id)
        if source:
            references.append({"source_id": source_id, **source})

    strong_visuals = sum(1 for value in appearance.values() if (value.get("primary") or {}).get("confidence") in {"strong", "moderate"})
    return {
        "schema_version": "partner-profile/v1",
        "ruleset_version": "bphs-partner-portrait/1.0.0",
        "scope": "A birth-chart-guided portrait of likely partner traits; not an exact photograph or identification of a specific person.",
        "appearance": appearance,
        "personality": personality,
        "factor_readings": factor_readings,
        "evidence": evidence,
        "references": references,
        "portrait_readiness": "ready" if strong_visuals >= 2 else "limited",
        "method_note": (
            "The classical texts supply the rashi and graha descriptions. AstroRoshni's declared resolver ranks "
            "them by spouse relevance and independent repetition; the numerical weights are an implementation "
            "policy, not a verse from the classics."
        ),
    }
