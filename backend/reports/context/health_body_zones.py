"""
Deterministic Kalapurusha body-zone + event-pattern evidence for Health reports.

Fuses house meaning × sign on house × lord condition × occupants/aspects × nakshatra
into ranked zones and concrete wellness-event patterns the LLM must narrate.
Never diagnoses disease — only chart-grounded susceptibility themes.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# Natural zodiac (Kalapurusha by sign)
SIGN_BODY: Dict[int, Dict[str, Any]] = {
    0: {"zones": ["head", "brain", "face", "eyes"], "tone": "heat / inflammation in the head"},
    1: {"zones": ["neck", "throat", "thyroid", "sinuses"], "tone": "throat-neck congestion or strain"},
    2: {"zones": ["shoulders", "arms", "hands", "lungs"], "tone": "upper limb / respiratory channels"},
    3: {"zones": ["chest", "stomach", "breasts", "fluids"], "tone": "chest-stomach fluid balance"},
    4: {"zones": ["heart", "spine", "upper back", "blood pressure tone"], "tone": "heart-spine heat and vascular tone"},
    5: {"zones": ["intestines", "digestion", "abdomen"], "tone": "digestive / gut sensitivity"},
    6: {"zones": ["kidneys", "lower back", "skin", "lumbar"], "tone": "kidney-lumbar / skin balance"},
    7: {"zones": ["reproductive organs", "pelvis", "excretory"], "tone": "pelvic / excretory sensitivity"},
    8: {"zones": ["hips", "thighs", "liver", "sciatic nerve"], "tone": "hip-thigh-liver axis"},
    9: {"zones": ["knees", "bones", "joints", "teeth"], "tone": "knees / skeletal stiffness"},
    10: {"zones": ["calves", "ankles", "circulation", "nerves"], "tone": "calf-ankle circulation / nerve tone"},
    11: {"zones": ["feet", "toes", "lymph", "sleep"], "tone": "feet / lymph / recovery sleep"},
}

# House Kalapurusha (by house number, independent of sign)
HOUSE_BODY: Dict[int, Dict[str, Any]] = {
    1: {"zones": ["head", "brain", "vitality", "overall body"], "role": "constitution / vitality"},
    2: {"zones": ["face", "mouth", "teeth", "throat", "sinuses"], "role": "intake / face-throat"},
    3: {"zones": ["shoulders", "arms", "hands", "lungs"], "role": "arms / breath effort"},
    4: {"zones": ["chest", "heart", "lungs", "digestion comfort"], "role": "chest / emotional gut"},
    5: {"zones": ["stomach", "spine", "heart region"], "role": "stomach / spine"},
    6: {"zones": ["abdomen", "immunity", "acute illness sites"], "role": "disease / immunity / accidents"},
    7: {"zones": ["kidneys", "lower back", "partner-stress body"], "role": "balance / lumbar"},
    8: {"zones": ["chronic organs", "nerves", "surgery / crisis sites"], "role": "chronic / surgery / sudden events"},
    9: {"zones": ["hips", "thighs", "liver", "long journeys risk"], "role": "thighs / fortune / travel body"},
    10: {"zones": ["knees", "bones", "joints", "career strain body"], "role": "knees / structure"},
    11: {"zones": ["calves", "ankles", "circulation"], "role": "circulation / gains body"},
    12: {"zones": ["feet", "sleep", "hospitalization / recovery beds"], "role": "feet / rest / hospitalization"},
}

PLANET_KARAKA: Dict[str, Dict[str, Any]] = {
    "Sun": {"zones": ["heart", "spine", "eyes", "vitality", "blood pressure tone"], "event": "vital heat / authority stress"},
    "Moon": {"zones": ["mind", "fluids", "stomach", "chest", "sleep"], "event": "emotional / fluid imbalance"},
    "Mars": {"zones": ["blood", "muscles", "inflammation", "accidents", "surgery"], "event": "acute injury / surgery / inflammation"},
    "Mercury": {"zones": ["nerves", "skin", "speech", "lungs", "sinuses"], "event": "nervous / communication strain"},
    "Jupiter": {"zones": ["liver", "fat", "growth", "thighs", "immunity"], "event": "liver / growth / recovery capacity"},
    "Venus": {"zones": ["hormones", "reproductive", "kidneys", "throat comfort"], "event": "hormonal / comfort tissue"},
    "Saturn": {"zones": ["bones", "joints", "teeth", "chronic pain", "blood pressure tone"], "event": "chronic / structural / pressure"},
    "Rahu": {"zones": ["toxins", "sudden flare", "nerves", "unusual symptoms", "sinuses"], "event": "sudden / hard-to-trace flare"},
    "Ketu": {"zones": ["hidden ailments", "nerves", "detachment fatigue", "chronic voids"], "event": "hidden / depleting sensitivity"},
}

SIGN_LORDS = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun", 5: "Mercury",
    6: "Venus", 7: "Mars", 8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter",
}

MALEFICS = {"Mars", "Saturn", "Rahu", "Ketu"}
DUSTHANA = {6, 8, 12}


def _sign_index(value: Any) -> Optional[int]:
    try:
        s = int(value)
        if 0 <= s <= 11:
            return s
        if 1 <= s <= 12:
            return s - 1
    except (TypeError, ValueError):
        pass
    return None


def _planet_house(planets: Dict[str, Any], name: str) -> Optional[int]:
    data = planets.get(name)
    if not isinstance(data, dict):
        return None
    try:
        h = int(data.get("house"))
        return h if 1 <= h <= 12 else None
    except (TypeError, ValueError):
        return None


def _planet_sign(planets: Dict[str, Any], name: str) -> Optional[int]:
    data = planets.get(name)
    if not isinstance(data, dict):
        return None
    return _sign_index(data.get("sign"))


def _house_sign(houses: List[Any], house_num: int) -> Optional[int]:
    if house_num < 1 or house_num > len(houses):
        return None
    row = houses[house_num - 1]
    if not isinstance(row, dict):
        return None
    return _sign_index(row.get("sign"))


def _residents(planets: Dict[str, Any]) -> Dict[int, List[str]]:
    out: Dict[int, List[str]] = {}
    for name, data in planets.items():
        if not isinstance(data, dict):
            continue
        try:
            h = int(data.get("house"))
        except (TypeError, ValueError):
            continue
        if 1 <= h <= 12:
            out.setdefault(h, []).append(name)
    return out


def _lord_of_house(houses: List[Any], house_num: int) -> Optional[str]:
    sign = _house_sign(houses, house_num)
    if sign is None:
        return None
    return SIGN_LORDS.get(sign)


def _merge_zones(*lists: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for lst in lists:
        for z in lst or []:
            key = str(z).strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(str(z).strip())
    return out


def _score_house(
    house_num: int,
    *,
    residents: List[str],
    aspecting: List[str],
    lord: Optional[str],
    lord_house: Optional[int],
    lord_with_malefics: List[str],
) -> Tuple[int, List[str]]:
    score = 0
    reasons: List[str] = []
    if house_num in DUSTHANA:
        score += 4
        reasons.append(f"H{house_num} is a dusthana (disease/crisis/recovery house)")
    if house_num in (1, 2, 4):
        score += 1
    malefic_here = [p for p in residents if p in MALEFICS]
    if malefic_here:
        score += 3 * len(malefic_here)
        reasons.append(f"Malefics in H{house_num}: {', '.join(malefic_here)}")
    if aspecting:
        score += min(3, len(aspecting))
        reasons.append(f"Aspects on H{house_num}: {', '.join(aspecting)}")
    if lord and lord_house in DUSTHANA:
        score += 3
        reasons.append(f"H{house_num} lord {lord} sits in dusthana H{lord_house}")
    if lord_with_malefics:
        score += 4
        reasons.append(f"H{house_num} lord {lord} conjunct {', '.join(lord_with_malefics)}")
    if lord == "Mars" or "Mars" in malefic_here:
        score += 1
    return score, reasons


def _nakshatra_zone_hints(lords_nakshatra: Dict[str, Any]) -> List[Dict[str, Any]]:
    hints: List[Dict[str, Any]] = []
    for key in ("lagna_lord", "moon", "sixth_lord", "eighth_lord"):
        row = lords_nakshatra.get(key) or {}
        nak = row.get("nakshatra") or {}
        name = str(nak.get("nakshatra") or nak.get("name") or "").strip()
        if not name:
            continue
        lower = name.lower()
        zones: List[str] = []
        tone = ""
        if lower in {"swati", "ashwini", "shatabhisha", "punarvasu"}:
            zones = ["nerves", "breath", "circulation", "anxiety tone"]
            tone = "Vayu / airy nervous-respiratory flavour"
        elif lower in {"magha", "uttara phalguni", "purva phalguni", "krittika"}:
            zones = ["spine", "digestion heat", "vital fire"]
            tone = "solar / pitta heat flavour"
        elif lower in {"rohini", "hasta", "revati"}:
            zones = ["fluids", "digestion comfort", "sleep"]
            tone = "nourishing / fluid tone"
        elif lower in {"mula", "jyeshtha", "ardra"}:
            zones = ["nerves", "hidden crisis sites", "detox pathways"]
            tone = "intense / crisis-sensitivity flavour"
        if zones:
            hints.append({
                "source": key,
                "planet": row.get("planet"),
                "nakshatra": name,
                "zones": zones,
                "tone": tone,
            })
    return hints


def build_priority_body_zones(
    chart: Dict[str, Any],
    *,
    lords_nakshatra: Optional[Dict[str, Any]] = None,
    current_dashas: Optional[Dict[str, Any]] = None,
    divisional_charts: Optional[Dict[str, Any]] = None,
    planet_conditions: Optional[Dict[str, Any]] = None,
    requested_category: str = "health",
) -> Dict[str, Any]:
    planets = chart.get("planets") or {}
    houses = chart.get("houses") or []
    if len(houses) < 12 or not planets:
        return {"priority_zones": [], "event_patterns": [], "house_map": [], "disclaimer": (
            "Astrological body-zone map only — not a medical diagnosis."
        )}

    residents_map = _residents(planets)
    drishti = chart.get("graha_drishti_by_house") or {}
    house_map: List[Dict[str, Any]] = []
    scored: List[Dict[str, Any]] = []

    for h in range(1, 13):
        sign = _house_sign(houses, h)
        sign_name = SIGN_NAMES[sign] if sign is not None else "--"
        lord = _lord_of_house(houses, h)
        lord_house = _planet_house(planets, lord) if lord else None
        residents = residents_map.get(h) or []
        aspect_rows = drishti.get(str(h)) or drishti.get(h) or []
        aspecting = [
            str(item.get("planet"))
            for item in aspect_rows
            if isinstance(item, dict) and item.get("planet")
        ]
        lord_company = []
        if lord and lord_house:
            lord_company = [p for p in (residents_map.get(lord_house) or []) if p != lord]
        lord_malefics = [p for p in lord_company if p in MALEFICS]

        score, reasons = _score_house(
            h,
            residents=residents,
            aspecting=aspecting,
            lord=lord,
            lord_house=lord_house,
            lord_with_malefics=lord_malefics,
        )

        house_zones = list((HOUSE_BODY.get(h) or {}).get("zones") or [])
        sign_zones = list((SIGN_BODY.get(sign) or {}).get("zones") or []) if sign is not None else []
        # Fusion: house meaning + sign flavour on that house
        fused = _merge_zones(house_zones[:3], sign_zones[:3])
        if h == 6 and sign is not None:
            # Disease house × rashi is especially important for vulnerability sites
            fused = _merge_zones(sign_zones, house_zones[:2])
            reasons.append(
                f"6th-house rashi {sign_name} flavours disease sites toward {', '.join(sign_zones[:3])}"
            )
            score += 2

        row = {
            "house": h,
            "sign": sign_name,
            "sign_index": sign,
            "lord": lord,
            "lord_house": lord_house,
            "residents": residents,
            "aspecting_planets": aspecting,
            "house_zones": house_zones,
            "sign_zones": sign_zones,
            "fused_zones": fused,
            "role": (HOUSE_BODY.get(h) or {}).get("role"),
            "sign_tone": (SIGN_BODY.get(sign) or {}).get("tone") if sign is not None else None,
            "score": score,
            "reasons": reasons,
        }
        house_map.append(row)
        if score > 0:
            scored.append(row)

    scored.sort(key=lambda r: (-int(r.get("score") or 0), int(r.get("house") or 99)))

    # Aggregate priority zone cards
    zone_weights: Dict[str, Dict[str, Any]] = {}
    for row in scored[:8]:
        for zone in row.get("fused_zones") or []:
            key = zone.lower()
            bucket = zone_weights.setdefault(key, {
                "zone": zone,
                "weight": 0,
                "standing_weight": 0,
                "sources": [],
                "why": [],
                "natal_layers": [],
                "activation_sources": [],
            })
            bucket["weight"] += int(row.get("score") or 0)
            bucket["standing_weight"] += int(row.get("score") or 0)
            if zone in (row.get("house_zones") or []):
                layer = f"house_anatomy:H{row['house']}"
                if layer not in bucket["natal_layers"]:
                    bucket["natal_layers"].append(layer)
            if zone in (row.get("sign_zones") or []):
                layer = f"sign_anatomy:{row.get('sign')}"
                if layer not in bucket["natal_layers"]:
                    bucket["natal_layers"].append(layer)
            src = f"H{row['house']} {row.get('sign')}"
            if src not in bucket["sources"]:
                bucket["sources"].append(src)
            for reason in (row.get("reasons") or [])[:2]:
                if reason not in bucket["why"]:
                    bucket["why"].append(reason)

    # Planet karaka boosts from afflicted placements
    for planet, meta in PLANET_KARAKA.items():
        h = _planet_house(planets, planet)
        if h is None:
            continue
        company = [p for p in (residents_map.get(h) or []) if p != planet]
        pressure = planet in MALEFICS or h in DUSTHANA or any(p in MALEFICS for p in company)
        if not pressure:
            continue
        for zone in meta.get("zones") or []:
            key = zone.lower()
            bucket = zone_weights.setdefault(key, {
                "zone": zone, "weight": 0, "standing_weight": 0,
                "sources": [], "why": [], "natal_layers": [], "activation_sources": [],
            })
            bucket["weight"] += 3
            bucket["standing_weight"] += 3
            layer = f"planet_karaka:{planet}"
            if layer not in bucket["natal_layers"]:
                bucket["natal_layers"].append(layer)
            label = f"{planet} in H{h}"
            if label not in bucket["sources"]:
                bucket["sources"].append(label)
            why = f"{planet} karaka for {zone}; placed in H{h}" + (
                f" with {', '.join([p for p in company if p in MALEFICS])}" if any(p in MALEFICS for p in company) else ""
            )
            if why not in bucket["why"]:
                bucket["why"].append(why)

    for hint in _nakshatra_zone_hints(lords_nakshatra or {}):
        for zone in hint.get("zones") or []:
            key = zone.lower()
            bucket = zone_weights.setdefault(key, {
                "zone": zone, "weight": 0, "standing_weight": 0,
                "sources": [], "why": [], "natal_layers": [], "activation_sources": [],
            })
            bucket["weight"] += 2
            bucket["standing_weight"] += 2
            layer = f"nakshatra:{hint.get('source')}"
            if layer not in bucket["natal_layers"]:
                bucket["natal_layers"].append(layer)
            src = f"{hint.get('nakshatra')} ({hint.get('source')})"
            if src not in bucket["sources"]:
                bucket["sources"].append(src)
            why = hint.get("tone") or ""
            if why and why not in bucket["why"]:
                bucket["why"].append(why)

    # Dasha activation
    dashas = current_dashas or {}
    for label in ("mahadasha", "antardasha", "pratyantardasha"):
        block = dashas.get(label) or {}
        planet = block.get("planet") if isinstance(block, dict) else None
        if not planet:
            continue
        h = _planet_house(planets, str(planet))
        sign = _planet_sign(planets, str(planet))
        karaka_zones = list((PLANET_KARAKA.get(str(planet)) or {}).get("zones") or [])
        house_zones = list((HOUSE_BODY.get(h) or {}).get("zones") or []) if h else []
        sign_zones = list((SIGN_BODY.get(sign) or {}).get("zones") or []) if sign is not None else []
        for zone in _merge_zones(karaka_zones[:3], house_zones[:2], sign_zones[:2]):
            key = zone.lower()
            bucket = zone_weights.setdefault(key, {
                "zone": zone, "weight": 0, "standing_weight": 0,
                "sources": [], "why": [], "natal_layers": [], "activation_sources": [],
            })
            bucket["weight"] += 2
            src = f"Current {label}: {planet}"
            if src not in bucket["sources"]:
                bucket["sources"].append(src)
            if src not in bucket["activation_sources"]:
                bucket["activation_sources"].append(src)

    event_patterns = _build_event_patterns(planets, houses, residents_map, house_map)

    # Boost zones named by event patterns so PDF + LLM prioritize lived-theme anatomy.
    for pattern in event_patterns:
        for zone in pattern.get("zones") or []:
            key = str(zone).strip().lower()
            if not key:
                continue
            bucket = zone_weights.setdefault(key, {
                "zone": zone, "weight": 0, "standing_weight": 0,
                "sources": [], "why": [], "natal_layers": [], "activation_sources": [],
            })
            bucket["weight"] += 5
            bucket["standing_weight"] += 5
            layer = f"event_pattern:{pattern.get('key') or 'health'}"
            if layer not in bucket["natal_layers"]:
                bucket["natal_layers"].append(layer)
            title = pattern.get("title") or pattern.get("key")
            if title and title not in bucket["sources"]:
                bucket["sources"].append(str(title))
            summary = pattern.get("summary")
            if summary and summary not in bucket["why"]:
                bucket["why"].append(str(summary)[:160])

    priority_zones = sorted(zone_weights.values(), key=lambda z: -int(z.get("weight") or 0))[:8]
    for item in priority_zones:
        item["why"] = (item.get("why") or [])[:4]
        item["sources"] = (item.get("sources") or [])[:5]
        item["guidance"] = (
            f"Astrological attention theme: {item['zone']}. "
            "Not a diagnosis — discuss symptoms with a qualified doctor."
        )

        # A dasha or transit can activate a natal susceptibility, but cannot
        # create one.  Named body-part claims therefore require at least two
        # independent natal calculation families.  This prevents a single
        # generic sign/planet association from becoming a scary medical claim.
        layer_families = {
            str(layer).split(":", 1)[0]
            for layer in (item.get("natal_layers") or [])
            if layer
        }
        standing_weight = int(item.get("standing_weight") or 0)
        item["confluence_count"] = len(layer_families)
        item["callout_allowed"] = len(layer_families) >= 2 and standing_weight >= 8
        item["confidence"] = (
            "high" if len(layer_families) >= 3 and standing_weight >= 14
            else "medium" if item["callout_allowed"]
            else "directional"
        )

    major_vulnerabilities = [
        {
            "zone": item.get("zone"),
            "confidence": item.get("confidence"),
            "confluence_count": item.get("confluence_count"),
            "standing_weight": item.get("standing_weight"),
            "natal_layers": list(item.get("natal_layers") or [])[:6],
            "activation_sources": list(item.get("activation_sources") or [])[:3],
            "sources": list(item.get("sources") or [])[:5],
            "why": list(item.get("why") or [])[:4],
        }
        for item in priority_zones
        if item.get("callout_allowed")
    ][:3]

    medical_profile = _build_medical_profile(
        chart=chart,
        house_map=house_map,
        major_vulnerabilities=major_vulnerabilities,
        event_patterns=event_patterns,
        divisional_charts=divisional_charts or {},
        planet_conditions=planet_conditions or {},
        current_dashas=current_dashas or {},
        requested_category=requested_category,
    )

    return {
        "disclaimer": (
            "These body zones and event patterns are Vedic chart susceptibilities only. "
            "They are not diagnoses of BP, sinus disease, injury, or any medical condition."
        ),
        "house_map": [
            {
                "house": r["house"],
                "sign": r["sign"],
                "lord": r["lord"],
                "lord_house": r["lord_house"],
                "fused_zones": r["fused_zones"],
                "score": r["score"],
                "reasons": r["reasons"][:3],
            }
            for r in scored[:8]
        ],
        "priority_zones": priority_zones,
        "major_vulnerabilities": major_vulnerabilities,
        "event_patterns": event_patterns,
        "top_zone_names": [z.get("zone") for z in major_vulnerabilities],
        "claim_policy": {
            "named_body_part_requires": "At least two independent natal calculation families and standing weight >= 8.",
            "timing_cannot_create_vulnerability": True,
            "diagnosis_allowed": False,
        },
        "medical_profile": medical_profile,
    }


def _chart_payload(chart: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(chart, dict):
        return {}
    nested = chart.get("divisional_chart")
    return nested if isinstance(nested, dict) else chart


def _division_planets(chart: Dict[str, Any]) -> Dict[str, Any]:
    payload = _chart_payload(chart)
    planets = payload.get("planets")
    return planets if isinstance(planets, dict) else {}


def _division_name(raw: str) -> str:
    value = str(raw or "").lower()
    for code in ("d30", "d8", "d6", "d3"):
        if value == code or value.startswith(code + "_"):
            return code.upper()
    return str(raw or "").upper()


def _condition_row(planet: str, raw: Dict[str, Any]) -> Dict[str, Any]:
    row = raw.get(planet) if isinstance(raw, dict) else {}
    row = row if isinstance(row, dict) else {}
    dignity = row.get("dignity_analysis") if isinstance(row.get("dignity_analysis"), dict) else row
    strength = row.get("strength_analysis") if isinstance(row.get("strength_analysis"), dict) else row
    combustion = row.get("combustion_status")
    if isinstance(combustion, dict):
        combustion = combustion.get("status") or ("combust" if combustion.get("is_combust") else "normal")
    return {
        "planet": planet,
        "dignity": dignity.get("dignity"),
        "functional_nature": dignity.get("functional_nature"),
        "strength_multiplier": dignity.get("strength_multiplier"),
        "shadbala_rupas": strength.get("shadbala_rupas") or strength.get("total_rupas"),
        "shadbala_grade": strength.get("shadbala_grade") or strength.get("grade"),
        "combustion": combustion,
        "retrograde": row.get("retrograde"),
    }


def _mechanisms_for_zone(zone: str, sources: List[str]) -> List[str]:
    text = " ".join([str(zone)] + [str(v) for v in sources]).lower()
    mechanisms: List[str] = []
    mapping = (
        ("acute / inflammatory", ("mars", "blood", "heat", "inflammation", "accident", "surgery")),
        ("chronic / degenerative", ("saturn", "bone", "joint", "chronic", "teeth")),
        ("toxic / unusual", ("rahu", "toxin", "unusual", "hard-to-trace")),
        ("hidden / depleting", ("ketu", "hidden", "fatigue", "void")),
        ("nervous / functional", ("mercury", "nerve", "speech", "respiratory")),
        ("fluid / hormonal", ("moon", "venus", "fluid", "hormone", "kidney", "reproductive")),
        ("metabolic / growth", ("jupiter", "liver", "fat", "growth", "immunity")),
    )
    for label, needles in mapping:
        if any(needle in text for needle in needles):
            mechanisms.append(label)
    return mechanisms[:3] or ["constitutional susceptibility"]


def _build_medical_profile(
    *,
    chart: Dict[str, Any],
    house_map: List[Dict[str, Any]],
    major_vulnerabilities: List[Dict[str, Any]],
    event_patterns: List[Dict[str, Any]],
    divisional_charts: Dict[str, Any],
    planet_conditions: Dict[str, Any],
    current_dashas: Dict[str, Any],
    requested_category: str,
) -> Dict[str, Any]:
    """Normalize medical-astrology evidence before any language generation.

    D1 establishes susceptibility. Vargas can confirm or weaken confidence but
    never create a vulnerability. Timing can activate only a D1-established
    theme. This contract deliberately contains no disease names.
    """
    planets = chart.get("planets") or {}
    houses_by_number = {int(row.get("house")): row for row in house_map if row.get("house")}
    ascendant = chart.get("ascendant")
    try:
        asc_sign = _sign_index(int(float(ascendant) / 30)) if ascendant is not None else None
    except (TypeError, ValueError):
        asc_sign = None
    # Some callers intentionally pass the compact chart shape without the
    # ascendant longitude.  House 1 still carries the calculated rising sign;
    # never silently turn a missing longitude into Aries.
    if asc_sign is None:
        asc_sign = _house_sign(chart.get("houses") or [], 1)
    lagna_lord = SIGN_LORDS.get(asc_sign) if asc_sign is not None else None
    constitution = {
        "ascendant_sign": SIGN_NAMES[asc_sign] if asc_sign is not None else None,
        "ascendant_lord": lagna_lord,
        "ascendant_lord_house": _planet_house(planets, lagna_lord) if lagna_lord else None,
        "sun_house": _planet_house(planets, "Sun"),
        "moon_house": _planet_house(planets, "Moon"),
        "core_houses": [
            {
                "house": h,
                "role": (HOUSE_BODY.get(h) or {}).get("role"),
                "sign": (houses_by_number.get(h) or {}).get("sign"),
                "lord": (houses_by_number.get(h) or {}).get("lord"),
                "lord_house": (houses_by_number.get(h) or {}).get("lord_house"),
                "residents": (houses_by_number.get(h) or {}).get("residents") or [],
                "aspecting_planets": (houses_by_number.get(h) or {}).get("aspecting_planets") or [],
                "pressure_score": (houses_by_number.get(h) or {}).get("score"),
            }
            for h in (1, 6, 8, 12)
        ],
    }

    condition_planets = {"Sun", "Moon", "Mars", "Saturn", "Rahu", "Ketu"}
    condition_planets.update(
        str((houses_by_number.get(h) or {}).get("lord") or "") for h in (1, 6, 8, 12)
    )
    conditions = [
        _condition_row(planet, planet_conditions)
        for planet in sorted(condition_planets)
        if planet and planet in planets
    ]

    divisions: Dict[str, Dict[str, Any]] = {}
    for raw_name, raw_chart in (divisional_charts or {}).items():
        code = _division_name(raw_name)
        if code not in {"D3", "D6", "D8", "D30"}:
            continue
        dplanets = _division_planets(raw_chart)
        divisions[code] = {
            "available": bool(dplanets),
            "planets": {
                planet: {
                    "house": _planet_house(dplanets, planet),
                    "sign": _planet_sign(dplanets, planet),
                }
                for planet in condition_planets
                if planet and planet in dplanets
            },
        }

    confirmations: List[Dict[str, Any]] = []
    enhanced_vulnerabilities: List[Dict[str, Any]] = []
    for vulnerability in major_vulnerabilities:
        sources = list(vulnerability.get("sources") or [])
        # The compact source labels intentionally omit some technical detail
        # (for example, the surgery label itself).  Recover the actual natal
        # actors from both those labels and their human-readable reasons so a
        # varga confirmation is not lost merely because the UI copy is short.
        source_evidence = sources + list(vulnerability.get("why") or [])
        source_planets = [
            p for p in PLANET_KARAKA
            if any(p.lower() in str(src).lower() for src in source_evidence)
        ]
        repeated: List[str] = []
        for code, division in divisions.items():
            for planet in source_planets:
                drow = (division.get("planets") or {}).get(planet) or {}
                if drow.get("house") in DUSTHANA:
                    repeated.append(f"{code}: {planet} repeats in health-sensitive House {drow.get('house')}")
        confidence = str(vulnerability.get("confidence") or "directional")
        if len(repeated) >= 2 and confidence == "medium":
            confidence = "high"
        enhanced = {
            **vulnerability,
            "confidence": confidence,
            "mechanisms": _mechanisms_for_zone(str(vulnerability.get("zone") or ""), sources),
            "divisional_repetition": repeated[:5],
        }
        enhanced_vulnerabilities.append(enhanced)
        if repeated:
            confirmations.append({"zone": vulnerability.get("zone"), "repetitions": repeated[:5]})

    benefics = {"Jupiter", "Venus", "Moon", "Mercury"}
    protection: List[str] = []
    for h in (1, 6, 8, 12):
        row = houses_by_number.get(h) or {}
        supporting = [p for p in (row.get("aspecting_planets") or []) if p in benefics]
        if supporting:
            protection.append(f"House {h} receives support from {', '.join(supporting)}")
    for row in conditions:
        if row.get("dignity") in {"exalted", "own_sign", "moolatrikona", "mooltrikona_sign"}:
            protection.append(f"{row.get('planet')} has strong dignity ({row.get('dignity')})")

    pattern_by_key = {str(row.get("key") or ""): row for row in event_patterns}
    activated_vulnerabilities = [
        {
            "zone": row.get("zone"),
            "confidence": row.get("confidence"),
            "activation_sources": list(row.get("activation_sources") or [])[:4],
        }
        for row in enhanced_vulnerabilities
        if row.get("activation_sources")
    ]
    judgments = {
        "constitutional": {
            "supported": bool(enhanced_vulnerabilities),
            "vulnerabilities": enhanced_vulnerabilities[:3],
        },
        "current": {
            "active": bool(activated_vulnerabilities),
            "activation_only": True,
            "activated_vulnerabilities": activated_vulnerabilities[:3],
            "rule": "Current timing may activate only a natal susceptibility listed above.",
        },
        "surgery": {
            "supported": "surgery_crisis_susceptibility" in pattern_by_key,
            "evidence": pattern_by_key.get("surgery_crisis_susceptibility"),
        },
        "accident": {
            "supported": "accident_injury_susceptibility" in pattern_by_key,
            "evidence": pattern_by_key.get("accident_injury_susceptibility"),
        },
        "recovery": {
            "supported": bool(protection),
            "protective_factors": protection[:5],
        },
    }
    return {
        "requested_category": requested_category,
        "constitution": constitution,
        "planet_conditions": conditions,
        "divisional_health_charts": divisions,
        "divisional_confirmations": confirmations,
        "protective_factors": protection[:6],
        "major_vulnerabilities": enhanced_vulnerabilities[:3],
        "mechanism_legend": {
            "acute / inflammatory": "fast, heat, injury or inflammatory expression",
            "chronic / degenerative": "slow, structural or recurring expression",
            "nervous / functional": "stress, nerve or regulation-related expression",
            "fluid / hormonal": "fluid, renal, reproductive or hormonal expression",
        },
        "judgments": judgments,
        "rules": [
            "D1 must establish susceptibility.",
            "D3/D6/D8/D30 may strengthen or weaken confidence, never create a new vulnerability.",
            "Dasha and transit may time only an established natal vulnerability.",
            "A body-system susceptibility is not a diagnosis.",
        ],
    }


def _build_event_patterns(
    planets: Dict[str, Any],
    houses: List[Any],
    residents_map: Dict[int, List[str]],
    house_map: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    patterns: List[Dict[str, Any]] = []
    lord6 = _lord_of_house(houses, 6)
    lord8 = _lord_of_house(houses, 8)
    lord12 = _lord_of_house(houses, 12)

    def company(planet: Optional[str]) -> List[str]:
        if not planet:
            return []
        h = _planet_house(planets, planet)
        if not h:
            return []
        return [p for p in (residents_map.get(h) or []) if p != planet]

    # Accident / injury: 6th lord with Mars/Rahu
    if lord6:
        co = company(lord6)
        hit = [p for p in co if p in {"Mars", "Rahu", "Ketu", "Saturn"}]
        if hit:
            h = _planet_house(planets, lord6)
            sign = _planet_sign(planets, lord6)
            sign_name = SIGN_NAMES[sign] if sign is not None else "--"
            zones = _merge_zones(
                list((HOUSE_BODY.get(h) or {}).get("zones") or [])[:2],
                list((SIGN_BODY.get(sign) or {}).get("zones") or [])[:2],
                list((PLANET_KARAKA.get("Mars") or {}).get("zones") or [])[:2],
            )
            patterns.append({
                "key": "accident_injury_susceptibility",
                "title": "Accident / acute injury susceptibility",
                "summary": (
                    f"6th lord {lord6} shares H{h} ({sign_name}) with {', '.join(hit)}. "
                    "Classical medical astrology reads 6th-lord + Mars/Rahu as heightened accident or acute injury risk."
                ),
                "zones": zones,
                "evidence": [f"6th lord {lord6} in H{h}", f"With {', '.join(hit)}"],
            })

    # Surgery: Mars with dusthana lords / malefics, or Mars in dusthana
    mars_h = _planet_house(planets, "Mars")
    mars_co = company("Mars")
    if mars_h and (
        lord6 in mars_co
        or lord8 in mars_co
        or lord12 in mars_co
        or mars_h in DUSTHANA
        or any(p in {"Rahu", "Ketu", "Saturn", "Jupiter"} for p in mars_co)
    ):
        patterns.append({
            "key": "surgery_crisis_susceptibility",
            "title": "Surgery / invasive-crisis susceptibility",
            "summary": (
                f"Mars in H{mars_h}"
                + (f" with {', '.join(mars_co)}" if mars_co else "")
                + " supports classical surgery / cutting / acute procedural themes when activated by dasha or transit."
            ),
            "zones": _merge_zones(
                list((HOUSE_BODY.get(mars_h) or {}).get("zones") or [])[:2],
                list((PLANET_KARAKA.get("Mars") or {}).get("zones") or [])[:3],
            ),
            "evidence": [f"Mars in H{mars_h}", f"Company: {', '.join(mars_co) or 'none'}"],
        })

    # Feet / rest / hospitalization: 12th × rashi (classical; not 9th)
    if lord12:
        co = company(lord12)
        hit = [p for p in co if p in MALEFICS]
        lord12_h = _planet_house(planets, lord12)
        h12_sign = _house_sign(houses, 12)
        h12_row = next((r for r in house_map if r.get("house") == 12), None)
        h12_malefics = [p for p in ((h12_row or {}).get("residents") or []) if p in MALEFICS]
        if hit or lord12_h in DUSTHANA or h12_malefics:
            zones = _merge_zones(
                list((HOUSE_BODY.get(12) or {}).get("zones") or []),
                list((SIGN_BODY.get(h12_sign) or {}).get("zones") or []) if h12_sign is not None else [],
            )
            patterns.append({
                "key": "twelfth_feet_rest_hospitalization",
                "title": "12th-house feet / rest / hospitalization theme",
                "summary": (
                    f"12th lord {lord12} in H{lord12_h}"
                    + (f" with {', '.join(hit)}" if hit else "")
                    + (
                        f"; 12th house sign {SIGN_NAMES[h12_sign]}"
                        if h12_sign is not None else ""
                    )
                    + ". Classical mapping uses 12th × rashi for feet, sleep, lymph, and hospital/recovery beds."
                ),
                "zones": zones,
                "evidence": [
                    f"12th lord {lord12}",
                    f"12th sign {SIGN_NAMES[h12_sign] if h12_sign is not None else '--'}",
                    f"With {', '.join(hit or h12_malefics) or '—'}",
                ],
            })

    # Vascular / BP tone: Sun/Mars/Saturn pressure in fire signs or kendras/dusthanas
    bp_planets = []
    for p in ("Sun", "Mars", "Saturn", "Rahu"):
        h = _planet_house(planets, p)
        s = _planet_sign(planets, p)
        if h is None:
            continue
        if p in {"Mars", "Saturn", "Rahu"} and (
            h in {1, 2, 4, 6, 8, 10} or (s in {0, 4, 8, 9}) or any(
                x in MALEFICS for x in company(p)
            )
        ):
            bp_planets.append(f"{p} in H{h}")
    if len(bp_planets) >= 2:
        patterns.append({
            "key": "vascular_pressure_tone",
            "title": "Vascular / blood-pressure tone",
            "summary": (
                "Multiple heat/pressure significators (Sun/Mars/Saturn/Rahu) are activated. "
                "Chart tone can favour high vascular pressure or inflammatory blood-heat themes — "
                "lifestyle pacing and medical monitoring if symptoms exist; not a BP diagnosis."
            ),
            "zones": ["blood pressure tone", "blood", "heart", "head"],
            "evidence": bp_planets[:4],
        })

    # Sinus / face / throat: 2nd house malefics
    h2 = next((r for r in house_map if r.get("house") == 2), None)
    if h2 and (set(h2.get("residents") or {}) & MALEFICS):
        patterns.append({
            "key": "sinus_face_throat_susceptibility",
            "title": "Sinus / face / throat susceptibility",
            "summary": (
                f"2nd house in {h2.get('sign')} holds {', '.join(h2.get('residents') or [])}. "
                "House-2 + malefic activation classically maps to face, sinuses, teeth, and throat attention themes — "
                "not a clinical diagnosis."
            ),
            "zones": _merge_zones(
                list(h2.get("fused_zones") or []),
                ["sinuses", "face", "throat", "teeth"],
            ),
            "evidence": [
                f"H2 {h2.get('sign')}",
                f"Residents: {', '.join(h2.get('residents') or [])}",
            ],
        })

    if lord8:
        co = company(lord8)
        if any(p in MALEFICS for p in co) or _planet_house(planets, lord8) in DUSTHANA:
            patterns.append({
                "key": "chronic_hidden_theme",
                "title": "Chronic / hidden vulnerability theme",
                "summary": (
                    f"8th lord {lord8} is under pressure"
                    + (f" with {', '.join([p for p in co if p in MALEFICS])}" if co else "")
                    + ", supporting chronic or hard-to-trace vulnerability themes."
                ),
                "zones": list((HOUSE_BODY.get(8) or {}).get("zones") or []),
                "evidence": [f"8th lord {lord8}", f"Company: {', '.join(co) or '—'}"],
            })

    return patterns[:6]
