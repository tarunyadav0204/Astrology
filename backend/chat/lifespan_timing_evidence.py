"""Deterministic lifespan timing evidence pack for Standard/Premium LIFESPAN answers.

Cite-only authority for MD/AD/PD dates, Double Transit status, topic divisionals,
afflictions, and confidence ceilings. Instant chat keeps its own short-horizon path.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

_SIGN_NAMES = (
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
)

_TOPIC_SPECS: Dict[str, Dict[str, Any]] = {
    # First job / general career: 6th = service/employment pipeline
    "career": {
        "primary_houses": [10, 6, 2, 11],
        "support_houses": [1],
        "karaka_keys": ["Amatyakaraka"],
        "divisionals": ["D10", "D9"],
        "div_chart_key": "d10_dasamsa",
        "ranking_bias": "first_job",
    },
    # Promotion / raise: status + gains; 6th is support only (not main DT house)
    "career_promotion": {
        "primary_houses": [10, 11, 2],
        "support_houses": [1, 6],
        "karaka_keys": ["Amatyakaraka"],
        "divisionals": ["D10", "D9"],
        "div_chart_key": "d10_dasamsa",
        "ranking_bias": "promotion",
    },
    "marriage": {
        "primary_houses": [7, 2, 11],
        "support_houses": [1],
        "karaka_keys": ["Darakaraka"],
        "divisionals": ["D9", "D7"],
        "div_chart_key": "d9_navamsa",
    },
    "children": {
        "primary_houses": [5, 2, 9, 11],
        "support_houses": [1],
        "karaka_keys": ["Putrakaraka"],
        "divisionals": ["D7", "D9"],
        "div_chart_key": "d7_saptamsa",
    },
    "property": {
        "primary_houses": [4, 11, 12],
        "karaka_keys": [],
        "divisionals": ["D4", "D9"],
        "div_chart_key": "d4_chaturthamsa",
    },
    "education": {
        "primary_houses": [4, 5, 9],
        "karaka_keys": [],
        "divisionals": ["D24", "D9"],
        "div_chart_key": "d24_chaturvimsamsa",
    },
    "health": {
        "primary_houses": [1, 6, 8, 12],
        "karaka_keys": [],
        "divisionals": ["D30", "D9"],
        "div_chart_key": "d30_trimsamsa",
    },
    "wealth": {
        "primary_houses": [2, 11, 9],
        "karaka_keys": [],
        "divisionals": ["D9", "D10"],
        "div_chart_key": "d9_navamsa",
    },
    "general": {
        "primary_houses": [1, 10, 11],
        "karaka_keys": [],
        "divisionals": ["D9"],
        "div_chart_key": "d9_navamsa",
    },
}

_HOUSE_LORDS = {
    0: "Mars",
    1: "Venus",
    2: "Mercury",
    3: "Moon",
    4: "Sun",
    5: "Mercury",
    6: "Venus",
    7: "Mars",
    8: "Jupiter",
    9: "Saturn",
    10: "Saturn",
    11: "Jupiter",
}


def _parse_date(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    s = str(value).strip().replace("T", " ").replace("Z", "")
    if "." in s:
        s = s.split(".")[0]
    s = s[:19]
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            chunk = s[:10] if fmt == "%Y-%m-%d" else s
            return datetime.strptime(chunk, fmt)
        except ValueError:
            continue
    return None


def _date_str(dt: Optional[datetime]) -> str:
    return dt.strftime("%Y-%m-%d") if dt else ""


def topic_spec_for_family(family: str) -> Dict[str, Any]:
    return dict(_TOPIC_SPECS.get(family, _TOPIC_SPECS["general"]))


def topic_spec_for_key(
    topic_key: str = "",
    *,
    family: str = "",
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """Resolve pack parameters; promotion is not the same house stack as first job."""
    key = str(topic_key or "").strip().lower()
    fam = str(family or "").strip().lower()
    cat = str(category or "").strip().lower()
    if (
        key in {"career_promotion", "promotion"}
        or key.endswith("_promotion")
        or cat == "promotion"
        or "promotion" in key
    ):
        return dict(_TOPIC_SPECS["career_promotion"])
    if key in _TOPIC_SPECS:
        return dict(_TOPIC_SPECS[key])
    if fam in _TOPIC_SPECS:
        return dict(_TOPIC_SPECS[fam])
    return topic_spec_for_family(fam or "general")


def is_promotion_topic(
    topic_key: str = "",
    *,
    category: Optional[str] = None,
    question: str = "",
) -> bool:
    key = str(topic_key or "").strip().lower()
    cat = str(category or "").strip().lower()
    q = str(question or "").lower()
    if key in {"career_promotion", "promotion"} or key.endswith("_promotion") or cat == "promotion":
        return True
    if "promotion" in q or "raise" in q or "appraisal" in q:
        # Avoid treating "get a job" style questions as promotion
        if any(t in q for t in ("first job", "get a job", "unemploy", "new job")):
            return False
        return True
    return False


def force_divisional_codes_for_lifespan(
    *,
    mode: Optional[str],
    category: Optional[str],
    question: str = "",
    existing: Optional[Sequence[str]] = None,
) -> List[str]:
    """Ensure topic divisionals even when category falls through as timing/general."""
    mode_u = str(mode or "").upper()
    lifespan = mode_u in {"LIFESPAN_EVENT_TIMING", "PREDICT_EVENT_TIMING"}
    try:
        from ai.prediction_anchor import infer_topic_family
    except Exception:
        infer_topic_family = None  # type: ignore
    family = "general"
    if infer_topic_family:
        # Prefer question cues over weak categories (timing/general).
        weak = str(category or "").strip().lower() in {"", "general", "timing"}
        family = infer_topic_family(
            question,
            category=None if weak else category,
        )
    elif category:
        family = str(category).strip().lower()
        if family in {"job", "promotion", "business"}:
            family = "career"
    if not lifespan and family == "general":
        return list(existing or ["D1", "D9"])
    spec = topic_spec_for_family(family)
    out: List[str] = []
    for code in list(existing or []) + ["D1", "D9"] + list(spec.get("divisionals") or []):
        c = str(code).strip()
        if c and c not in out:
            out.append(c)
    return out


def _asc_sign_id(context: Dict[str, Any]) -> int:
    asc = context.get("ascendant_info") or {}
    if isinstance(asc.get("sign_id"), int):
        return int(asc["sign_id"])
    chart = context.get("d1_chart") or {}
    lon = chart.get("ascendant")
    if lon is None:
        pa = context.get("planetary_analysis") or {}
        # fallback via birth chart in planetary analysis is unavailable; try chart_data
        lon = (context.get("chart_data") or {}).get("ascendant")
    if lon is not None:
        try:
            return int(float(lon) / 30) % 12
        except (TypeError, ValueError):
            pass
    return 0


def _house_lord(asc_sign: int, house: int) -> str:
    sign = (asc_sign + house - 1) % 12
    return _HOUSE_LORDS[sign]


def _planet_house(context: Dict[str, Any], planet: str) -> Optional[int]:
    pa = context.get("planetary_analysis") or {}
    row = pa.get(planet) if isinstance(pa, dict) else None
    if isinstance(row, dict):
        basic = row.get("basic_info") or row
        h = basic.get("house")
        if h is not None:
            try:
                return int(h)
            except (TypeError, ValueError):
                pass
    d1 = context.get("d1_chart") or {}
    planets = d1.get("planets") if isinstance(d1, dict) else {}
    if isinstance(planets, dict) and planet in planets:
        h = planets[planet].get("house")
        if h is not None:
            try:
                return int(h)
            except (TypeError, ValueError):
                pass
    return None


def _planet_sign_id(context: Dict[str, Any], planet: str) -> Optional[int]:
    pa = context.get("planetary_analysis") or {}
    row = pa.get(planet) if isinstance(pa, dict) else None
    if isinstance(row, dict):
        basic = row.get("basic_info") or row
        if basic.get("sign") is not None:
            try:
                return int(basic["sign"])
            except (TypeError, ValueError):
                pass
        name = basic.get("sign_name")
        if name in _SIGN_NAMES:
            return _SIGN_NAMES.index(name)
    return None


def _aspect_houses_from(house: int) -> List[int]:
    """Whole-sign aspects: conjunction + classic graha aspects approximated as house offsets."""
    # Conservative: conjunction, opposition, trines — enough for light DT.
    offsets = {0, 6, 4, 8}  # conj, opp, trines
    return [((house - 1 + o) % 12) + 1 for o in offsets]


def _macro_house_occupancy(
    macro: Dict[str, Any],
    planet: str,
    start: datetime,
    end: datetime,
) -> List[int]:
    rows = macro.get(planet) if isinstance(macro, dict) else None
    if not isinstance(rows, list):
        return []
    houses: List[int] = []
    for seg in rows:
        if not isinstance(seg, dict):
            continue
        s = _parse_date(seg.get("start_date"))
        e = _parse_date(seg.get("end_date"))
        if not s or not e:
            continue
        if e < start or s > end:
            continue
        h = seg.get("house")
        if h is not None:
            try:
                houses.append(int(h))
            except (TypeError, ValueError):
                pass
    return sorted(set(houses))


def _double_transit_status(
    context: Dict[str, Any],
    *,
    primary_houses: Sequence[int],
    asc_sign: int,
    start: datetime,
    end: datetime,
    support_houses: Optional[Sequence[int]] = None,
) -> Dict[str, Any]:
    """Light Ju+Sa DT. Strict: full requires both on the *main* event house (occupy/aspect)."""
    macro = context.get("macro_transits_timeline") or {}
    ju_houses = _macro_house_occupancy(macro, "Jupiter", start, end)
    sa_houses = _macro_house_occupancy(macro, "Saturn", start, end)
    main_house = int(primary_houses[0]) if primary_houses else 1
    support = set(int(h) for h in (support_houses if support_houses is not None else primary_houses[1:])) | {1}

    def _hits(transit_houses: List[int]) -> Dict[str, bool]:
        occ_main = main_house in transit_houses
        asp_main = any(
            th != main_house and main_house in _aspect_houses_from(th) for th in transit_houses
        )
        occ_support = any(h in support for h in transit_houses)
        return {
            "main_occupy": occ_main,
            "main_aspect": asp_main and not occ_main,
            "main": occ_main or asp_main,
            "support": occ_support,
        }

    ju = _hits(ju_houses)
    sa = _hits(sa_houses)

    # full = both on main AND at least one occupies (aspect-only pairs are not High-grade)
    if ju["main"] and sa["main"] and (ju["main_occupy"] or sa["main_occupy"]):
        status = "full"
    # partial = one occupies main, or both aspect main, or main+support combo
    elif ju["main_occupy"] or sa["main_occupy"]:
        status = "partial"
    elif ju["main"] and sa["main"]:
        status = "partial"
    elif (ju["main"] and sa["support"]) or (sa["main"] and ju["support"]):
        status = "partial"
    elif ju["main"] or sa["main"]:
        status = "partial"
    else:
        status = "none"

    return {
        "status": status,
        "main_house": main_house,
        "jupiter_houses": ju_houses,
        "saturn_houses": sa_houses,
        "jupiter_hits": ju,
        "saturn_hits": sa,
        "window_start": _date_str(start),
        "window_end": _date_str(end),
    }


def _compact_divisional(context: Dict[str, Any], family: str, spec: Dict[str, Any]) -> Dict[str, Any]:
    divs = context.get("divisional_charts") or {}
    key = spec.get("div_chart_key")
    chart_wrap = divs.get(key) if key else None
    chart = None
    if isinstance(chart_wrap, dict):
        chart = chart_wrap.get("divisional_chart") or chart_wrap
    planets = (chart or {}).get("planets") if isinstance(chart, dict) else {}
    rows = []
    if isinstance(planets, dict):
        for pname in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"):
            pl = planets.get(pname)
            if not isinstance(pl, dict):
                continue
            rows.append(
                {
                    "planet": pname,
                    "sign": pl.get("sign_name") or pl.get("sign"),
                    "house": pl.get("house"),
                    "dignity": pl.get("dignity"),
                }
            )
    asc_lon = (chart or {}).get("ascendant") if isinstance(chart, dict) else None
    asc_sign = None
    if asc_lon is not None:
        try:
            asc_sign = _SIGN_NAMES[int(float(asc_lon) / 30) % 12]
        except (TypeError, ValueError, IndexError):
            asc_sign = None
    return {
        "family": family,
        "charts_required": list(spec.get("divisionals") or []),
        "primary_chart": key,
        "ascendant_sign": asc_sign,
        "planets": rows[:12],
        "present": bool(rows),
    }


def _afflictions(context: Dict[str, Any], planets: Sequence[str]) -> List[Dict[str, Any]]:
    pa = context.get("planetary_analysis") or {}
    sniper = context.get("sniper_points") or {}
    mb = sniper.get("mrityu_bhaga") if isinstance(sniper, dict) else {}
    mb_planets = set()
    if isinstance(mb, dict):
        for row in mb.get("afflicted_points") or []:
            if isinstance(row, dict) and row.get("planet"):
                mb_planets.add(str(row["planet"]))
    out: List[Dict[str, Any]] = []
    for planet in planets:
        row = pa.get(planet) if isinstance(pa, dict) else None
        if not isinstance(row, dict):
            continue
        basic = row.get("basic_info") or {}
        dig = row.get("dignity_analysis") or {}
        comb = row.get("combustion_status") or {}
        av = basic.get("avastha") or ""
        entry = {
            "planet": planet,
            "house": basic.get("house"),
            "avastha_natal": av,
            "dignity_natal": dig.get("dignity"),
            "combust_natal": bool(comb.get("is_combust")),
            "mrityu_bhaga": planet in mb_planets,
            "tense": "natal",
        }
        if (
            entry["combust_natal"]
            or entry["mrityu_bhaga"]
            or (entry["dignity_natal"] in {"debilitated", "debility"})
            or (isinstance(av, str) and any(x in av for x in ("Mrit", "Bal", "Bala", "Infant")))
        ):
            out.append(entry)
    return out


def _chara_execution(
    context: Dict[str, Any],
    *,
    near_start: datetime,
    near_end: datetime,
    karaka_keys: Sequence[str],
) -> Dict[str, Any]:
    chara = context.get("chara_dasha") or {}
    periods = chara.get("periods") if isinstance(chara, dict) else []
    current_md = None
    current_ad = None
    overlapping = []
    for md in periods or []:
        if not isinstance(md, dict):
            continue
        s = _parse_date(md.get("start_date"))
        e = _parse_date(md.get("end_date"))
        if not s or not e:
            continue
        if md.get("is_current"):
            current_md = {
                "sign": md.get("sign_name"),
                "start": md.get("start_date"),
                "end": md.get("end_date"),
            }
        if e < near_start or s > near_end:
            continue
        ads = []
        for ad in md.get("antardashas") or []:
            if not isinstance(ad, dict):
                continue
            ads_s = _parse_date(ad.get("start_date"))
            ads_e = _parse_date(ad.get("end_date"))
            if not ads_s or not ads_e:
                continue
            if ads_e < near_start or ads_s > near_end:
                continue
            ads.append(
                {
                    "sign": ad.get("sign_name"),
                    "start": ad.get("start_date"),
                    "end": ad.get("end_date"),
                    "is_current": bool(ad.get("is_current")),
                }
            )
            if ad.get("is_current"):
                current_ad = ads[-1]
        overlapping.append(
            {
                "sign": md.get("sign_name"),
                "start": md.get("start_date"),
                "end": md.get("end_date"),
                "antardashas": ads[:6],
            }
        )

    karaka_signs = {}
    ck = context.get("chara_karakas") or {}
    table = ck.get("chara_karakas") if isinstance(ck, dict) else ck
    if isinstance(table, dict):
        for key in karaka_keys:
            row = table.get(key)
            if isinstance(row, dict):
                sid = row.get("sign")
                if sid is not None:
                    try:
                        karaka_signs[key] = _SIGN_NAMES[int(sid) % 12]
                    except (TypeError, ValueError, IndexError):
                        pass
                elif row.get("sign_name"):
                    karaka_signs[key] = row.get("sign_name")

    hit = False
    for key, sign in karaka_signs.items():
        if current_md and current_md.get("sign") == sign:
            hit = True
        if current_ad and current_ad.get("sign") == sign:
            hit = True
        for md in overlapping:
            if md.get("sign") == sign:
                hit = True

    return {
        "current_md": current_md,
        "current_ad": current_ad,
        "near_band_periods": overlapping[:8],
        "karaka_signs": karaka_signs,
        "karaka_sign_hit": hit,
    }


def _varshphal_hooks(context: Dict[str, Any], near_start: datetime, near_end: datetime) -> Dict[str, Any]:
    vp = context.get("varshphal") or {}
    if not isinstance(vp, dict) or not vp:
        return {}
    mudda = []
    for row in vp.get("mudda_dasha") or []:
        if not isinstance(row, dict):
            continue
        s = _parse_date(row.get("start"))
        e = _parse_date(row.get("end"))
        if not s or not e:
            continue
        if e < near_start or s > near_end:
            continue
        mudda.append(
            {
                "planet": row.get("planet"),
                "start": row.get("start"),
                "end": row.get("end"),
                "type": row.get("type"),
            }
        )
    return {
        "year": vp.get("year"),
        "year_lord": vp.get("year_lord"),
        "muntha_house": vp.get("muntha_house"),
        "mudda_in_near_band": mudda[:8],
    }


def _dasha_lords_connect(
    context: Dict[str, Any],
    *,
    md: str,
    ad: str,
    pd: Optional[str],
    primary_houses: Sequence[int],
    asc_sign: int,
    family: str = "general",
    ranking_bias: str = "",
) -> Tuple[bool, List[str], int]:
    """Return (connects, reasons, strength). strength: occupy/rule > karaka > significator."""
    reasons: List[str] = []
    strength = 0
    main_house = int(primary_houses[0]) if primary_houses else 1
    topic_lords = {_house_lord(asc_sign, int(h)) for h in primary_houses}
    main_lord = _house_lord(asc_sign, main_house)
    # Natural karakas used as soft connectors (not enough alone for High).
    if ranking_bias == "promotion":
        natural = {"Sun", "Saturn", "Jupiter", "Mercury"}
    else:
        natural = {
            "marriage": {"Venus", "Jupiter"},
            "children": {"Jupiter"},
            "career": {"Sun", "Mercury", "Saturn", "Jupiter"},
            "property": {"Mars", "Venus", "Moon"},
        }.get(family, set())
    status_houses = {10, 11} if ranking_bias == "promotion" else set()
    service_only_ok = ranking_bias != "promotion"

    # PD refinement scores only the PD lord (MD/AD already counted on the AD pass).
    levels = (("PD", pd),) if pd else (("MD", md), ("AD", ad))

    for level, planet in levels:
        if not planet:
            continue
        h = _planet_house(context, planet)
        if h and int(h) == main_house:
            reasons.append(f"{level} {planet} occupies main house {main_house}")
            strength += 5 if level == "AD" else (4 if level == "MD" else 3)
            continue
        if h and int(h) in set(int(x) for x in primary_houses):
            # Promotion: occupying 6 alone (if ever in primary) is weaker than 10/11
            if ranking_bias == "promotion" and int(h) == 6 and int(h) not in status_houses:
                reasons.append(f"{level} {planet} occupies service house {h} (weak for promotion)")
                strength += 1
            else:
                reasons.append(f"{level} {planet} occupies house {h}")
                strength += 4 if level == "AD" else (3 if level == "MD" else 2)
                if ranking_bias == "promotion" and int(h) in status_houses:
                    strength += 2
            continue
        if planet == main_lord or planet in topic_lords:
            reasons.append(f"{level} {planet} rules a topic house")
            strength += 4 if level == "AD" else (3 if level == "MD" else 2)
            if ranking_bias == "promotion" and planet == main_lord:
                strength += 2
            continue
        # Service-house (6) lord alone is not enough for promotion ranking
        if ranking_bias == "promotion" and not service_only_ok:
            sixth_lord = _house_lord(asc_sign, 6)
            if planet == sixth_lord and planet not in topic_lords and planet != main_lord:
                reasons.append(f"{level} {planet} rules 6th (service — weak alone for promotion)")
                strength += 1
                continue
        if planet in natural and level in {"AD", "MD", "PD"}:
            label = "promotion" if ranking_bias == "promotion" else family
            reasons.append(f"{level} {planet} is a natural karaka for {label}")
            strength += 2 if level != "PD" else 1
            continue
        kp = context.get("kp_analysis") or {}
        psig = kp.get("planet_significators") if isinstance(kp, dict) else None
        if isinstance(psig, dict) and planet in psig:
            sigs = psig.get(planet) or []
            if any(int(x) in set(int(y) for y in primary_houses) for x in sigs if str(x).isdigit() or isinstance(x, int)):
                reasons.append(f"{level} {planet} signifies topic houses {sigs}")
                strength += 1  # weak — not enough alone for AD-first topics
    # Require real occupy/rule/karaka for marriage/children; significator-only is insufficient.
    if family in {"marriage", "children"} and not pd:
        connects = strength >= 2 and any(
            "occupies" in r or "rules" in r or "natural karaka" in r for r in reasons
        )
    elif ranking_bias == "promotion" and not pd:
        # Need a status/gains hook — not service-only
        connects = strength >= 3 and any(
            "main house" in r or "occupies house 10" in r or "occupies house 11" in r or "rules a topic" in r
            or "natural karaka" in r
            for r in reasons
        )
    else:
        connects = strength > 0
    return connects, reasons, strength


def _build_candidate_windows(
    context: Dict[str, Any],
    *,
    family: str,
    primary_houses: Sequence[int],
    asc_sign: int,
    ad_spine: Sequence[Dict[str, Any]],
    pd_near: Sequence[Dict[str, Any]],
    judgment: datetime,
    scan_start: datetime,
    divisional_present: bool,
    chara_hit: bool,
    ranking_bias: str = "",
    support_houses: Optional[Sequence[int]] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Rank AD windows. Marriage/children: AD-level ripe bands; PD only as execution refinement."""
    ad_first = family in {"marriage", "children", "property"}
    future_ads: List[Dict[str, Any]] = []
    past_similar: List[Dict[str, Any]] = []
    dt_support = list(support_houses) if support_houses is not None else list(primary_houses[1:]) + [1]

    for ad in ad_spine:
        s = _parse_date(ad.get("ad_start") or ad.get("start_date"))
        e = _parse_date(ad.get("ad_end") or ad.get("end_date"))
        if not s or not e:
            continue
        # Clip to scan; skip tiny overlaps
        if e < judgment - timedelta(days=1) and e < scan_start:
            pass
        connects, reasons, dasha_strength = _dasha_lords_connect(
            context,
            md=str(ad.get("mahadasha") or ""),
            ad=str(ad.get("antardasha") or ""),
            pd=None,
            primary_houses=primary_houses,
            asc_sign=asc_sign,
            family=family,
            ranking_bias=ranking_bias,
        )
        dt = _double_transit_status(
            context,
            primary_houses=primary_houses,
            asc_sign=asc_sign,
            start=max(s, judgment - timedelta(days=30)),
            end=e,
            support_houses=dt_support,
        )
        # Include AD if dasha connects OR (children/marriage with full DT on main house during AD)
        dt_rescue = ad_first and dt["status"] == "full"
        if not connects and not dt_rescue:
            continue
        if dt_rescue and not connects:
            reasons = list(reasons) + [
                f"Double Transit full on house {dt.get('main_house')} during this AD"
            ]

        best_pd = None
        best_pd_score = -1
        base_reasons = list(reasons)
        for pd in pd_near:
            if pd.get("mahadasha") != ad.get("mahadasha") or pd.get("antardasha") != ad.get("antardasha"):
                continue
            ps = _parse_date(pd.get("start_date"))
            pe = _parse_date(pd.get("end_date"))
            if not ps or not pe:
                continue
            if pe < s or ps > e:
                continue
            pd_connects, pd_reasons, pd_str = _dasha_lords_connect(
                context,
                md=str(pd.get("mahadasha") or ""),
                ad=str(pd.get("antardasha") or ""),
                pd=str(pd.get("pratyantardasha") or ""),
                primary_houses=primary_houses,
                asc_sign=asc_sign,
                family=family,
                ranking_bias=ranking_bias,
            )
            if not pd_connects and pd_str < 3:
                continue
            pd_days = max(1, (pe - ps).days)
            pd_score = pd_str
            pd_planet = str(pd.get("pratyantardasha") or "")
            main_lord = _house_lord(asc_sign, int(primary_houses[0])) if primary_houses else ""
            # Prefer main-house lord / occupant PDs (e.g. 10L Mercury for career)
            if pd_planet == main_lord:
                pd_score += 4
            if primary_houses and _planet_house(context, pd_planet) == int(primary_houses[0]):
                pd_score += 3
            if ranking_bias == "promotion" and _planet_house(context, pd_planet) == 11:
                pd_score += 2  # gains house supports title/comp step-up
            # Prefer multi-week/month execution bands over micro spikes
            if pd_days >= 45:
                pd_score += 4
            elif pd_days >= 21:
                pd_score += 2
            else:
                pd_score -= 4
            if ps <= judgment + timedelta(days=365 * 3) and pe >= judgment - timedelta(days=60):
                pd_score += 2
            # PD-window DT (career especially) — don't only score the whole AD
            pd_dt = _double_transit_status(
                context,
                primary_houses=primary_houses,
                asc_sign=asc_sign,
                start=ps,
                end=pe,
                support_houses=dt_support,
            )
            if pd_dt["status"] == "full":
                pd_score += 4
            elif pd_dt["status"] == "partial":
                pd_score += 2
            if pd_score > best_pd_score:
                best_pd_score = pd_score
                best_pd = {
                    "planet": pd.get("pratyantardasha"),
                    "start": pd.get("start_date"),
                    "end": pd.get("end_date"),
                    "reasons": pd_reasons,
                    "days": pd_days,
                    "dt": pd_dt,
                }

        reasons = list(base_reasons)
        if best_pd:
            reasons = reasons + list(best_pd.get("reasons") or [])

        chain = f"{ad.get('mahadasha')}-{ad.get('antardasha')}"
        ad_start_s = ad.get("ad_start") or ad.get("start_date")
        ad_end_s = ad.get("ad_end") or ad.get("end_date")
        micro_pd = bool(best_pd and int(best_pd.get("days") or 0) < 45)
        # AD-first topics always use AD ripe bands; career micro-PDs also fall back to AD ripe.
        use_ad_ripe = ad_first or micro_pd or not best_pd
        if use_ad_ripe:
            band_start, band_end = ad_start_s, ad_end_s
            execution_start = best_pd["start"] if best_pd else ad_start_s
            execution_end = best_pd["end"] if best_pd else ad_end_s
            chain_display = f"{chain}-{best_pd['planet']}" if best_pd else chain
        else:
            band_start = best_pd["start"]
            band_end = best_pd["end"]
            execution_start, execution_end = band_start, band_end
            chain_display = f"{chain}-{best_pd['planet']}"

        score = dasha_strength
        if best_pd and not ad_first:
            score += 2 + max(0, best_pd_score // 2)
            if micro_pd:
                score -= 3  # do not let 5–14d PD spikes outrank multi-month bands
        elif best_pd and ad_first:
            score += 1  # execution refinement only
        # Prefer PD-window DT when tighter than AD-window DT
        effective_dt = dt
        if best_pd and isinstance(best_pd.get("dt"), dict):
            order = {"none": 0, "partial": 1, "full": 2}
            if order.get(best_pd["dt"].get("status"), 0) > order.get(dt.get("status"), 0):
                effective_dt = best_pd["dt"]
        if effective_dt["status"] == "full":
            score += 5 if ad_first else 3
        elif effective_dt["status"] == "partial":
            score += 2 if ad_first else 1
        if effective_dt.get("jupiter_hits", {}).get("main_occupy") or effective_dt.get("saturn_hits", {}).get(
            "main_occupy"
        ):
            score += 3  # real occupation of main house beats aspect-only
        if divisional_present:
            score += 1
        if chara_hit:
            score += 2
        ad_planet = str(ad.get("antardasha") or "")
        if primary_houses and _planet_house(context, ad_planet) == int(primary_houses[0]):
            score += 4
        # Nearness: strongly prefer adult windows inside judgment → +5y
        if s <= judgment + timedelta(days=365 * 5):
            score += 4
        elif s <= judgment + timedelta(days=365 * 10):
            score += 1
        else:
            score -= 5
        if s > judgment + timedelta(days=365 * 15):
            score -= 4

        # High only with strict full DT + solid dasha (occupy/rule), not significator-only
        solid_dasha = dasha_strength >= 4
        if effective_dt["status"] == "full" and solid_dasha and divisional_present:
            ceiling = "high"
        elif effective_dt["status"] == "full" and solid_dasha:
            ceiling = "medium"
        elif effective_dt["status"] in {"full", "partial"} or solid_dasha:
            ceiling = "medium"
        else:
            ceiling = "low"
        if ceiling == "high" and effective_dt["status"] != "full":
            ceiling = "medium"
        # Use effective DT on the ranked row
        dt = effective_dt

        item = {
            "label": f"{band_start} – {band_end}",
            "start": band_start,
            "end": band_end,
            "execution_start": execution_start,
            "execution_end": execution_end,
            "dasha_chain": chain_display,
            "ad_start": ad_start_s,
            "ad_end": ad_end_s,
            "double_transit": dt["status"],
            "double_transit_detail": dt,
            "why": reasons[:6],
            "score": score,
            "confidence_ceiling": ceiling,
            "same_arc_hint": "same_arc" if s >= judgment - timedelta(days=180) else "alternate_path",
            "ranking_mode": "ad_first" if use_ad_ripe else "pd_execution",
        }
        if e < judgment:
            past_similar.append(item)
        else:
            future_ads.append(item)

    future_ads.sort(key=lambda x: (-int(x.get("score") or 0), x.get("start") or ""))
    ranked = []
    for i, item in enumerate(future_ads[:5]):
        row = dict(item)
        row["rank"] = i + 1
        if i == 0:
            row["same_arc_hint"] = "same_arc"
        elif row.get("same_arc_hint") == "same_arc":
            lead_end = _parse_date(ranked[0].get("ad_end") or ranked[0].get("end"))
            this_start = _parse_date(row.get("start"))
            if lead_end and this_start and this_start > lead_end + timedelta(days=60):
                row["same_arc_hint"] = "alternate_path"
        ranked.append(row)

    past_similar.sort(key=lambda x: (-int(x.get("score") or 0), x.get("start") or ""))
    past_note = {
        "summary": (
            f"{len(past_similar)} earlier adult AD window(s) connected to topic significators "
            "but ranked weaker on Double Transit / near-band refinement."
            if past_similar
            else "No stronger past AD windows with the same topic significators were flagged in the scan."
        ),
        "examples": [
            {
                "label": p.get("label"),
                "dasha_chain": p.get("dasha_chain"),
                "double_transit": p.get("double_transit"),
                "score": p.get("score"),
            }
            for p in past_similar[:3]
        ],
    }
    return ranked, past_note


def build_lifespan_timing_evidence(
    context: Dict[str, Any],
    *,
    birth_data: Optional[Dict[str, Any]] = None,
    user_question: str = "",
    intent_result: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Build cite-only lifespan timing pack. Returns None when not a lifespan request."""
    intent = intent_result or context.get("intent") or {}
    timing_focus = context.get("timing_focus") or {}
    mode = str(intent.get("mode") or timing_focus.get("mode") or "").upper()
    open_ended = bool(timing_focus.get("open_ended_lifespan"))
    if mode not in {"LIFESPAN_EVENT_TIMING", "PREDICT_EVENT_TIMING"} and not open_ended:
        # Also allow when scan window is long
        scan_s = timing_focus.get("scan_start_year")
        scan_e = timing_focus.get("scan_end_year")
        if not (scan_s and scan_e and int(scan_e) - int(scan_s) >= 10):
            return None

    try:
        from ai.prediction_anchor import infer_topic_family, infer_topic_key
    except Exception:
        infer_topic_family = lambda q, category=None, faq_category=None: "general"  # type: ignore
        infer_topic_key = lambda q, category=None, faq_category=None: "general"  # type: ignore

    category = intent.get("category")
    family = infer_topic_family(user_question, category=category)
    topic_key = infer_topic_key(user_question, category=category)
    if is_promotion_topic(topic_key, category=category, question=user_question):
        topic_key = "career_promotion"
        family = "career"
    spec = topic_spec_for_key(topic_key, family=family, category=category)
    primary_houses = list(spec["primary_houses"])
    support_houses = list(spec.get("support_houses") or [1])
    ranking_bias = str(spec.get("ranking_bias") or "")
    asc_sign = _asc_sign_id(context)

    judgment = timing_focus.get("focus_date")
    if not isinstance(judgment, datetime):
        jy = timing_focus.get("judgment_year") or datetime.now().year
        judgment = datetime(int(jy), 7, 1)
    scan_start_y = timing_focus.get("scan_start_year")
    scan_end_y = timing_focus.get("scan_end_year")
    if not scan_start_y or not scan_end_y:
        tr = intent.get("transit_request") or {}
        scan_start_y = tr.get("startYear") or tr.get("start_year") or judgment.year - 1
        scan_end_y = tr.get("endYear") or tr.get("end_year") or judgment.year + 25
    scan_start = datetime(int(scan_start_y), 1, 1)
    scan_end = datetime(int(scan_end_y), 12, 31)
    near_start = datetime(max(scan_start.year, judgment.year - 1), 1, 1)
    near_end = datetime(min(scan_end.year, judgment.year + 3), 12, 31)

    rds = context.get("requested_dasha_summary") or {}
    ad_spine = list(rds.get("ad_spine") or [])
    pd_near = list((rds.get("pd_near_band") or {}).get("periods") or [])
    if (not ad_spine or not pd_near) and birth_data:
        try:
            from shared.dasha_calculator import DashaCalculator

            calc = DashaCalculator()
            if not ad_spine:
                ad_spine = calc.iter_ad_periods(birth_data, scan_start, scan_end)
            if not pd_near:
                pd_near = calc.iter_pd_periods(birth_data, near_start, near_end)
        except Exception:
            logger.exception("lifespan_timing_evidence_dasha_spine_failed")

    current = context.get("current_dashas") or {}
    current_stack = {
        "mahadasha": (current.get("mahadasha") or {}).get("planet"),
        "antardasha": (current.get("antardasha") or {}).get("planet"),
        "pratyantardasha": (current.get("pratyantardasha") or {}).get("planet"),
        "md_start": (current.get("mahadasha") or {}).get("start"),
        "md_end": (current.get("mahadasha") or {}).get("end"),
        "ad_start": (current.get("antardasha") or {}).get("start"),
        "ad_end": (current.get("antardasha") or {}).get("end"),
    }

    divisional_topic = _compact_divisional(context, family, spec)
    chara_execution = _chara_execution(
        context,
        near_start=near_start,
        near_end=near_end,
        karaka_keys=spec.get("karaka_keys") or [],
    )

    dasha_planets = [
        p
        for p in (
            current_stack.get("mahadasha"),
            current_stack.get("antardasha"),
            current_stack.get("pratyantardasha"),
        )
        if p
    ]
    topic_lords = [_house_lord(asc_sign, h) for h in primary_houses]
    afflict_planets = list(dict.fromkeys(topic_lords + dasha_planets))
    afflictions = _afflictions(context, afflict_planets)

    candidates, past_note = _build_candidate_windows(
        context,
        family=family,
        primary_houses=primary_houses,
        asc_sign=asc_sign,
        ad_spine=ad_spine,
        pd_near=pd_near,
        judgment=judgment,
        scan_start=scan_start,
        divisional_present=bool(divisional_topic.get("present")),
        chara_hit=bool(chara_execution.get("karaka_sign_hit")),
        ranking_bias=ranking_bias,
        support_houses=support_houses,
    )

    overall_ceiling = "medium"
    if candidates:
        overall_ceiling = candidates[0].get("confidence_ceiling") or "medium"
    # Global: High forbidden if top window DT is none
    if candidates and candidates[0].get("double_transit") == "none" and overall_ceiling == "high":
        overall_ceiling = "medium"
        candidates[0]["confidence_ceiling"] = "medium"

    near_dt = _double_transit_status(
        context,
        primary_houses=primary_houses,
        asc_sign=asc_sign,
        start=near_start,
        end=near_end,
        support_houses=support_houses,
    )

    top_dt_status = str((candidates[0].get("double_transit") if candidates else near_dt.get("status")) or "none")
    main_h = int(primary_houses[0]) if primary_houses else 10
    dt_cite = _double_transit_cite_instruction(top_dt_status, main_house=main_h)
    cite_rules = [
        "Cite MD/AD/PD planet names and date ranges ONLY from dasha_spine (ad_spine / pd_near / current).",
        "Do not invent pratyantardasha stacks outside pd_near.",
        "Prefer candidate_windows order for Window 1..N. Soft override allowed when Double Transit "
        "full on the main house clearly favors a later AD in ad_spine — then rank that AD Window 1 "
        "and keep the pack's prior #1 as Same arc / Alternate path. Do not invent dates outside the spine.",
        "For marriage/children/property, Ripe Window = AD dates; PD is Execution only (not Window label).",
        f"Confidence must not exceed confidence_ceiling ({overall_ceiling}). Never say Extremely High. "
        "High requires full Double Transit on the main event house plus solid dasha occupy/rule.",
        dt_cite,
        "For career/marriage/children/property, mention divisional_topic when present.",
        "Natal avastha/combust/Mrityu Bhaga from afflictions are natal facts — not 'currently' sky conditions.",
        "Do not claim degree-exact Jupiter over a natal planet unless longitude evidence is in the pack.",
        "Use Ripe Window (not Promise Window). Keep Technical Deep Dive slim — no Kota/full school dump.",
    ]
    if ranking_bias == "promotion" or is_promotion_topic(topic_key, category=category, question=user_question):
        cite_rules.append(
            "PROMOTION (not first job): use Visibility → Formalization → Settle. "
            "Do NOT use Activation/Offer/Joining. Emphasize 10th/11th status+gains and D10; "
            "6th is service support only, not the main event house."
        )
    elif family == "career":
        cite_rules.append(
            "Career/job: separate Activation / Offer / Joining; PD start ≠ offer/joining SLA."
        )

    return {
        "topic": {
            "family": family,
            "topic_key": topic_key,
            "primary_houses": primary_houses,
            "support_houses": support_houses,
            "ranking_bias": ranking_bias,
            "karaka_keys": list(spec.get("karaka_keys") or []),
            "divisionals_required": list(spec.get("divisionals") or []),
        },
        "timing_focus": {
            "judgment_year": judgment.year,
            "scan_start_year": int(scan_start_y),
            "scan_end_year": int(scan_end_y),
            "near_band_start": _date_str(near_start),
            "near_band_end": _date_str(near_end),
            "open_ended_lifespan": open_ended or mode == "LIFESPAN_EVENT_TIMING",
        },
        "dasha_spine": {
            "current": current_stack,
            "ad_spine": ad_spine[:80],
            "pd_near": pd_near[:80],
            "period_coverage_actual": rds.get("period_coverage_actual"),
            "truncated": bool(rds.get("truncated")),
        },
        "double_transit": {
            "near_band": near_dt,
            "top_window": (candidates[0].get("double_transit_detail") if candidates else near_dt),
            "claim_allowed": top_dt_status,  # full | partial | none — only authority for DT wording
            "cite_line": dt_cite,
        },
        "divisional_topic": divisional_topic,
        "afflictions": afflictions,
        "chara_execution": chara_execution,
        "varshphal_hooks": _varshphal_hooks(context, near_start, near_end),
        "candidate_windows": candidates,
        "past_scan_note": past_note,
        "confidence_ceiling": overall_ceiling,
        "cite_rules": cite_rules,
    }


def compact_lifespan_timing_evidence_for_prompt(pack: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Smaller JSON for merge_user injection."""
    if not isinstance(pack, dict) or not pack:
        return None
    cands = []
    for c in (pack.get("candidate_windows") or [])[:5]:
        cands.append(
            {
                "rank": c.get("rank"),
                "label": c.get("label"),
                "start": c.get("start"),
                "end": c.get("end"),
                "execution_start": c.get("execution_start"),
                "execution_end": c.get("execution_end"),
                "dasha_chain": c.get("dasha_chain"),
                "double_transit": c.get("double_transit"),
                "confidence_ceiling": c.get("confidence_ceiling"),
                "same_arc_hint": c.get("same_arc_hint"),
                "ranking_mode": c.get("ranking_mode"),
                "why": (c.get("why") or [])[:4],
            }
        )
    dt = pack.get("double_transit") or {}
    return {
        "topic": pack.get("topic"),
        "timing_focus": pack.get("timing_focus"),
        "dasha_spine": {
            "current": (pack.get("dasha_spine") or {}).get("current"),
            "pd_near": ((pack.get("dasha_spine") or {}).get("pd_near") or [])[:40],
            "ad_spine_sample": ((pack.get("dasha_spine") or {}).get("ad_spine") or [])[:24],
            "period_coverage_actual": (pack.get("dasha_spine") or {}).get("period_coverage_actual"),
        },
        "double_transit": {
            "near_band_status": (dt.get("near_band") or {}).get("status"),
            "top_window_status": (dt.get("top_window") or {}).get("status")
            if isinstance(dt.get("top_window"), dict)
            else dt.get("top_window"),
            "claim_allowed": dt.get("claim_allowed")
            or (
                (dt.get("top_window") or {}).get("status")
                if isinstance(dt.get("top_window"), dict)
                else None
            )
            or (dt.get("near_band") or {}).get("status"),
            "cite_line": dt.get("cite_line"),
            "main_house": (dt.get("top_window") or {}).get("main_house")
            if isinstance(dt.get("top_window"), dict)
            else (dt.get("near_band") or {}).get("main_house"),
            "jupiter_houses": (dt.get("top_window") or {}).get("jupiter_houses")
            if isinstance(dt.get("top_window"), dict)
            else (dt.get("near_band") or {}).get("jupiter_houses"),
            "saturn_houses": (dt.get("top_window") or {}).get("saturn_houses")
            if isinstance(dt.get("top_window"), dict)
            else (dt.get("near_band") or {}).get("saturn_houses"),
        },
        "divisional_topic": {
            "primary_chart": (pack.get("divisional_topic") or {}).get("primary_chart"),
            "ascendant_sign": (pack.get("divisional_topic") or {}).get("ascendant_sign"),
            "present": (pack.get("divisional_topic") or {}).get("present"),
            "planets": ((pack.get("divisional_topic") or {}).get("planets") or [])[:9],
        },
        "afflictions": (pack.get("afflictions") or [])[:8],
        "chara_execution": {
            "current_md": (pack.get("chara_execution") or {}).get("current_md"),
            "current_ad": (pack.get("chara_execution") or {}).get("current_ad"),
            "karaka_signs": (pack.get("chara_execution") or {}).get("karaka_signs"),
            "karaka_sign_hit": (pack.get("chara_execution") or {}).get("karaka_sign_hit"),
        },
        "varshphal_hooks": pack.get("varshphal_hooks"),
        "candidate_windows": cands,
        "past_scan_note": pack.get("past_scan_note"),
        "confidence_ceiling": pack.get("confidence_ceiling"),
        "cite_rules": pack.get("cite_rules"),
    }


def _double_transit_cite_instruction(status: str, *, main_house: int) -> str:
    """Prompt-only DT wording rules (language-agnostic machine status → model instruction)."""
    st = str(status or "none").lower()
    if st == "full":
        return (
            f"Double Transit status for Window 1 is FULL on house {main_house}. "
            "You may say full Double Transit only if both Jupiter and Saturn hit that same main house "
            "(at least one by occupation). Do not relocate Saturn/Jupiter to other houses. "
            "Phrase this in the user's language."
        )
    if st == "partial":
        return (
            f"Double Transit status for Window 1 is PARTIAL on house {main_house}. "
            "Describe partial transit confirmation only — never claim full/activated Double Transit. "
            "Jupiter on the main house while Saturn is only in a non-main house (e.g. 9th) is NOT Double Transit. "
            "Phrase this in the user's language."
        )
    return (
        f"Double Transit status for Window 1 is NONE on house {main_house}. "
        "Do not claim Double Transit / Ju+Sa joint activation of the event. "
        "You may mention individual Jupiter or Saturn transits factually. "
        "Phrase this in the user's language."
    )