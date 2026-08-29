"""
Deterministic Kalapurusha body-zone + event-pattern evidence for Health reports.

Fuses house meaning × sign on house × lord condition × occupants/aspects × nakshatra
into ranked zones and concrete wellness-event patterns the LLM must narrate.
Never diagnoses disease — only chart-grounded susceptibility themes.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List, Mapping, Optional, Tuple

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
    8: {
        "zones": ["anus", "rectum", "pelvis", "excretory organs", "reproductive organs"],
        "role": "chronic / surgery / sudden events",
    },
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

# Nakshatra Purusha anatomy.  This is intentionally kept separate from the
# broader temperament hints below: for medical ranking the 6th lord's exact
# nakshatra supplies a concrete anatomical candidate, not merely a doshic tone.
# Canonical 27-fold Nakshatra Purusha anatomy used by the health engine.
# Source family: Narada-Purana anatomical sequence, as summarized in the
# supplied Dr. K. S. Charak computational framework.  Keep this as one table:
# reports, Instant, and evidence UI must never maintain competing mappings.
NAKSHATRA_BODY: Dict[str, List[str]] = {
    "ashwini": ["knees"],
    "bharani": ["head"],
    "krittika": ["waist"],
    "rohini": ["legs"],
    "mrigashira": ["eyes"],
    "ardra": ["hair"],
    "punarvasu": ["fingers"],
    "pushya": ["mouth", "face"],
    "ashlesha": ["nails"],
    "magha": ["nose"],
    "purva phalguni": ["private parts"],
    "uttara phalguni": ["private parts"],
    "hasta": ["hands"],
    "chitra": ["forehead"],
    "swati": ["teeth"],
    "vishakha": ["upper limbs"],
    "anuradha": ["heart"],
    "jyeshtha": ["tongue"],
    "mula": ["feet"],
    "moola": ["feet"],
    "purva ashada": ["thighs"],
    "purvashada": ["thighs"],
    "purva ashadha": ["thighs"],
    "uttara ashada": ["thighs"],
    "uttarashada": ["thighs"],
    "uttara ashadha": ["thighs"],
    "shravana": ["ears"],
    "dhanishta": ["back"],
    "shatabhisha": ["chin"],
    "shatabhishak": ["chin"],
    "purva bhadrapada": ["sides of body"],
    "uttara bhadrapada": ["sides of body"],
    "revati": ["armpits", "groins"],
}

# Production payloads have historically used several transliterations and
# separators for the same nakshatra.  Resolve those at one boundary so every
# one of the 27 mappings works for reports, Instant and evidence rendering.
NAKSHATRA_ALIASES: Dict[str, str] = {
    "aswini": "ashwini",
    "asvini": "ashwini",
    "krttika": "krittika",
    "mrigasira": "mrigashira",
    "mrgasira": "mrigashira",
    "mrgashira": "mrigashira",
    "mrugasira": "mrigashira",
    "aslesha": "ashlesha",
    "aslesa": "ashlesha",
    "pusya": "pushya",
    "pushyami": "pushya",
    "citra": "chitra",
    "svati": "swati",
    "visakha": "vishakha",
    "jyeshta": "jyeshtha",
    "jyestha": "jyeshtha",
    "moola": "mula",
    "poorvaphalguni": "purvaphalguni",
    "uttaraphalguni": "uttaraphalguni",
    "poorvaashada": "purvaashada",
    "poorvaashadha": "purvaashada",
    "purvashada": "purvaashada",
    "poorvashadha": "purvaashada",
    "purvaashadha": "purvaashada",
    "uttarashada": "uttaraashada",
    "uttaraashadha": "uttaraashada",
    "sravana": "shravana",
    "dhanista": "dhanishta",
    "satabhisa": "shatabhisha",
    "satabhisha": "shatabhisha",
    "satabhishak": "shatabhisha",
    "shatabhishak": "shatabhisha",
    "poorvabhadrapada": "purvabhadrapada",
    "purvabhadra": "purvabhadrapada",
    "uttarabhadra": "uttarabhadrapada",
    "revathi": "revati",
}


def _nakshatra_key(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    ascii_text = "".join(char for char in text if not unicodedata.combining(char))
    key = re.sub(r"[^a-z]", "", ascii_text.lower())
    return NAKSHATRA_ALIASES.get(key, key)


def _nakshatra_body_zones(value: Any) -> List[str]:
    key = _nakshatra_key(value)
    for canonical_name, zones in NAKSHATRA_BODY.items():
        if _nakshatra_key(canonical_name) == key:
            return list(zones)
    return []

# Closely related anatomical labels must read as one vulnerability, not as
# several independent findings.  These families are deliberately small: they
# merge synonyms/one clinical region while leaving genuinely different organs
# (for example liver versus thighs) separate.
ANATOMICAL_FAMILIES: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("face and jaw (including lips and chin)", ("face", "forehead", "lips", "chin", "mouth")),
    ("heart and upper spine/back", ("heart", "spine", "upper back", "heart region")),
    ("hips and thighs", ("hips", "thighs", "right thigh", "left thigh")),
    ("anorectal and pelvic region", ("anus", "rectum", "pelvis", "excretory organs")),
)

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
        lower = _nakshatra_key(name)
        zones: List[str] = []
        tone = ""
        if lower in {"swati", "ashwini", "shatabhisha", "punarvasu"}:
            zones = ["nerves", "breath", "circulation", "anxiety tone"]
            tone = "Vayu / airy nervous-respiratory flavour"
        elif lower in {"magha", "uttaraphalguni", "purvaphalguni", "krittika"}:
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


def _sixth_lord_nakshatra(lords_nakshatra: Dict[str, Any]) -> Dict[str, Any]:
    row = (lords_nakshatra or {}).get("sixth_lord") or {}
    nak = row.get("nakshatra") or {}
    name = str(nak.get("nakshatra") or nak.get("name") or "").strip()
    lord = nak.get("lord") or nak.get("nakshatra_lord")
    return {
        "planet": row.get("planet"),
        "name": name or None,
        "lord": lord,
        "pada": nak.get("pada"),
        "zones": _nakshatra_body_zones(name),
    }


def _add_primary_medical_factor(
    buckets: Dict[str, Dict[str, Any]],
    *,
    zones: List[str],
    factor: str,
    label: str,
    base_weight: int,
) -> None:
    """Add a 6th-house-chain factor while preserving its provenance.

    Earlier items in a classical anatomical list are more specific, so they
    receive a small ordering advantage.  This prevents four broad synonyms
    from tying and being selected arbitrarily.
    """
    for index, zone in enumerate(zones or []):
        key = str(zone).strip().lower()
        if not key:
            continue
        weight = max(base_weight - (index * 2), base_weight - 6)
        bucket = buckets.setdefault(key, {
            "zone": zone, "weight": 0, "standing_weight": 0,
            "sources": [], "why": [], "natal_layers": [],
            "activation_sources": [], "primary_medical_factors": [],
            "primary_medical_reasons": [],
            "primary_medical_factor_rank": {},
        })
        bucket["weight"] += weight
        bucket["standing_weight"] += weight
        layer = f"sixth_chain:{factor}"
        if layer not in bucket["natal_layers"]:
            bucket["natal_layers"].append(layer)
        if factor not in bucket["primary_medical_factors"]:
            bucket["primary_medical_factors"].append(factor)
        ranks = bucket.setdefault("primary_medical_factor_rank", {})
        ranks[factor] = min(int(ranks.get(factor, index)), index)
        if label not in bucket["sources"]:
            bucket["sources"].append(label)
        if label not in bucket["why"]:
            bucket["why"].append(label)
        if label not in bucket["primary_medical_reasons"]:
            bucket["primary_medical_reasons"].append(label)


def _group_anatomical_families(buckets: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Collapse anatomical synonyms without multiplying their evidence.

    A single Magha calculation can yield lips, chin and face.  Summing those
    labels would falsely turn one calculation into three confirmations.  The
    merged family therefore keeps the strongest score for a member and unions
    provenance lists; genuinely different calculation factors remain visible.
    """
    member_to_family = {
        member: (label, members)
        for label, members in ANATOMICAL_FAMILIES
        for member in members
    }
    grouped: Dict[str, Dict[str, Any]] = {}
    list_fields = (
        "sources", "why", "natal_layers", "activation_sources",
        "primary_medical_factors", "confirmation_factors",
        "primary_medical_reasons",
    )
    for raw_key, raw_bucket in buckets.items():
        family = member_to_family.get(str(raw_key).strip().lower())
        label = family[0] if family else str(raw_bucket.get("zone") or raw_key)
        members = family[1] if family else (str(raw_bucket.get("zone") or raw_key),)
        key = label.lower()
        target = grouped.setdefault(key, {
            "zone": label,
            "anatomical_members": [],
            "weight": 0,
            "standing_weight": 0,
            **{field: [] for field in list_fields},
            "primary_medical_factor_rank": {},
        })
        # Synonyms produced by the same calculation are alternatives, not
        # additive evidence.  The highest member score represents the family.
        target["weight"] = max(int(target.get("weight") or 0), int(raw_bucket.get("weight") or 0))
        target["standing_weight"] = max(
            int(target.get("standing_weight") or 0),
            int(raw_bucket.get("standing_weight") or 0),
        )
        raw_zone = str(raw_bucket.get("zone") or raw_key).strip()
        if raw_zone and raw_zone not in target["anatomical_members"]:
            target["anatomical_members"].append(raw_zone)
        for member in members:
            if member in buckets and member not in target["anatomical_members"]:
                target["anatomical_members"].append(member)
        for field in list_fields:
            for value in raw_bucket.get(field) or []:
                if value not in target[field]:
                    target[field].append(value)
        for factor, rank in (raw_bucket.get("primary_medical_factor_rank") or {}).items():
            current = target["primary_medical_factor_rank"].get(factor)
            target["primary_medical_factor_rank"][factor] = (
                int(rank) if current is None else min(int(current), int(rank))
            )
    return grouped


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

    # The classical medical foundation is the 6th-house chain. It establishes
    # the anatomy eligible to become a named major vulnerability: sign in H6,
    # sign occupied by its lord, the lord's nakshatra, and the anatomical field
    # of the house occupied by the 6th lord.  The destination house is a valid
    # contributor, but no one factor is sufficient for a narrow diagnosis.
    sixth_sign = _house_sign(houses, 6)
    sixth_lord = _lord_of_house(houses, 6)
    sixth_lord_sign = _planet_sign(planets, sixth_lord) if sixth_lord else None
    sixth_nakshatra = _sixth_lord_nakshatra(lords_nakshatra or {})
    sixth_lord_house = _planet_house(planets, sixth_lord) if sixth_lord else None
    sixth_house_chain = {
        "sixth_house_sign": SIGN_NAMES[sixth_sign] if sixth_sign is not None else None,
        "sixth_house_sign_zones": list((SIGN_BODY.get(sixth_sign) or {}).get("zones") or []),
        "sixth_lord": sixth_lord,
        "sixth_lord_house": sixth_lord_house,
        "sixth_lord_house_zones": list((HOUSE_BODY.get(sixth_lord_house) or {}).get("zones") or []),
        "sixth_lord_sign": SIGN_NAMES[sixth_lord_sign] if sixth_lord_sign is not None else None,
        "sixth_lord_sign_zones": list((SIGN_BODY.get(sixth_lord_sign) or {}).get("zones") or []),
        "sixth_lord_nakshatra": sixth_nakshatra.get("name"),
        "sixth_lord_nakshatra_pada": sixth_nakshatra.get("pada"),
        "sixth_lord_nakshatra_lord": sixth_nakshatra.get("lord"),
        "sixth_lord_nakshatra_zones": sixth_nakshatra.get("zones") or [],
    }

    # Aggregate priority zone cards.
    zone_weights: Dict[str, Dict[str, Any]] = {}
    if sixth_sign is not None:
        _add_primary_medical_factor(
            zone_weights,
            zones=sixth_house_chain["sixth_house_sign_zones"],
            factor="sixth_house_sign",
            label=(
                f"The sign in House 6 is {SIGN_NAMES[sixth_sign]}, linking the disease axis "
                f"to {', '.join(sixth_house_chain['sixth_house_sign_zones'][:3])}."
            ),
            base_weight=18,
        )
    if sixth_lord and sixth_lord_sign is not None:
        _add_primary_medical_factor(
            zone_weights,
            zones=sixth_house_chain["sixth_lord_sign_zones"],
            factor="sixth_lord_sign",
            label=(
                f"House 6 lord {sixth_lord} is in {SIGN_NAMES[sixth_lord_sign]}, focusing its "
                f"health indication on {', '.join(sixth_house_chain['sixth_lord_sign_zones'][:3])}."
            ),
            base_weight=20,
        )
    if sixth_nakshatra.get("name") and sixth_nakshatra.get("zones"):
        pada_text = f" pada {sixth_nakshatra.get('pada')}" if sixth_nakshatra.get("pada") else ""
        lord_text = f", ruled by {sixth_nakshatra.get('lord')}" if sixth_nakshatra.get("lord") else ""
        _add_primary_medical_factor(
            zone_weights,
            zones=sixth_nakshatra["zones"],
            factor="sixth_lord_nakshatra",
            label=(
                f"House 6 lord {sixth_lord} occupies {sixth_nakshatra['name']}{pada_text}{lord_text}; "
                f"its anatomical focus is {', '.join(sixth_nakshatra['zones'][:3])}."
            ),
            base_weight=24,
        )
        nak_lord = str(sixth_nakshatra.get("lord") or "").strip()
        nak_lord_house = _planet_house(planets, nak_lord) if nak_lord else None
        nak_lord_sign = _planet_sign(planets, nak_lord) if nak_lord else None
        if nak_lord and nak_lord_house:
            confirmation = (
                f"Its nakshatra lord {nak_lord} is placed in House {nak_lord_house}"
                + (
                    f" in {SIGN_NAMES[nak_lord_sign]}"
                    if nak_lord_sign is not None else ""
                )
                + ", confirming how this anatomical indication is expressed."
            )
            for zone in sixth_nakshatra["zones"]:
                bucket = zone_weights.get(str(zone).strip().lower())
                if not bucket:
                    continue
                bucket["weight"] += 3
                bucket["standing_weight"] += 3
                confirmations = bucket.setdefault("confirmation_factors", [])
                if "nakshatra_lord_condition" not in confirmations:
                    confirmations.append("nakshatra_lord_condition")
                if "sixth_chain:nakshatra_lord_condition" not in bucket["natal_layers"]:
                    bucket["natal_layers"].append("sixth_chain:nakshatra_lord_condition")
                if confirmation not in bucket["sources"]:
                    bucket["sources"].append(confirmation)
                if confirmation not in bucket["why"]:
                    bucket["why"].append(confirmation)
    if sixth_lord and sixth_lord_house:
        destination_zones = sixth_house_chain["sixth_lord_house_zones"]
        _add_primary_medical_factor(
            zone_weights,
            zones=destination_zones,
            factor="sixth_lord_house",
            label=(
                f"House 6 lord {sixth_lord} is placed in House {sixth_lord_house}; "
                f"that house's anatomical field includes {', '.join(destination_zones[:4])}."
            ),
            # This is a real anatomical limb of the medical chain, but ranks
            # below the exact nakshatra and rashi mappings unless corroborated.
            base_weight=16,
        )
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

    # Present anatomical regions rather than duplicate synonyms such as
    # "face", "lips" and "chin" as separate vulnerabilities.
    zone_weights = _group_anatomical_families(zone_weights)

    priority_zones = sorted(
        zone_weights.values(),
        key=lambda z: (
            0 if z.get("primary_medical_factors") else 1,
            min(
                (
                    {
                        "sixth_lord_nakshatra": 0,
                        "sixth_lord_sign": 1,
                        "sixth_house_sign": 2,
                        "sixth_lord_house": 3,
                    }.get(factor, 9)
                    for factor in (z.get("primary_medical_factors") or [])
                ),
                default=9,
            ),
            -len(z.get("primary_medical_factors") or []),
            -int(z.get("weight") or 0),
        ),
    )
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
        primary_factor_count = len(item.get("primary_medical_factors") or [])
        confirmation_factor_count = len(item.get("confirmation_factors") or [])
        standing_weight = int(item.get("standing_weight") or 0)
        # Each limb of the classical sixth-house chain is an independently
        # calculated anatomical factor.  Do not collapse H6 sign, sixth-lord
        # sign and sixth-lord nakshatra into one opaque evidence count.
        item["confluence_count"] = primary_factor_count + confirmation_factor_count
        # Confirmation cannot invent anatomy. Other houses, karakas and vargas
        # may only strengthen or weaken a 6th-house-chain candidate.
        has_primary_basis = bool(item.get("primary_medical_factors"))
        item["callout_allowed"] = has_primary_basis and standing_weight >= 12
        item["confidence"] = (
            "high" if item["confluence_count"] >= 3 and standing_weight >= 14
            else "medium" if item["callout_allowed"]
            else "directional"
        )

    # Keep the general-vulnerability answer compact while preserving every
    # distinct limb of the classical sixth-house chain.  The exact nakshatra,
    # lord-sign and H6-sign regions come first; the sixth lord's destination
    # house may add one further, distinct anatomical region.  In particular,
    # a 6th lord in H8 must not lose the anorectal/pelvic field merely because
    # three more specific sign/nakshatra regions were already selected.
    selected_major_zones: List[Dict[str, Any]] = []
    selected_zone_names = set()
    for factor in (
        "sixth_lord_nakshatra",
        "sixth_lord_sign",
        "sixth_house_sign",
        "sixth_lord_house",
    ):
        # A destination-house body field is broad. Preserve it as a major
        # constitutional callout when the disease lord lands in a medical
        # dusthana (H6/H8/H12); elsewhere it remains available in the full
        # evidence ranking without displacing the three precise rashi/star
        # regions. This makes 6L-in-8 retain the anorectal/pelvic indication.
        if factor == "sixth_lord_house" and sixth_lord_house not in DUSTHANA:
            continue
        candidates = [
            item for item in priority_zones
            if item.get("callout_allowed")
            and factor in (item.get("primary_medical_factors") or [])
            and str(item.get("zone") or "").lower() not in selected_zone_names
        ]
        candidate = min(
            candidates,
            key=lambda item: (
                int((item.get("primary_medical_factor_rank") or {}).get(factor, 99)),
                -int(item.get("standing_weight") or 0),
            ),
            default=None,
        )
        if candidate and len(selected_major_zones) < 4:
            selected_major_zones.append(candidate)
            selected_zone_names.add(str(candidate.get("zone") or "").lower())

    major_vulnerabilities = [
        {
            "zone": item.get("zone"),
            "confidence": item.get("confidence"),
            "confluence_count": item.get("confluence_count"),
            "standing_weight": item.get("standing_weight"),
            "natal_layers": list(item.get("natal_layers") or [])[:6],
            "activation_sources": list(item.get("activation_sources") or [])[:3],
            "primary_medical_factors": list(item.get("primary_medical_factors") or [])[:3],
            "primary_medical_reasons": list(item.get("primary_medical_reasons") or [])[:3],
            "confirmation_factors": list(item.get("confirmation_factors") or [])[:3],
            "anatomical_members": list(item.get("anatomical_members") or [])[:6],
            "sources": list(item.get("sources") or [])[:5],
            "why": list(item.get("why") or [])[:4],
        }
        for item in selected_major_zones[:4]
    ]

    medical_profile = _build_medical_profile(
        chart=chart,
        house_map=house_map,
        sixth_house_chain=sixth_house_chain,
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
        "sixth_house_chain": sixth_house_chain,
        "event_patterns": event_patterns,
        "top_zone_names": [z.get("zone") for z in major_vulnerabilities],
        "claim_policy": {
            "named_body_part_requires": (
                "The zone must originate in the sign in House 6, the sign or house occupied by "
                "its lord, or the 6th lord's nakshatra; other natal layers may only confirm and rank it."
            ),
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
    sixth_house_chain: Dict[str, Any],
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
        primary_factors = set(vulnerability.get("primary_medical_factors") or [])
        source_planets: List[str] = []
        sixth_lord = str(sixth_house_chain.get("sixth_lord") or "").strip()
        nakshatra_lord = str(sixth_house_chain.get("sixth_lord_nakshatra_lord") or "").strip()
        if sixth_lord:
            source_planets.append(sixth_lord)
        if "sixth_lord_nakshatra" in primary_factors and nakshatra_lord and nakshatra_lord not in source_planets:
            source_planets.append(nakshatra_lord)
        repeated: List[str] = []
        for code, division in divisions.items():
            for planet in source_planets:
                drow = (division.get("planets") or {}).get(planet) or {}
                if drow.get("house") in DUSTHANA:
                    repeated.append(f"{code}: {planet} repeats in health-sensitive House {drow.get('house')}")
        confidence = str(vulnerability.get("confidence") or "directional")
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
    condition_keys = {
        "vascular_pressure_tone",
        "mental_emotional_regulation_susceptibility",
        "metabolic_blood_sugar_susceptibility",
    }
    condition_susceptibilities = [
        {
            "key": row.get("key"),
            "title": row.get("title"),
            "risk_level": row.get("risk_level") or "directional",
            "evidence": list(row.get("evidence") or [])[:5],
            "interpretation": row.get("summary"),
            "responsible_guidance": row.get("user_framing"),
            "diagnosis": False,
        }
        for row in event_patterns
        if str(row.get("key") or "") in condition_keys
    ]
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
            "vulnerabilities": enhanced_vulnerabilities[:4],
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
        "condition_susceptibilities": condition_susceptibilities,
    }
    return {
        "requested_category": requested_category,
        "constitution": constitution,
        "sixth_house_chain": sixth_house_chain,
        "planet_conditions": conditions,
        "divisional_health_charts": divisions,
        "divisional_confirmations": confirmations,
        "protective_factors": protection[:6],
        "major_vulnerabilities": enhanced_vulnerabilities[:4],
        "condition_susceptibilities": condition_susceptibilities,
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

    def house_row(house: Optional[int]) -> Dict[str, Any]:
        return next((row for row in house_map if row.get("house") == house), {})

    def pressure_on_planet(planet: str) -> List[str]:
        """Return independent natal pressure indicators, not a diagnosis."""
        house = _planet_house(planets, planet)
        if not house:
            return []
        indicators: List[str] = []
        conjunctions = [p for p in company(planet) if p in MALEFICS and p != planet]
        if conjunctions:
            indicators.append(f"{planet} is conjunct {', '.join(conjunctions)} in House {house}")
        aspectors = [
            p for p in (house_row(house).get("aspecting_planets") or [])
            if p in MALEFICS and p != planet
        ]
        if aspectors:
            indicators.append(f"{planet} receives pressure from {', '.join(aspectors)}")
        if house in DUSTHANA:
            indicators.append(f"{planet} is placed in health-sensitive House {house}")
        return indicators

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

    # Vascular / BP regulation. A broad Mars/Saturn/Rahu placement is not
    # sufficient: require independent convergence across the Sun/vascular
    # karaka, heart houses, and a heat-pressure combination.
    bp_factors: List[str] = []
    sun_pressure = pressure_on_planet("Sun")
    if sun_pressure:
        bp_factors.append(f"Vital/vascular karaka under pressure: {sun_pressure[0]}")
    for heart_house, label in ((4, "cardiac foundation"), (5, "heart and circulation")):
        row = house_row(heart_house)
        actors = list(dict.fromkeys(
            [p for p in (row.get("residents") or []) if p in MALEFICS]
            + [p for p in (row.get("aspecting_planets") or []) if p in MALEFICS]
        ))
        if actors:
            bp_factors.append(f"House {heart_house} ({label}) is under pressure from {', '.join(actors)}")
    pressure_pairs = []
    for planet in ("Mars", "Saturn", "Rahu"):
        co = [p for p in company(planet) if p in {"Mars", "Saturn", "Rahu"} and p != planet]
        if co:
            pair = " + ".join(sorted((planet, co[0])))
            if pair not in pressure_pairs:
                pressure_pairs.append(pair)
    if pressure_pairs:
        bp_factors.append(f"Heat/pressure combination: {', '.join(pressure_pairs)}")
    pitta_actors = []
    for planet in ("Sun", "Mars", "Ketu"):
        sign = _planet_sign(planets, planet)
        house = _planet_house(planets, planet)
        if sign in {0, 4, 8} and house in {1, 4, 5, 6, 8, 10}:
            pitta_actors.append(planet)
    if len(pitta_actors) >= 2:
        bp_factors.append(f"Concentrated Pitta/heat signature: {', '.join(pitta_actors)}")
    bp_factors = list(dict.fromkeys(bp_factors))
    if len(bp_factors) >= 2:
        patterns.append({
            "key": "vascular_pressure_tone",
            "title": "Vascular / blood-pressure tone",
            "summary": (
                "Multiple heat/pressure significators (Sun/Mars/Saturn/Rahu) are activated. "
                "Chart tone can favour high vascular pressure or inflammatory blood-heat themes — "
                "lifestyle pacing and medical monitoring if symptoms exist; not a BP diagnosis."
            ),
            "zones": ["blood pressure tone", "blood", "heart", "head"],
            "evidence": bp_factors[:4],
            "risk_level": "elevated" if len(bp_factors) >= 3 else "moderate",
            "user_framing": (
                "The chart shows a preventive-attention signal for vascular or blood-pressure regulation. "
                "It does not establish hypertension; routine BP checks are sensible, especially if symptoms or family history exist."
            ),
        })

    # Mental/emotional regulation: keep conjunction, aspect and broader
    # multi-factor pressure distinct.  In particular, a Ketu aspect to the
    # Moon must never be relabelled as the Moon occupying the nodal axis.
    moon_house = _planet_house(planets, "Moon")
    moon_company = company("Moon")
    mental_evidence: List[str] = []
    moon_shares_house_with_ketu = "Ketu" in moon_company
    if moon_shares_house_with_ketu:
        mental_evidence.append(f"Moon shares House {moon_house} with Ketu")
    mental_evidence.extend(pressure_on_planet("Moon"))
    mercury_pressure = pressure_on_planet("Mercury")
    if mercury_pressure:
        mental_evidence.append(mercury_pressure[0])
    for mental_house, label in ((4, "emotional security"), (5, "judgment and emotional processing")):
        row = house_row(mental_house)
        malefic_residents = [p for p in (row.get("residents") or []) if p in MALEFICS]
        malefic_aspects = [p for p in (row.get("aspecting_planets") or []) if p in MALEFICS]
        if malefic_residents or malefic_aspects:
            actors = list(dict.fromkeys(malefic_residents + malefic_aspects))
            mental_evidence.append(f"House {mental_house} ({label}) is under pressure from {', '.join(actors)}")
    mental_evidence = list(dict.fromkeys(mental_evidence))
    moon_receives_ketu_aspect = any(
        line.startswith("Moon receives pressure from") and "Ketu" in line
        for line in mental_evidence
    )
    if moon_shares_house_with_ketu:
        mental_summary = (
            "Moon and Ketu sharing a house, together with the other calculated mental-regulation factors, "
            "can show detachment, rumination, sleep disruption, emotional volatility or periods of "
            "psychological strain. This is a vulnerability signal, not proof of a mental disorder."
        )
    elif moon_receives_ketu_aspect:
        mental_summary = (
            "Ketu's calculated aspect to the Moon, together with the other Moon, Mercury and emotional-house "
            "pressure factors listed here, can show detachment, rumination, sleep disruption, emotional "
            "volatility or periods of psychological strain. This is a vulnerability signal, not proof of a "
            "mental disorder. The Moon is not conjunct Ketu or on the nodal axis."
        )
    else:
        mental_summary = (
            "The combined calculated pressure on the Moon, Mercury and emotional-regulation houses can show "
            "rumination, sleep disruption, emotional volatility or periods of psychological strain. This is "
            "a vulnerability signal, not proof of a mental disorder."
        )
    if moon_shares_house_with_ketu or len(mental_evidence) >= 3:
        patterns.append({
            "key": "mental_emotional_regulation_susceptibility",
            "title": "Mental and emotional regulation susceptibility",
            "summary": mental_summary,
            "zones": ["mind", "sleep", "nervous regulation"],
            "evidence": mental_evidence[:5],
            "risk_level": "elevated" if len(mental_evidence) >= 3 else "moderate",
            "user_framing": (
                "This pattern deserves preventive attention to mental wellbeing. If persistent anxiety, low mood, "
                "confusion, severe sleep disturbance, or loss of functioning is present, professional assessment is appropriate."
            ),
        })

    # Metabolic/blood-sugar susceptibility needs a confluence: Jupiter/Venus
    # condition plus the food/metabolism/disease axis. Never infer diabetes
    # from Jupiter or Venus alone.
    metabolic_evidence: List[str] = []
    metabolic_factor_classes = set()
    jupiter_pressure = pressure_on_planet("Jupiter")
    if jupiter_pressure:
        metabolic_factor_classes.add("jupiter")
        metabolic_evidence.append(f"Jupiter/metabolic karaka under pressure: {jupiter_pressure[0]}")
    venus_house = _planet_house(planets, "Venus")
    venus_pressure = pressure_on_planet("Venus")
    lord6 = _lord_of_house(houses, 6)
    if venus_house == 6:
        metabolic_factor_classes.add("venus")
        metabolic_evidence.append("Venus/endocrine karaka is placed in House 6")
    elif lord6 and lord6 in company("Venus"):
        metabolic_factor_classes.add("venus")
        metabolic_evidence.append(f"Venus/endocrine karaka is conjunct House 6 lord {lord6}")
    elif venus_pressure:
        metabolic_factor_classes.add("venus")
        metabolic_evidence.append(f"Venus/endocrine karaka under pressure: {venus_pressure[0]}")
    h2 = house_row(2)
    h6 = house_row(6)
    metabolic_axis_planets = {"Jupiter", "Venus", "Moon", "Rahu", "Saturn"}
    for house, label, row in ((2, "food and intake", h2), (6, "disease and regulation", h6)):
        actors = [
            p for p in list(row.get("residents") or []) + list(row.get("aspecting_planets") or [])
            if p in metabolic_axis_planets
        ]
        actors = list(dict.fromkeys(actors))
        if len(actors) >= 2:
            metabolic_factor_classes.add(f"axis_h{house}")
            metabolic_evidence.append(f"House {house} ({label}) is linked with {', '.join(actors)}")
    metabolic_evidence = list(dict.fromkeys(metabolic_evidence))
    if len(metabolic_factor_classes) >= 2:
        patterns.append({
            "key": "metabolic_blood_sugar_susceptibility",
            "title": "Metabolic / blood-sugar regulation susceptibility",
            "summary": (
                "Multiple metabolism, intake and disease-axis factors converge. This can justify preventive "
                "attention to blood-sugar and metabolic regulation, but it does not establish diabetes."
            ),
            "zones": ["metabolic regulation", "blood sugar tone", "liver", "pancreatic-endocrine axis"],
            "evidence": metabolic_evidence[:5],
            "risk_level": "elevated" if len(metabolic_factor_classes) >= 3 else "moderate",
            "user_framing": (
                "If there is family history, weight change, excess thirst/urination, fatigue, or prior abnormal results, "
                "routine glucose/HbA1c screening is a prudent medical check."
            ),
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

    # Keep distinct responsible condition signals available to the prompt and
    # evidence UI. The previous six-item cap could silently discard mental or
    # metabolic findings after accident/surgery/house patterns were added.
    return patterns[:10]


def _lords_nakshatra_from_chart(chart: Dict[str, Any]) -> Dict[str, Any]:
    """Build the sixth-lord nakshatra payload Instant Chat and reports share."""
    try:
        from .shared_branch_context import build_nakshatra_context

        nakshatra = build_nakshatra_context(chart)
        positions = (nakshatra.get("positions") or {}) if isinstance(nakshatra, dict) else {}
    except Exception:
        positions = {}
    houses = chart.get("houses") or []
    sixth_lord = _lord_of_house(houses, 6)
    eighth_lord = _lord_of_house(houses, 8)
    lagna_lord = _lord_of_house(houses, 1)

    def row_for(planet: Optional[str]) -> Dict[str, Any]:
        if not planet:
            return {}
        nak_row = positions.get(planet) or {}
        return {
            "planet": planet,
            "nakshatra": {
                "nakshatra": nak_row.get("nakshatra_name") or nak_row.get("nakshatra"),
                "lord": nak_row.get("nakshatra_lord") or nak_row.get("lord"),
                "pada": nak_row.get("pada"),
                "deity": nak_row.get("nakshatra_deity"),
                "longitude": nak_row.get("longitude"),
            },
        }

    return {
        "lagna_lord": row_for(lagna_lord),
        "sixth_lord": row_for(sixth_lord),
        "eighth_lord": row_for(eighth_lord),
        "moon": row_for("Moon"),
    }


def compute_health_body_zone_map(
    chart: Dict[str, Any],
    *,
    lords_nakshatra: Optional[Dict[str, Any]] = None,
    current_dashas: Optional[Dict[str, Any]] = None,
    divisional_charts: Optional[Dict[str, Any]] = None,
    planet_conditions: Optional[Dict[str, Any]] = None,
    requested_category: str = "health",
) -> Dict[str, Any]:
    """Run the sixth-house body-zone calculator, filling nakshatra from the chart when omitted."""
    return build_priority_body_zones(
        chart,
        lords_nakshatra=lords_nakshatra if lords_nakshatra is not None else _lords_nakshatra_from_chart(chart),
        current_dashas=current_dashas,
        divisional_charts=divisional_charts,
        planet_conditions=planet_conditions,
        requested_category=requested_category,
    )


def sixth_house_chain_limbs(chain: Mapping[str, Any] | Dict[str, Any] | None) -> List[Dict[str, Any]]:
    """Display-ready limbs of the classical sixth-house anatomical chain."""
    chain = chain if isinstance(chain, dict) else {}
    lord = str(chain.get("sixth_lord") or "the 6th lord").strip()
    limbs: List[Dict[str, Any]] = []

    sixth_sign = str(chain.get("sixth_house_sign") or "").strip()
    if sixth_sign:
        limbs.append({
            "factor": "sixth_house_sign",
            "label": "House 6 sign",
            "anchor": sixth_sign,
            "detail": f"House 6 is {sixth_sign}",
            "zones": list(chain.get("sixth_house_sign_zones") or [])[:4],
        })
    lord_sign = str(chain.get("sixth_lord_sign") or "").strip()
    if lord and lord_sign:
        limbs.append({
            "factor": "sixth_lord_sign",
            "label": "6th lord sign",
            "anchor": f"{lord} in {lord_sign}",
            "detail": f"6th lord {lord} occupies {lord_sign}",
            "zones": list(chain.get("sixth_lord_sign_zones") or [])[:4],
        })
    nakshatra = str(chain.get("sixth_lord_nakshatra") or "").strip()
    if lord and nakshatra:
        pada = chain.get("sixth_lord_nakshatra_pada")
        nak_lord = str(chain.get("sixth_lord_nakshatra_lord") or "").strip()
        detail = f"6th lord {lord} occupies {nakshatra}"
        if pada:
            detail += f" pada {pada}"
        if nak_lord:
            detail += f", ruled by {nak_lord}"
        limbs.append({
            "factor": "sixth_lord_nakshatra",
            "label": "6th lord nakshatra",
            "anchor": nakshatra,
            "detail": detail,
            "zones": list(chain.get("sixth_lord_nakshatra_zones") or [])[:4],
        })
    lord_house = chain.get("sixth_lord_house")
    if lord and lord_house:
        limbs.append({
            "factor": "sixth_lord_house",
            "label": "6th lord house",
            "anchor": f"{lord} in House {lord_house}",
            "detail": f"6th lord {lord} is placed in House {lord_house}",
            "zones": list(chain.get("sixth_lord_house_zones") or [])[:4],
        })
    return limbs


def compact_health_body_zone_map(value: Any) -> Dict[str, Any]:
    """Bounded payload for Instant Chat, health analysis UI, and the LLM."""
    if not isinstance(value, dict):
        return {}

    zone_keys = (
        "zone",
        "anatomical_members",
        "confidence",
        "confluence_count",
        "primary_medical_reasons",
        "primary_medical_factors",
        "confirmation_factors",
        "natal_layers",
        "sources",
        "why",
        "mechanisms",
        "divisional_repetition",
        "activation_sources",
    )
    chain_keys = (
        "sixth_house_sign",
        "sixth_house_sign_zones",
        "sixth_lord",
        "sixth_lord_house",
        "sixth_lord_house_zones",
        "sixth_lord_sign",
        "sixth_lord_sign_zones",
        "sixth_lord_nakshatra",
        "sixth_lord_nakshatra_pada",
        "sixth_lord_nakshatra_lord",
        "sixth_lord_nakshatra_zones",
    )

    def selected(source: Any, keys: tuple[str, ...]) -> Dict[str, Any]:
        if not isinstance(source, dict):
            return {}
        return {
            key: source.get(key)
            for key in keys
            if source.get(key) not in (None, "", [], {})
        }

    chain = selected(value.get("sixth_house_chain"), chain_keys)
    medical_profile = value.get("medical_profile") if isinstance(value.get("medical_profile"), dict) else {}
    calculated = [row for row in list(value.get("major_vulnerabilities") or []) if isinstance(row, dict)]
    profile_rows = [
        row for row in list(medical_profile.get("major_vulnerabilities") or [])
        if isinstance(row, dict)
    ]
    calculated_by_zone = {
        str(row.get("zone") or "").strip().lower(): row
        for row in calculated
        if str(row.get("zone") or "").strip()
    }
    merged_rows: List[Dict[str, Any]] = []
    seen_zones = set()
    for row in profile_rows or calculated:
        zone_key = str(row.get("zone") or "").strip().lower()
        base = calculated_by_zone.get(zone_key) or {}
        combined = {**base, **row}
        for rich_key in ("primary_medical_reasons", "primary_medical_factors", "anatomical_members"):
            if not combined.get(rich_key) and base.get(rich_key):
                combined[rich_key] = base[rich_key]
        selected_row = selected(combined, zone_keys)
        if selected_row:
            merged_rows.append(selected_row)
        if zone_key:
            seen_zones.add(zone_key)
    for row in calculated:
        zone_key = str(row.get("zone") or "").strip().lower()
        if zone_key and zone_key not in seen_zones:
            merged_rows.append(selected(row, zone_keys))
            seen_zones.add(zone_key)
    majors = [row for row in merged_rows[:4] if row]
    result = {
        "major_vulnerabilities": majors,
        "sixth_house_chain": chain,
        "chain_limbs": sixth_house_chain_limbs(chain),
        "top_zone_names": [row.get("zone") for row in majors if row.get("zone")],
        "claim_policy": value.get("claim_policy"),
        "disclaimer": value.get("disclaimer"),
    }
    conditions = list(medical_profile.get("condition_susceptibilities") or [])[:4]
    if conditions:
        result["condition_susceptibilities"] = [
            selected(row, (
                "key", "title", "risk_level", "evidence",
                "interpretation", "responsible_guidance", "diagnosis",
            ))
            for row in conditions
            if isinstance(row, dict)
        ]
    protection = list(medical_profile.get("protective_factors") or [])[:4]
    if protection:
        result["protective_factors"] = protection
    return {key: item for key, item in result.items() if item not in (None, "", [], {})}
