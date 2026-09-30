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
    "spouse_karaka": {"weight": 1.5, "independence": "spouse_karaka"},
}

RULESET_VERSION = "bphs-partner-portrait/1.4.0"

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
    "fair or light complexion": "light_complexion",
    "fair or light golden complexion": "light_complexion",
    "warm reddish-brown complexion": "warm_complexion",
    "warm reddish complexion": "warm_complexion",
    "olive or dusky complexion": "dusky_complexion",
    "brown or dusky complexion": "dusky_complexion",
    "dark complexion": "dark_complexion",
}


def _planet_condition(row: Mapping[str, Any]) -> Dict[str, Any]:
    """Qualify how clearly a graha can deliver its natural description.

    The classics supply the dignity and cancellation conditions. The numeric
    factors are an explicit resolver policy used only to rank competing
    descriptions; they are not presented as classical points.
    """
    dignity = str(row.get("dignity") or "neutral").strip().lower()
    neecha_bhanga = bool(row.get("neecha_bhanga"))
    combust = bool(row.get("combust"))
    # BPHS 45.5-6 qualifies a debilitated graha's capacity to deliver results;
    # it does not state that the graha ceases to signify its classical form.
    # Keep that testimony visible at reduced resolver weight. Neecha Bhanga
    # removes this particular reduction without inventing extra appearance.
    dignity_factor = {
        "exalted": 1.20,
        "moolatrikona": 1.12,
        "own_sign": 1.08,
        "favorable": 1.04,
        "friendly": 1.04,
        "neutral": 1.00,
        "unfavorable": 0.85,
        "enemy": 0.85,
        # Cancellation mitigates debilitation; it does not make the graha
        # exalted or erase the natal fact that it occupies its fall sign.
        "debilitated": 0.80 if neecha_bhanga else 0.55,
    }.get(dignity, 1.00)
    combustion_factor = 0.80 if combust else 1.00
    factor = dignity_factor * combustion_factor
    if dignity == "debilitated" and neecha_bhanga:
        state = "debilitation_cancelled"
    elif dignity == "debilitated":
        state = "debilitated"
    elif combust:
        state = "combust"
    elif dignity in {"exalted", "moolatrikona", "own_sign", "favorable", "friendly"}:
        state = "supported"
    else:
        state = "ordinary"
    return {
        "dignity": dignity,
        "neecha_bhanga": neecha_bhanga,
        "neecha_bhanga_rules": list(row.get("neecha_bhanga_rules") or []),
        "neecha_bhanga_source": row.get("neecha_bhanga_source"),
        "combust": combust,
        "condition_state": state,
        "condition_factor": round(factor, 4),
    }


def _add_rule_signals(
    ledger: list[Dict[str, Any]], *, channel: str, factor: str, rule: Mapping[str, Any],
    condition: Mapping[str, Any] | None = None,
) -> None:
    channel_meta = CHANNELS[channel]
    condition = dict(condition or {})
    condition_factor = float(condition.get("condition_factor", 1.0))
    for attribute, value in (rule.get("appearance") or {}).items():
        attribute_sources = rule.get("appearance_sources") or {}
        attribute_verses = rule.get("appearance_verses") or {}
        ledger.append({
            "attribute": attribute,
            "value": value,
            "concept": APPEARANCE_CONCEPTS.get(value, value),
            "weight": channel_meta["weight"] * condition_factor,
            "base_weight": channel_meta["weight"],
            "independence": channel_meta["independence"],
            "channel": channel,
            "factor": factor,
            "source_id": attribute_sources.get(attribute) or rule.get("source_id"),
            "verse": attribute_verses.get(attribute) or rule.get("verse"),
            **condition,
        })


