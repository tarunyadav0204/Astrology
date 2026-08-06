"""KP houses-giving-results for today / this hour.

Algorithm (product-agreed):
  Base eligible   = natal houses signified by current AD or PD (MD alone is not enough)
  Today eligible  = Base ∩ Sookshma houses
  Hour eligible   = Base ∩ Sookshma ∩ Prana houses
                    (soft fallback without Prana if empty)
  Today results   = Today eligible ∩ day ruling planets (Day Lord + Moon Star Lord)
  Hour results    = Hour eligible ∩ moment ruling planets (Asc/Moon star+sub + Day Lord)
  Today ⊇ Hour    = any house giving results this hour is also counted for today
                    (hour is part of the day; Asc/Moon sub can confirm what day RPs miss)
  Manifestations  = one combined theme per subject (self/spouse/mother/father)
                    from primary activated houses → shared cache or LLM
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

from shared.dasha_calculator import DashaCalculator
from prediction_engine.house_significations import (
    HOUSE_SIGNIFICATIONS,
    relative_house_for_native,
)
from prediction_engine.subjects import SUBJECTS
from prediction_engine.contracts import Polarity
from prediction_engine.manifestation_synthesis import synthesize_manifestations
from utils.timezone_service import parse_timezone_offset

logger = logging.getLogger(__name__)

from ..utils.kp_calculations import KPCalculations
from .chart_service import KPChartService

# Same subject set as Activation Explorer / Combined Life Themes — shared LLM cache.
KP_MANIFESTATION_SUBJECTS = ("self", "spouse", "mother", "father")

DUSTHANA = {6, 8, 12}
FULFILLMENT = {11}

DAY_RP_KEYS = ("day_lord", "moon_star_lord")
HOUR_RP_KEYS = (
    "day_lord",
    "asc_star_lord",
    "asc_sub_lord",
    "moon_star_lord",
    "moon_sub_lord",
)

RP_ROLE_LABELS = {
    "day_lord": "Day Lord",
    "moon_star_lord": "Moon Star Lord",
    "moon_sign_lord": "Moon Sign Lord",
    "asc_star_lord": "Ascendant Star Lord",
    "asc_sub_lord": "Ascendant Sub Lord",
    "moon_sub_lord": "Moon Sub Lord",
}

DASHA_LEVEL_LABELS = {
    "mahadasha": "Mahadasha",
    "antardasha": "Antardasha",
    "pratyantardasha": "Pratyantardasha",
    "sookshma": "Sookshma",
    "prana": "Prana",
}


def _planet(value: Any) -> str:
    if isinstance(value, Mapping):
        return str(value.get("planet") or "").strip()
    return str(value or "").strip()


def _normalize_planet_sigs(raw: Mapping[Any, Any]) -> Dict[str, List[int]]:
    out: Dict[str, List[int]] = {}
    for planet, houses in (raw or {}).items():
        key = str(planet).strip()
        if not key or key == "Ascendant":
            continue
        cleaned: List[int] = []
        for house in houses or []:
            try:
                h = int(house)
            except (TypeError, ValueError):
                continue
            if 1 <= h <= 12:
                cleaned.append(h)
        out[key] = sorted(set(cleaned))
    return out


def _houses_for_planets(
    planets: Iterable[str],
    planet_sigs: Mapping[str, Sequence[int]],
) -> Dict[int, List[str]]:
    by_house: Dict[int, List[str]] = {}
    for planet in planets:
        name = str(planet or "").strip()
        if not name:
            continue
        for house in planet_sigs.get(name, []):
            bucket = by_house.setdefault(int(house), [])
            if name not in bucket:
                bucket.append(name)
    return by_house


def _tone_for_house(
    house: int,
    activating_rps: Sequence[str],
    planet_sigs: Mapping[str, Sequence[int]],
) -> str:
    return _tone_evidence(house, activating_rps, planet_sigs)["tone"]


def _tone_evidence(
    house: int,
    activating_rps: Sequence[str],
    planet_sigs: Mapping[str, Sequence[int]],
) -> Dict[str, Any]:
    linked_by_planet = {
        str(planet): sorted(int(h) for h in planet_sigs.get(planet, []))
        for planet in activating_rps
        if planet
    }
    linked: Set[int] = set()
    for houses in linked_by_planet.values():
        linked.update(houses)
    dusthana_hit = sorted(linked & DUSTHANA)
    fulfillment_hit = sorted(linked & FULFILLMENT)
    has_fulfillment = bool(fulfillment_hit)
    has_dusthana = bool(dusthana_hit)

    if house in DUSTHANA:
        tone = Polarity.MIXED.value if has_fulfillment else Polarity.CHALLENGING.value
        reason = (
            f"H{house} is a dusthana; activating RPs also link 11 → mixed."
            if has_fulfillment
            else f"H{house} is a dusthana and activating RPs do not bring 11 → challenging."
        )
    elif has_dusthana and has_fulfillment:
        tone = Polarity.MIXED.value
        reason = (
            f"Activating RPs link both fulfilment (H{', H'.join(map(str, fulfillment_hit))}) "
            f"and dusthana (H{', H'.join(map(str, dusthana_hit))}) → mixed."
        )
    elif has_dusthana:
        tone = Polarity.CHALLENGING.value
        reason = (
            f"Activating RPs also signify dusthana H{', H'.join(map(str, dusthana_hit))} "
            f"without H11 → challenging."
        )
    elif has_fulfillment or house in {1, 2, 4, 5, 7, 9, 10, 11}:
        tone = Polarity.SUPPORTIVE.value
        reason = (
            f"Activating RPs link H11 → supportive."
            if has_fulfillment
            else f"H{house} is treated as a constructive life area and no dusthana link → supportive."
        )
    else:
        tone = Polarity.NEUTRAL.value
        reason = "No clear fulfilment or dusthana signal from activating RPs → neutral."

    return {
        "tone": tone,
        "reason": reason,
        "linked_houses": sorted(linked),
        "dusthana_houses": dusthana_hit,
        "fulfillment_houses": fulfillment_hit,
        "linked_by_planet": linked_by_planet,
    }


def _roles_for_planet(planet: str, role_map: Mapping[str, str]) -> List[str]:
    name = str(planet or "").strip()
    if not name:
        return []
    return [
        RP_ROLE_LABELS.get(key, key)
        for key, value in role_map.items()
        if str(value or "").strip() == name and key in RP_ROLE_LABELS
    ]


def _dasha_hits_for_house(
    house: int,
    *,
    md: str,
    ad: str,
    pd: str,
    sk: str,
    pr: str,
    planet_sigs: Mapping[str, Sequence[int]],
) -> List[Dict[str, Any]]:
    hits: List[Dict[str, Any]] = []
    for level, planet in (
        ("mahadasha", md),
        ("antardasha", ad),
        ("pratyantardasha", pd),
        ("sookshma", sk),
        ("prana", pr),
    ):
        houses = [int(h) for h in planet_sigs.get(planet, [])]
        if house in houses:
            hits.append({
                "level": level,
                "label": DASHA_LEVEL_LABELS.get(level, level),
                "planet": planet,
                "planet_houses": houses,
                "counts_for_base": level in {"antardasha", "pratyantardasha"},
                "counts_for_sookshma_gate": level == "sookshma",
                "counts_for_prana_gate": level == "prana",
            })
    return hits


def _build_house_calculation(
    *,
    house: int,
    tier: str,
    activating_rps: Sequence[str],
    role_map: Mapping[str, str],
    anchors: Sequence[str],
    planet_sigs: Mapping[str, Sequence[int]],
    md: str,
    ad: str,
    pd: str,
    sk: str,
    pr: str,
    base_eligible: Set[int],
    sk_houses: Set[int],
    pr_houses: Set[int],
    eligible: Set[int],
    scope: str,
    prana_fallback: bool,
) -> Dict[str, Any]:
    dasha_hits = _dasha_hits_for_house(
        house, md=md, ad=ad, pd=pd, sk=sk, pr=pr, planet_sigs=planet_sigs
    )
    in_base = house in base_eligible
    in_sk = house in sk_houses
    in_pr = house in pr_houses
    in_eligible = house in eligible
    rp_roles = [
        {
            "planet": planet,
            "roles": _roles_for_planet(planet, role_map),
            "natal_houses": sorted(int(h) for h in planet_sigs.get(planet, [])),
        }
        for planet in activating_rps
    ]
    anchor_set = {str(a) for a in anchors if a}
    anchored_by = [p for p in activating_rps if p in anchor_set]
    multi_rp = len(list(dict.fromkeys(activating_rps))) >= 2
    if multi_rp:
        tier_reason = f"Signified by {len(activating_rps)} ruling planets → primary."
    elif anchored_by:
        tier_reason = (
            f"Signified by anchor RP {', '.join(anchored_by)} "
            f"({'Moon Star Lord' if scope == 'today' else 'Asc/Moon Star Lord'}) → primary."
        )
    else:
        tier_reason = "Only non-anchor RP (e.g. Day Lord alone) → secondary / background."

    tone_info = _tone_evidence(house, activating_rps, planet_sigs)

    gate_lines = [
        f"Base (AD∪PD): {'pass' if in_base else 'fail'}"
        f" — AD {ad or '—'} houses {sorted(planet_sigs.get(ad, []))}; "
        f"PD {pd or '—'} houses {sorted(planet_sigs.get(pd, []))}.",
        f"Sookshma gate ({sk or '—'}): {'pass' if in_sk else 'fail'}"
        f" — houses {sorted(planet_sigs.get(sk, []))}.",
    ]
    if scope == "hour":
        gate_lines.append(
            f"Prana gate ({pr or '—'}): {'pass' if in_pr else 'fail'}"
            f" — houses {sorted(planet_sigs.get(pr, []))}."
            + (" Soft fallback used (Prana empty after Sookshma)." if prana_fallback and in_eligible and not in_pr else "")
        )
    gate_lines.append(
        f"Dasha-eligible for {scope}: {'yes' if in_eligible else 'no'} → {sorted(eligible)}."
    )

    steps = [
        {
            "step": 1,
            "title": "Dasha permission",
            "passed": in_eligible,
            "detail": " ".join(gate_lines),
            "dasha_hits": dasha_hits,
        },
        {
            "step": 2,
            "title": "Ruling-planet trigger",
            "passed": bool(activating_rps),
            "detail": (
                f"Current {scope} RPs that signify H{house}: "
                + (
                    ", ".join(
                        f"{row['planet']} ({', '.join(row['roles']) or 'RP'})"
                        for row in rp_roles
                    )
                    if rp_roles
                    else "none"
                )
                + "."
            ),
            "activating_rps": rp_roles,
            "ruling_planets_used": dict(role_map),
        },
        {
            "step": 3,
            "title": "Strength tier",
            "passed": tier == "primary",
            "detail": tier_reason,
            "tier": tier,
            "anchors": sorted(anchor_set),
            "anchored_by": anchored_by,
        },
        {
            "step": 4,
            "title": "Outcome tone",
            "passed": True,
            "detail": tone_info["reason"],
            "tone": tone_info["tone"],
            "linked_houses": tone_info["linked_houses"],
            "dusthana_houses": tone_info["dusthana_houses"],
            "fulfillment_houses": tone_info["fulfillment_houses"],
            "linked_by_planet": tone_info["linked_by_planet"],
        },
    ]

    summary_bits = [
        f"H{house} is {tier} for {scope}",
        "because it passed the dasha gate" if in_eligible else "but failed the dasha gate",
        f"and is triggered by {', '.join(activating_rps) or 'no RP'}",
        f"with {tone_info['tone']} tone",
    ]
    return {
        "summary": " ".join(summary_bits) + ".",
        "steps": steps,
    }


def _polarity(value: str) -> Polarity:
    try:
        return Polarity(str(value or "neutral").lower())
    except ValueError:
        return Polarity.NEUTRAL


def _combine_tones(tones: Sequence[str]) -> str:
    values = {_polarity(t) for t in tones if t}
    if not values:
        return Polarity.NEUTRAL.value
    if Polarity.CHALLENGING in values and Polarity.SUPPORTIVE in values:
        return Polarity.MIXED.value
    if Polarity.MIXED in values:
        return Polarity.MIXED.value
    if Polarity.CHALLENGING in values:
        return Polarity.CHALLENGING.value
    if Polarity.SUPPORTIVE in values:
        return Polarity.SUPPORTIVE.value
    return Polarity.NEUTRAL.value


def _tier_houses(
    *,
    candidate_houses: Mapping[int, Sequence[str]],
    eligible: Set[int],
    primary_anchors: Sequence[str],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Split into primary (will give results) vs secondary.

    Primary: house signified by ≥2 RPs, or by an anchor RP (Moon star lord for day,
    Asc/Moon star lord for hour). Day-lord-only stays secondary.
    """
    primary: List[Dict[str, Any]] = []
    secondary: List[Dict[str, Any]] = []
    anchors = {str(p) for p in primary_anchors if p}

    for house in sorted(set(candidate_houses) & eligible):
        unique = list(dict.fromkeys(candidate_houses.get(house) or []))
        anchored = bool(anchors & set(unique))
        is_primary = len(unique) >= 2 or anchored
        row = {
            "house": house,
            "tier": "primary" if is_primary else "secondary",
            "activating_rps": unique,
        }
        if is_primary:
            primary.append(row)
        else:
            secondary.append(row)
    return primary, secondary


def _enrich_house_rows(
    rows: List[Dict[str, Any]],
    *,
    planet_sigs: Mapping[str, Sequence[int]],
    role_map: Mapping[str, str],
    anchors: Sequence[str],
    md: str,
    ad: str,
    pd: str,
    sk: str,
    pr: str,
    base_eligible: Set[int],
    sk_houses: Set[int],
    pr_houses: Set[int],
    eligible: Set[int],
    scope: str,
    prana_fallback: bool,
) -> List[Dict[str, Any]]:
    for row in rows:
        house = int(row["house"])
        activating = list(row.get("activating_rps") or [])
        tone_info = _tone_evidence(house, activating, planet_sigs)
        row["tone"] = tone_info["tone"]
        sig = HOUSE_SIGNIFICATIONS.get(house)
        row["label"] = sig.label if sig else f"House {house}"
        row["significations"] = list(sig.significations) if sig else []
        row["how"] = _build_house_calculation(
            house=house,
            tier=str(row.get("tier") or "secondary"),
            activating_rps=activating,
            role_map=role_map,
            anchors=anchors,
            planet_sigs=planet_sigs,
            md=md,
            ad=ad,
            pd=pd,
            sk=sk,
            pr=pr,
            base_eligible=base_eligible,
            sk_houses=sk_houses,
            pr_houses=pr_houses,
            eligible=eligible,
            scope=scope,
            prana_fallback=prana_fallback,
        )
    return rows