def _personality_signals(
    ledger: list[Dict[str, Any]], *, channel: str, factor: str, rule: Mapping[str, Any],
    condition: Mapping[str, Any] | None = None,
) -> None:
    channel_meta = CHANNELS[channel]
    condition = dict(condition or {})
    condition_factor = float(condition.get("condition_factor", 1.0))
    for value in (rule.get("personality") or rule.get("temperament") or []):
        ledger.append({
            "value": value,
            "weight": channel_meta["weight"] * condition_factor,
            "base_weight": channel_meta["weight"],
            "independence": channel_meta["independence"],
            "channel": channel,
            "factor": factor,
            "source_id": rule.get("source_id"),
            "verse": rule.get("verse"),
            **condition,
        })


def _effective_repetitions(rows: Iterable[Dict[str, Any]]) -> float:
    strongest_by_channel: dict[str, float] = {}
    for row in rows:
        independence = str(row["independence"])
        strongest_by_channel[independence] = max(
            strongest_by_channel.get(independence, 0.0),
            min(1.0, float(row.get("condition_factor", 1.0))),
        )
    return sum(strongest_by_channel.values())


def _confidence(rows: Iterable[Dict[str, Any]]) -> str:
    effective = _effective_repetitions(rows)
    if effective >= 2.5:
        return "strong"
    if effective >= 1.5:
        return "moderate"
    return "suggestive"