def _day_ruling_planets(rp: Mapping[str, Any]) -> Dict[str, str]:
    moon = rp.get("moon") or {}
    return {
        "day_lord": str(rp.get("day_lord") or ""),
        "moon_star_lord": str(moon.get("star_lord") or ""),
        "moon_sign_lord": str(moon.get("sign_lord") or ""),  # corroborator only
    }


def _hour_ruling_planets(rp: Mapping[str, Any]) -> Dict[str, str]:
    asc = rp.get("ascendant") or {}
    moon = rp.get("moon") or {}
    return {
        "day_lord": str(rp.get("day_lord") or ""),
        "asc_star_lord": str(asc.get("star_lord") or ""),
        "asc_sub_lord": str(asc.get("sub_lord") or ""),
        "moon_star_lord": str(moon.get("star_lord") or ""),
        "moon_sub_lord": str(moon.get("sub_lord") or ""),
    }


def _active_rp_planets(role_map: Mapping[str, str], keys: Sequence[str]) -> List[str]:
    planets: List[str] = []
    for key in keys:
        name = str(role_map.get(key) or "").strip()
        if name and name not in planets:
            planets.append(name)
    return planets


def _theme_from_houses(
    *,
    scope: str,
    subject: str,
    theme_key: str,
    label: str,
    summary: str,
    possibilities: Sequence[str],
    domain: str,
    native_houses: Sequence[int],
    tone_by_native: Mapping[int, str],
    window: Mapping[str, Any],
) -> Dict[str, Any]:
    """Build one theme for a subject. Relatives use relative_house for LLM/cache identity."""
    house_roles = []
    tones = []
    # Map native → relative; if two natives collapse to one relative, keep stronger pressure tone.
    relative_tone: Dict[int, str] = {}
    relative_native: Dict[int, int] = {}
    tone_rank = {
        Polarity.CHALLENGING.value: 3,
        Polarity.MIXED.value: 2,
        Polarity.SUPPORTIVE.value: 1,
        Polarity.NEUTRAL.value: 0,
    }
    for native in sorted(int(h) for h in native_houses):
        tone = str(tone_by_native.get(native) or Polarity.NEUTRAL.value)
        relative = native if subject == "self" else relative_house_for_native(subject, native)
        prev = relative_tone.get(relative)
        if prev is None or tone_rank.get(tone, 0) >= tone_rank.get(prev, 0):
            relative_tone[relative] = tone
            relative_native[relative] = native

    for relative in sorted(relative_tone):
        tone = relative_tone[relative]
        tones.append(tone)
        native = relative_native[relative]
        house_roles.append({
            "native_house": native,
            "relative_house": relative,
            "role": "focus",
            "outcome_tone": tone,
            "activation_state": "kp_fructifying",
        })

    return {
        "manifestation_id": f"kp-{scope}-{subject}-{theme_key}",
        "signature_key": f"kp:{scope}:{subject}:{theme_key}",
        "subject": subject,
        "domain": domain,
        "label": label,
        "summary": summary,
        "possibilities": list(possibilities),
        "outcome_tone": _combine_tones(tones),
        "synthesis_strength": "moderate",
        "house_roles": house_roles,
        "window": dict(window),
        "source": "kp_fructification",
    }


def _build_deterministic_manifestations(
    *,
    scope: str,
    primary_houses: Sequence[Mapping[str, Any]],
    as_of: datetime,
    dasha: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    """One combined theme per subject (self/spouse/mother/father) → shared cache or LLM.

    Same fingerprint as Combined Life Themes:
      subject + activated houses (native for self, relative for others) + tone_by_house
    So KP and Chart activation screens populate / reuse the same wording cache.
    """
    tone_by_native = {
        int(row["house"]): str(row.get("tone") or Polarity.NEUTRAL.value)
        for row in primary_houses
    }
    activated = set(tone_by_native)
    if not activated:
        return []

    window = {
        "start_date": as_of.strftime("%Y-%m-%d"),
        "end_date": as_of.strftime("%Y-%m-%d"),
        "scope": scope,
        "mahadasha": _planet(dasha.get("mahadasha")),
        "antardasha": _planet(dasha.get("antardasha")),
        "pratyantardasha": _planet(dasha.get("pratyantardasha")),
        "sookshma": _planet(dasha.get("sookshma")),
        "prana": _planet(dasha.get("prana")),
    }

    activated_key = tuple(sorted(activated))
    house_list = ", ".join(f"H{h}" for h in activated_key)
    seed_possibilities: List[str] = []
    for house in activated_key:
        sig = HOUSE_SIGNIFICATIONS.get(house)
        if sig and sig.manifestations:
            seed_possibilities.extend(list(sig.manifestations)[:2])
    seed = list(dict.fromkeys(seed_possibilities))[:8]
    theme_key = f"combined-{'-'.join(str(h) for h in activated_key)}"

    items: List[Dict[str, Any]] = []
    for subject in KP_MANIFESTATION_SUBJECTS:
        if subject == "self":
            label = "Combined activated life themes"
            summary = (
                f"Houses {house_list} are co-activated and can combine into practical life themes."
            )
        else:
            subject_label = SUBJECTS[subject].label
            label = "Combined activated life themes"
            summary = (
                f"Native houses {house_list} read for {subject_label} via relative-house "
                "significations (shared cache with What is activated now)."
            )
        items.append(_theme_from_houses(
            scope=scope,
            subject=subject,
            theme_key=theme_key,
            label=label,
            summary=summary,
            possibilities=seed,
            domain="other",
            native_houses=activated_key,
            tone_by_native=tone_by_native,
            window=window,
        ))
    return items


def _parse_as_of(
    as_of_date: Optional[str],
    as_of_time: Optional[str],
) -> datetime:
    now = datetime.now()
    date_str = (as_of_date or now.strftime("%Y-%m-%d")).strip()[:10]
    time_str = (as_of_time or now.strftime("%H:%M")).strip()
    if len(time_str) == 5:
        time_str = f"{time_str}:00"
    elif len(time_str) >= 8:
        time_str = time_str[:8]
    return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")


def _birth_payload_for_dasha(
    birth_date: str,
    birth_time: str,
    latitude: float,
    longitude: float,
    timezone: Optional[str],
) -> Dict[str, Any]:
    tz_offset = parse_timezone_offset(timezone or "", latitude, longitude)
    time_str = birth_time.strip()
    if len(time_str) == 5:
        time_str = f"{time_str}:00"
    return {
        "date": birth_date.strip()[:10],
        "time": time_str[:8],
        "latitude": latitude,
        "longitude": longitude,
        "timezone": tz_offset,
    }


def analyze_window(
    *,
    planet_sigs: Mapping[str, Sequence[int]],
    dasha: Mapping[str, Any],
    ruling_planets: Mapping[str, Any],
    scope: str,
    as_of: datetime,
) -> Dict[str, Any]:
    md = _planet(dasha.get("mahadasha"))
    ad = _planet(dasha.get("antardasha"))
    pd = _planet(dasha.get("pratyantardasha"))
    sk = _planet(dasha.get("sookshma"))
    pr = _planet(dasha.get("prana"))

    ad_houses = set(_houses_for_planets([ad], planet_sigs))
    pd_houses = set(_houses_for_planets([pd], planet_sigs))
    base_eligible = ad_houses | pd_houses

    sk_houses = set(_houses_for_planets([sk], planet_sigs))
    pr_houses = set(_houses_for_planets([pr], planet_sigs))

    today_eligible = base_eligible & sk_houses
    hour_eligible = today_eligible & pr_houses
    prana_fallback = False
    if scope == "hour" and not hour_eligible and today_eligible:
        hour_eligible = set(today_eligible)
        prana_fallback = True

    eligible = today_eligible if scope == "today" else hour_eligible

    if scope == "today":
        role_map = _day_ruling_planets(ruling_planets)
        rp_keys = DAY_RP_KEYS
        anchors = [role_map.get("moon_star_lord") or ""]
    else:
        role_map = _hour_ruling_planets(ruling_planets)
        rp_keys = HOUR_RP_KEYS
        anchors = [role_map.get("asc_star_lord") or "", role_map.get("moon_star_lord") or ""]

    rp_planets = _active_rp_planets(role_map, rp_keys)
    rp_houses = _houses_for_planets(rp_planets, planet_sigs)
    anchor_list = [a for a in anchors if a]

    primary, secondary = _tier_houses(
        candidate_houses=rp_houses,
        eligible=eligible,
        primary_anchors=anchor_list,
    )
    enrich_kwargs = dict(
        planet_sigs=planet_sigs,
        role_map=role_map,
        anchors=anchor_list,
        md=md,
        ad=ad,
        pd=pd,
        sk=sk,
        pr=pr,
        base_eligible=base_eligible,
        sk_houses=sk_houses,
        pr_houses=pr_houses,
        eligible=eligible,
        scope=scope,
        prana_fallback=prana_fallback if scope == "hour" else False,
    )
    primary = _enrich_house_rows(primary, **enrich_kwargs)
    secondary = _enrich_house_rows(secondary, **enrich_kwargs)

    calculation = {
        "title": f"How {scope} houses are identified",
        "formula": (
            "Base(AD∪PD) ∩ Sookshma ∩ RulingPlanets(day)"
            if scope == "today"
            else "Base(AD∪PD) ∩ Sookshma ∩ Prana ∩ RulingPlanets(hour)"
        ),
        "steps": [
            {
                "step": 1,
                "title": "Natal KP planet significators",
                "detail": "Each planet’s natal houses come from KP 4-level significators (P-Sig).",
                "planet_significators": {
                    planet: list(houses)
                    for planet, houses in sorted(planet_sigs.items())
                },
            },
            {
                "step": 2,
                "title": "Current Vimshottari stack",
                "detail": (
                    f"MD {md or '—'}, AD {ad or '—'}, PD {pd or '—'}, "
                    f"Sookshma {sk or '—'}, Prana {pr or '—'}."
                ),
                "dasha": {
                    "mahadasha": md,
                    "antardasha": ad,
                    "pratyantardasha": pd,
                    "sookshma": sk,
                    "prana": pr,
                },
                "houses_by_level": {
                    "mahadasha": sorted(planet_sigs.get(md, [])),
                    "antardasha": sorted(ad_houses),
                    "pratyantardasha": sorted(pd_houses),
                    "sookshma": sorted(sk_houses),
                    "prana": sorted(pr_houses),
                },
            },
            {
                "step": 3,
                "title": "Dasha eligibility gate",
                "detail": (
                    f"Base houses (AD∪PD, MD alone ignored) = {sorted(base_eligible)}. "
                    f"After Sookshma = {sorted(today_eligible)}."
                    + (
                        f" After Prana = {sorted(today_eligible & pr_houses)}"
                        + (
                            " (fallback to Sookshma set because Prana intersection was empty)."
                            if prana_fallback
                            else "."
                        )
                        if scope == "hour"
                        else ""
                    )
                ),
                "eligible_houses": sorted(eligible),
                "prana_fallback": prana_fallback if scope == "hour" else False,
            },
            {
                "step": 4,
                "title": f"Ruling planets for {scope}",
                "detail": (
                    "Day uses Day Lord + Moon Star Lord. "
                    if scope == "today"
                    else "Hour uses Day Lord + Asc Star/Sub + Moon Star/Sub. "
                )
                + f"Active RP planets: {', '.join(rp_planets) or 'none'}.",
                "ruling_planets_used": dict(role_map),
                "rp_planets": rp_planets,
                "houses_from_rps": {
                    str(house): list(planets)
                    for house, planets in sorted(rp_houses.items())
                },
                "anchors": anchor_list,
            },
            {
                "step": 5,
                "title": "Intersection → fructifying houses",
                "detail": (
                    f"Eligible ∩ RP houses, then tiered. "
                    f"Primary: {[r['house'] for r in primary]}. "
                    f"Secondary: {[r['house'] for r in secondary]}."
                ),
                "primary_houses": [r["house"] for r in primary],
                "secondary_houses": [r["house"] for r in secondary],
            },
        ],
    }

    return {
        "scope": scope,
        "ruling_planets_used": role_map,
        "rp_planets": rp_planets,
        "dasha_gate": {
            "base_planets": {"antardasha": ad, "pratyantardasha": pd, "mahadasha": md},
            "base_houses": sorted(base_eligible),
            "sookshma_planet": sk,
            "sookshma_houses": sorted(sk_houses),
            "prana_planet": pr,
            "prana_houses": sorted(pr_houses),
            "eligible_houses": sorted(eligible),
            "prana_fallback": prana_fallback if scope == "hour" else False,
        },
        "calculation": calculation,
        "houses_giving_results": primary,
        "houses_secondary": secondary,
        "manifestations_deterministic": _build_deterministic_manifestations(
            scope=scope,
            primary_houses=primary,
            as_of=as_of,
            dasha=dasha,
        ),
    }


def _merge_hour_primaries_into_today(
    today: Dict[str, Any],
    hour: Dict[str, Any],
    *,
    as_of: datetime,
    dasha: Mapping[str, Any],
) -> Dict[str, Any]:
    """Ensure Today never looks empty when This hour has fructifying houses.

    Day RPs are only Day Lord + Moon Star Lord; hour adds Asc/Moon star+sub, so hour can
    confirm houses the day gate alone misses. Those houses still belong to "today".
    """
    today_primary = {
        int(row["house"]): dict(row)
        for row in (today.get("houses_giving_results") or [])
        if row.get("house") is not None
    }
    today_secondary = {
        int(row["house"]): dict(row)
        for row in (today.get("houses_secondary") or [])
        if row.get("house") is not None
    }
    absorbed: List[int] = []

    for row in hour.get("houses_giving_results") or []:
        house = int(row["house"])
        if house in today_primary:
            continue
        if house in today_secondary:
            promoted = dict(today_secondary.pop(house))
            promoted["tier"] = "primary"
            promoted["included_from_hour"] = True
            how = dict(promoted.get("how") or {})
            how["summary"] = (
                (how.get("summary") or f"H{house} is primary for today")
                + " Included because it is giving results this hour."
            )
            promoted["how"] = how
            today_primary[house] = promoted
        else:
            cloned = dict(row)
            cloned["tier"] = "primary"
            cloned["included_from_hour"] = True
            how = dict(cloned.get("how") or {})
            how["summary"] = (
                (how.get("summary") or f"H{house} is primary for today")
                + " Day RPs alone did not confirm it; included because this hour’s "
                "ruling planets confirm it within today’s dasha gate."
            )
            cloned["how"] = how
            # Keep hour activating RPs for transparency; scope label stays useful in UI.
            today_primary[house] = cloned
        absorbed.append(house)

    if not absorbed:
        return today

    primary_rows = [today_primary[h] for h in sorted(today_primary)]
    secondary_rows = [today_secondary[h] for h in sorted(today_secondary)]
    out = dict(today)
    out["houses_giving_results"] = primary_rows
    out["houses_secondary"] = secondary_rows
    out["hour_houses_absorbed"] = absorbed
    calc = dict(out.get("calculation") or {})
    steps = list(calc.get("steps") or [])
    steps.append({
        "step": len(steps) + 1,
        "title": "Hour houses counted for today",
        "detail": (
            "This hour confirmed house(s) "
            + ", ".join(f"H{h}" for h in absorbed)
            + " via Asc/Moon star or sub lords. They are included in Today because "
            "the hour falls within the day."
        ),
        "houses": absorbed,
    })
    calc["steps"] = steps
    out["calculation"] = calc
    out["manifestations_deterministic"] = _build_deterministic_manifestations(
        scope="today",
        primary_houses=primary_rows,
        as_of=as_of,
        dasha=dasha,
    )
    return out


async def compute_fructification(
    *,
    birth_date: str,
    birth_time: str,
    latitude: float,
    longitude: float,
    timezone: Optional[str] = "",
    as_of_date: Optional[str] = None,
    as_of_time: Optional[str] = None,
    language: str = "en",
    synthesize: bool = True,
) -> Dict[str, Any]:
    as_of = _parse_as_of(as_of_date, as_of_time)

    natal = KPChartService.calculate_kp_chart(
        birth_date, birth_time, latitude, longitude, timezone
    )
    planet_sigs = _normalize_planet_sigs(natal.get("planet_significators") or {})

    birth_for_dasha = _birth_payload_for_dasha(
        birth_date, birth_time, latitude, longitude, timezone
    )
    dasha = DashaCalculator().calculate_current_dashas(birth_for_dasha, as_of)

    ruling_planets = KPCalculations.get_ruling_planets(
        as_of.strftime("%Y-%m-%d"),
        as_of.strftime("%H:%M:%S"),
        latitude,
        longitude,
        timezone or "",
    )

    today = analyze_window(
        planet_sigs=planet_sigs,
        dasha=dasha,
        ruling_planets=ruling_planets,
        scope="today",
        as_of=as_of,
    )
    hour = analyze_window(
        planet_sigs=planet_sigs,
        dasha=dasha,
        ruling_planets=ruling_planets,
        scope="hour",
        as_of=as_of,
    )
    today = _merge_hour_primaries_into_today(today, hour, as_of=as_of, dasha=dasha)

    async def _with_synthesis(block: Dict[str, Any]) -> Dict[str, Any]:
        deterministic = list(block.pop("manifestations_deterministic") or [])
        out = dict(block)
        if not deterministic:
            out["manifestations"] = []
            out["manifestation_synthesis"] = {
                "version": None,
                "cached_or_generated": "empty",
                "error": False,
            }
            return out
        if not synthesize:
            out["manifestations"] = deterministic
            out["manifestation_synthesis"] = {
                "version": None,
                "cached_or_generated": "skipped",
                "error": False,
            }
            return out
        try:
            synthesis = await synthesize_manifestations(
                deterministic=deterministic,
                locale=language or "en",
            )
            out["manifestations"] = synthesis.get("manifestations") or deterministic
            errored = bool(synthesis.get("synthesis_error"))
            out["manifestation_synthesis"] = {
                "version": synthesis.get("synthesis_version"),
                "cached_or_generated": (
                    "error"
                    if errored and not synthesis.get("synthesis_version")
                    else "cache_or_llm"
                ),
                "error": errored,
                "partial": bool(synthesis.get("synthesis_partial")),
                "theme_count": len(out["manifestations"]),
            }
        except Exception:
            # Never blank Results when LLM/cache fails — keep deterministic themes.
            logger.exception("KP manifestation synthesis failed; returning deterministic themes")
            out["manifestations"] = deterministic
            out["manifestation_synthesis"] = {
                "version": None,
                "cached_or_generated": "deterministic_fallback",
                "error": True,
                "theme_count": len(deterministic),
            }
        return out

    # Warm cache once for overlapping today/hour fingerprints, then attach each window.
    today_det = list(today.get("manifestations_deterministic") or [])
    hour_det = list(hour.get("manifestations_deterministic") or [])
    if synthesize and (today_det or hour_det):
        try:
            await synthesize_manifestations(
                deterministic=today_det + hour_det,
                locale=language or "en",
            )
        except Exception:
            logger.exception("KP shared manifestation warm-up failed; continuing per window")

    today_out, hour_out = await asyncio.gather(
        _with_synthesis(today),
        _with_synthesis(hour),
    )

    dasha_public = {
        "mahadasha": dasha.get("mahadasha"),
        "antardasha": dasha.get("antardasha"),
        "pratyantardasha": dasha.get("pratyantardasha"),
        "sookshma": dasha.get("sookshma"),
        "prana": dasha.get("prana"),
    }

    return {
        "as_of": as_of.isoformat(sep="T"),
        "dasha": dasha_public,
        "ruling_planets": ruling_planets,
        "natal_planet_significators": planet_sigs,
        "today": today_out,
        "hour": hour_out,
    }