def _rank_appearance(ledger: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    by_attribute: dict[str, dict[str, list[Dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in ledger:
        by_attribute[row["attribute"]][row.get("concept") or row["value"]].append(row)
    result: Dict[str, Any] = {}
    for attribute, values in by_attribute.items():
        ranked = sorted(
            values.items(),
            key=lambda item: (
                sum(float(r["weight"]) for r in item[1]),
                _effective_repetitions(item[1]),
                len({r["independence"] for r in item[1]}),
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
                "confidence": _confidence(evidence),
                "independent_repetitions": independent,
                "effective_repetitions": round(_effective_repetitions(evidence), 2),
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
        key=lambda item: (sum(r["weight"] for r in item[1]), _effective_repetitions(item[1])),
        reverse=True,
    )
    return [
        {
            "trait": value,
            "confidence": _confidence(rows),
            "independent_repetitions": len({r["independence"] for r in rows}),
            "effective_repetitions": round(_effective_repetitions(rows), 2),
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
                "dignity": row.get("dignity"),
                "neecha_bhanga": bool(row.get("neecha_bhanga")),
                "neecha_bhanga_rules": list(row.get("neecha_bhanga_rules") or []),
                "neecha_bhanga_source": row.get("neecha_bhanga_source"),
                "combust": bool(row.get("combust")),
                "condition_state": row.get("condition_state"),
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


def _summary_factor_type(factor: str) -> str:
    return "sign" if factor in SIGN_RULES else "planet"


def _resolved_summary(
    appearance: Mapping[str, Any],
    personality: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    """Build a consumer-ready summary from the same resolved evidence ledger.

    This is deliberately structured instead of prose so every client can
    localize it. Raw alternatives remain available only as explained
    resolutions; they never become simultaneous image instructions.
    """

    appearance_rows: list[Dict[str, Any]] = []
    personality_rows: list[Dict[str, Any]] = []
    conflicts: list[Dict[str, Any]] = []
    factor_scores: dict[str, Dict[str, Any]] = {}

    def factor_bucket(row: Mapping[str, Any]) -> Dict[str, Any]:
        factor = str(row.get("factor") or "")
        bucket = factor_scores.setdefault(factor, {
            "factor": factor,
            "factor_type": _summary_factor_type(factor),
            "score": 0.0,
            "appearance": [],
            "personality": [],
            "channels": [],
            "condition_state": row.get("condition_state"),
            "dignity": row.get("dignity"),
        })
        if row.get("channel") and row["channel"] not in bucket["channels"]:
            bucket["channels"].append(row["channel"])
        return bucket

    for attribute, result in appearance.items():
        if not isinstance(result, Mapping):
            continue
        primary = result.get("primary")
        if not isinstance(primary, Mapping) or not primary.get("value"):
            continue
        evidence = list(primary.get("evidence") or [])
        factors = list(dict.fromkeys(str(row.get("factor")) for row in evidence if row.get("factor")))
        appearance_rows.append({
            "attribute": attribute,
            "value": primary["value"],
            "confidence": primary.get("confidence"),
            "factors": factors,
        })
        for row in evidence:
            bucket = factor_bucket(row)
            contribution = {"attribute": attribute, "value": primary["value"]}
            if contribution not in bucket["appearance"]:
                bucket["appearance"].append(contribution)
                bucket["score"] += float(row.get("weight", 0.0))

        alternatives = [row for row in result.get("alternatives") or [] if isinstance(row, Mapping) and row.get("value")]
        if alternatives:
            alternative = alternatives[0]
            alternative_evidence = list(alternative.get("evidence") or [])
            conflicts.append({
                "attribute": attribute,
                "selected": primary["value"],
                "alternative": alternative["value"],
                "selected_factors": factors,
                "alternative_factors": list(dict.fromkeys(
                    str(row.get("factor")) for row in alternative_evidence if row.get("factor")
                )),
                "selected_support": primary.get("effective_repetitions"),
                "alternative_support": alternative.get("effective_repetitions"),
            })

    for item in list(personality)[:4]:
        if not isinstance(item, Mapping) or not item.get("trait"):
            continue
        evidence = list(item.get("evidence") or [])
        factors = list(dict.fromkeys(str(row.get("factor")) for row in evidence if row.get("factor")))
        personality_rows.append({
            "trait": item["trait"],
            "confidence": item.get("confidence"),
            "factors": factors,
        })
        for row in evidence:
            bucket = factor_bucket(row)
            if item["trait"] not in bucket["personality"]:
                bucket["personality"].append(item["trait"])
                bucket["score"] += float(row.get("weight", 0.0))

    ranked_factors = sorted(
        (row for factor, row in factor_scores.items() if factor),
        key=lambda row: (row["score"], len(row["channels"])),
        reverse=True,
    )
    public_factors = [{key: value for key, value in row.items() if key != "score"} for row in ranked_factors[:5]]
    return {
        "appearance": appearance_rows,
        "personality": personality_rows,
        "dominant_factors": public_factors[:3],
        "secondary_factors": public_factors[3:],
        "conflicts_resolved": conflicts,
    }


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
            condition = _planet_condition(row)
            _add_rule_signals(appearance_ledger, channel=channel, factor=planet, rule=rule, condition=condition)
            _personality_signals(personality_ledger, channel=channel, factor=planet, rule=rule, condition=condition)

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
    add_planet_and_placement_sign("spouse_karaka", d1.get("spouse_karaka") or d1.get("venus"))

    appearance = _rank_appearance(appearance_ledger)
    personality = _rank_personality(personality_ledger)
    factor_readings = _factor_readings(appearance_ledger, personality_ledger)
    resolved_summary = _resolved_summary(appearance, personality)
    references = []
    used_sources = {row.get("source_id") for row in appearance_ledger + personality_ledger if row.get("source_id")}
    if any(row.get("condition_state") == "debilitated" for row in appearance_ledger + personality_ledger):
        used_sources.add("bphs.graha_states")
    if any(row.get("neecha_bhanga") for row in appearance_ledger + personality_ledger):
        used_sources.add("phaladeepika.neecha_bhanga")
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
        "ruleset_version": RULESET_VERSION,
        "scope": "A birth-chart-guided portrait of likely partner traits; not an exact photograph or identification of a specific person.",
        "appearance": appearance,
        "personality": personality,
        "factor_readings": factor_readings,
        "resolved_summary": resolved_summary,
        "evidence": evidence,
        "references": references,
        "portrait_readiness": "ready" if strong_visuals >= 2 else "limited",
        "method_note": (
            "The classical texts supply the rashi and graha descriptions. Debilitation weakens how prominently "
            "a graha's description is used; a matched Phaladeepika 7.26-30 Neecha Bhanga condition mitigates, "
            "but does not reverse, that reduction. AstroRoshni's declared resolver ranks the descriptions by spouse relevance "
            "and independent repetition; the numerical weights are an implementation policy, not a verse from the classics."
        ),
    }
