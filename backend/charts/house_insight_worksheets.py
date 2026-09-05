from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Set

from calculators.ashtakavarga import CLASSICAL_PLANETS, AshtakavargaCalculator
from calculators.chara_karaka_calculator import CharaKarakaCalculator
from calculators.divisional_chart_calculator import DivisionalChartCalculator
from calculators.jaimini_point_calculator import JaiminiPointCalculator
from calculators.sniper_points_calculator import SniperPointsCalculator
from shared.dasha_calculator import DashaCalculator

SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

HOUSE_NATURAL_KARAKAS = {
    1: ["Sun"],
    2: ["Jupiter"],
    3: ["Mars"],
    4: ["Moon"],
    5: ["Jupiter"],
    6: ["Mars", "Saturn"],
    7: ["Venus"],
    8: ["Saturn"],
    9: ["Jupiter", "Sun"],
    10: ["Sun", "Mercury", "Jupiter", "Saturn"],
    11: ["Jupiter"],
    12: ["Saturn"],
}

KARAKA_ABBR = {
    "Atmakaraka": "AK",
    "Amatyakaraka": "AmK",
    "Bhratrukaraka": "BK",
    "Matrukaraka": "MK",
    "Putrakaraka": "PK",
    "Pitrikaraka": "PiK",
    "Gnatikaraka": "GK",
    "Darakaraka": "DK",
}

ARGALA_OFFSETS = ((1, "2nd"), (3, "4th"), (10, "11th"))
VIRODHA_OFFSETS = ((11, "12th"), (9, "10th"), (2, "3rd"))
SKIP_PLANETS = {"Gulika", "Mandi", "InduLagna", "Ascendant"}
SIGN_LORDS = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon",
    4: "Sun", 5: "Mercury", 6: "Venus", 7: "Mars",
    8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter",
}
NAKSHATRA_LORDS = {
    1: "Ketu", 2: "Venus", 3: "Sun", 4: "Moon", 5: "Mars", 6: "Rahu", 7: "Jupiter",
    8: "Saturn", 9: "Mercury", 10: "Ketu", 11: "Venus", 12: "Sun", 13: "Moon",
    14: "Mars", 15: "Rahu", 16: "Jupiter", 17: "Saturn", 18: "Mercury", 19: "Ketu",
    20: "Venus", 21: "Sun", 22: "Moon", 23: "Mars", 24: "Rahu", 25: "Jupiter",
    26: "Saturn", 27: "Mercury",
}
RELATED_CHARTS = {
    2: {"id": "hora", "name": "Hora (D2)", "division": 2},
    4: {"id": "chaturthamsa", "name": "Chaturthamsa (D4)", "division": 4},
    5: {"id": "saptamsa", "name": "Saptamsa (D7)", "division": 7},
    7: {"id": "navamsa", "name": "Navamsa (D9)", "division": 9},
    9: {"id": "vimsamsa", "name": "Vimsamsa (D20)", "division": 20},
    10: {"id": "dashamsa", "name": "Dasamsa (D10)", "division": 10},
    12: {"id": "dwadashamsa", "name": "Dwadashamsa (D12)", "division": 12},
}


def _normalize_chart_data(chart_data: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(chart_data, dict) and isinstance(chart_data.get("divisional_chart"), dict):
        return chart_data["divisional_chart"]
    return chart_data


def _houses_ruled_by_planet(chart_data: Dict[str, Any], planet: str) -> List[int]:
    ruled = []
    for index, house in enumerate(chart_data.get("houses") or [], start=1):
        if house and house.get("sign") is not None:
            if SIGN_LORDS.get(house.get("sign")) == planet:
                ruled.append(index)
    return ruled


def _lagna_sign(chart: Dict[str, Any]) -> int:
    houses = chart.get("houses") or []
    if houses and isinstance(houses[0], dict) and houses[0].get("sign") is not None:
        return int(houses[0]["sign"])
    asc = chart.get("ascendant")
    if isinstance(asc, (int, float)):
        return int((((float(asc) % 360) + 360) % 360) / 30)
    return 0


def _house_from_sign(sign: int, lagna_sign: int) -> int:
    return ((int(sign) - int(lagna_sign) + 12) % 12) + 1


def _planet_row(chart: Dict[str, Any], planet: str) -> Dict[str, Any]:
    data = (chart.get("planets") or {}).get(planet) or {}
    sign = data.get("sign")
    if sign is None and isinstance(data.get("longitude"), (int, float)):
        sign = int((((float(data["longitude"]) % 360) + 360) % 360) / 30)
    house = data.get("house")
    if house is None and sign is not None:
        house = _house_from_sign(int(sign), _lagna_sign(chart))
    return {
        "planet": planet,
        "sign": sign,
        "sign_name": SIGN_NAMES[int(sign)] if isinstance(sign, int) and 0 <= sign < 12 else None,
        "house": house,
        "degree": data.get("degree"),
        "longitude": data.get("longitude"),
        "retrograde": bool(data.get("retrograde")) and planet not in {"Rahu", "Ketu"},
        "nakshatra": data.get("nakshatra") or data.get("nakshatra_name"),
    }


def _planets_in_house(chart: Dict[str, Any], house_num: int) -> List[str]:
    names = []
    for planet, data in (chart.get("planets") or {}).items():
        if planet in SKIP_PLANETS or not isinstance(data, dict):
            continue
        house = data.get("house")
        if house is None and data.get("sign") is not None:
            house = _house_from_sign(int(data["sign"]), _lagna_sign(chart))
        if house == house_num:
            names.append(planet)
    return names


def _bindu_for_sign(bindus: Any, sign: int) -> int:
    if isinstance(bindus, dict):
        value = bindus.get(sign)
        if value is None:
            value = bindus.get(str(sign))
        return int(value or 0)
    if isinstance(bindus, list) and 0 <= sign < len(bindus):
        return int(bindus[sign] or 0)
    return 0


def _parse_dt(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and len(value) >= 10:
        try:
            return datetime.strptime(value[:10], "%Y-%m-%d")
        except ValueError:
            return None
    return None


def _fmt_date(value: Any) -> Optional[str]:
    parsed = _parse_dt(value)
    if parsed:
        return parsed.strftime("%Y-%m-%d")
    if isinstance(value, str) and len(value) >= 10:
        return value[:10]
    return None


def _dasha_role(planet: str, lord: str, occupants: Set[str], aspectors: Set[str]) -> Optional[str]:
    if planet == lord:
        return "House lord"
    if planet in occupants:
        return "Occupant"
    if planet in aspectors:
        return "Aspecting"
    return None


def build_lord_worksheet(
    *,
    lord: str,
    lord_analysis: Dict[str, Any],
    chart_data: Dict[str, Any],
    shadbala_data: Dict[str, Any],
) -> Dict[str, Any]:
    basic = lord_analysis.get("basic_info") or {}
    dignity = lord_analysis.get("dignity_analysis") or {}
    combustion = lord_analysis.get("combustion_status") or {}
    retrograde = lord_analysis.get("retrograde_analysis") or {}
    special = lord_analysis.get("special_lordships") or {}
    longitude = basic.get("longitude")
    nakshatra_num = None
    if isinstance(longitude, (int, float)):
        nakshatra_num = int((((float(longitude) % 360) + 360) % 360) / 13.333333) + 1
        nakshatra_num = min(max(nakshatra_num, 1), 27)
    shadbala = shadbala_data.get(lord) or {}
    return {
        "planet": lord,
        "sign_name": basic.get("sign_name"),
        "house": basic.get("house"),
        "degree": basic.get("degree"),
        "nakshatra": basic.get("nakshatra"),
        "nakshatra_lord": NAKSHATRA_LORDS.get(nakshatra_num) if nakshatra_num else None,
        "dignity": dignity.get("dignity"),
        "functional_nature": dignity.get("functional_nature"),
        "retrograde": bool(retrograde.get("is_retrograde")),
        "combust": bool(combustion.get("is_combust")),
        "cazimi": bool(combustion.get("is_cazimi")),
        "other_lordships": _houses_ruled_by_planet(chart_data, lord),
        "special_roles": special.get("special_roles") or [],
        "shadbala_rupas": shadbala.get("total_rupas"),
        "required_rupas": shadbala.get("minimum_required_rupas"),
        "meets_minimum": shadbala.get("meets_minimum"),
        "classical_status": shadbala.get("classical_status"),
    }


def build_argala(chart_data: Dict[str, Any], house_num: int) -> Dict[str, Any]:
    def collect(offsets: Iterable[tuple], kind: str) -> List[Dict[str, Any]]:
        rows = []
        for offset, label in offsets:
            source_house = ((house_num - 1 + offset) % 12) + 1
            for planet in _planets_in_house(chart_data, source_house):
                rows.append({
                    "planet": planet,
                    "from_house": source_house,
                    "label": label,
                    "kind": kind,
                })
        return rows

    support = collect(ARGALA_OFFSETS, "argala")
    obstruct = collect(VIRODHA_OFFSETS, "virodha")
    net = len(support) - len(obstruct)
    if net > 0:
        grade = "Support"
    elif net < 0:
        grade = "Obstruction"
    else:
        grade = "Neutral"
    return {
        "grade": grade,
        "support": support,
        "obstruction": obstruct,
    }


def build_points_in_house(
    *,
    natal_chart: Dict[str, Any],
    house_num: int,
    yogi_data: Dict[str, Any],
) -> List[Dict[str, Any]]:
    points: List[Dict[str, Any]] = []
    lagna_sign = _lagna_sign(natal_chart)

    def add(key: str, label: str, sign: Any, house: Any = None, detail: str = "") -> None:
        if sign is None:
            return
        sign_id = None
        if isinstance(sign, int):
            sign_id = sign
        elif isinstance(sign, str) and sign in SIGN_NAMES:
            sign_id = SIGN_NAMES.index(sign)
        resolved_house = house
        if resolved_house is None and isinstance(sign_id, int):
            resolved_house = _house_from_sign(sign_id, lagna_sign)
        if resolved_house != house_num:
            return
        points.append({
            "key": key,
            "label": label,
            "sign_name": SIGN_NAMES[sign_id] if isinstance(sign_id, int) and 0 <= sign_id < 12 else sign,
            "house": resolved_house,
            "detail": detail,
        })

    try:
        d9 = _normalize_chart_data(
            DivisionalChartCalculator(natal_chart).calculate_divisional_chart(9)
        )
        ak = (
            (CharaKarakaCalculator(natal_chart).calculate_chara_karakas().get("chara_karakas") or {})
            .get("Atmakaraka", {})
            .get("planet")
        )
        if ak:
            jaimini = JaiminiPointCalculator(natal_chart, d9, ak).calculate_jaimini_points()
            mapping = (
                ("al", "Arudha Lagna", "arudha_lagna"),
                ("ul", "Upapada", "upapada_lagna"),
                ("a7", "Darapada A7", "darapada"),
                ("hl", "Hora Lagna", "hora_lagna"),
                ("gl", "Ghatika Lagna", "ghatika_lagna"),
            )
            for key, label, lookup in mapping:
                point = jaimini.get(lookup) or {}
                add(key, label, point.get("sign_id"), detail=point.get("description") or "")
    except Exception:
        pass

    indu = (natal_chart.get("planets") or {}).get("InduLagna") or {}
    if indu:
        add("indu", "Indu Lagna", indu.get("sign"), indu.get("house"))

    try:
        d3 = _normalize_chart_data(
            DivisionalChartCalculator(natal_chart).calculate_divisional_chart(3)
        )
        d9 = _normalize_chart_data(
            DivisionalChartCalculator(natal_chart).calculate_divisional_chart(9)
        )
        bb = SniperPointsCalculator(natal_chart, d3, d9).calculate_bhrigu_bindu()
        if not bb.get("error") and bb.get("sign") in SIGN_NAMES:
            add(
                "bb",
                "Bhrigu Bindu",
                bb.get("sign"),
                _house_from_sign(SIGN_NAMES.index(bb["sign"]), lagna_sign),
                f"{bb.get('degree')}°" if bb.get("degree") is not None else "",
            )
    except Exception:
        pass

    add("yogi", "Yogi sign", (yogi_data.get("yogi") or {}).get("sign"), detail=(yogi_data.get("yogi") or {}).get("lord") or "")
    add("avayogi", "Avayogi sign", (yogi_data.get("avayogi") or {}).get("sign"), detail=(yogi_data.get("avayogi") or {}).get("lord") or "")
    add("dagdha", "Dagdha rashi", (yogi_data.get("dagdha_rashi") or {}).get("sign"), detail=(yogi_data.get("dagdha_rashi") or {}).get("lord") or "")
    return points


def build_chara_karakas_here(chart_data: Dict[str, Any], natal_chart: Dict[str, Any], house_num: int) -> List[Dict[str, Any]]:
    try:
        payload = CharaKarakaCalculator(natal_chart).calculate_chara_karakas()
    except Exception:
        return []
    rows = []
    for name, info in (payload.get("chara_karakas") or {}).items():
        planet = info.get("planet")
        if not planet:
            continue
        house = _planet_row(chart_data, planet).get("house")
        if house != house_num:
            continue
        rows.append({
            "karaka": name,
            "abbr": KARAKA_ABBR.get(name, name),
            "title": info.get("title") or name,
            "planet": planet,
            "house": house,
        })
    return rows


def build_natural_karakas(chart_data: Dict[str, Any], house_num: int) -> List[Dict[str, Any]]:
    return [_planet_row(chart_data, planet) for planet in HOUSE_NATURAL_KARAKAS.get(house_num, [])]


def build_related_varga(
    natal_chart: Dict[str, Any],
    house_num: int,
    chart_id: str,
) -> Optional[Dict[str, Any]]:
    if chart_id != "lagna":
        return None
    related = RELATED_CHARTS.get(house_num)
    if not related:
        return None
    division = related.get("division")
    if not division:
        return None
    try:
        varga = _normalize_chart_data(
            DivisionalChartCalculator(natal_chart).calculate_divisional_chart(division)
        )
    except Exception:
        return None
    houses = varga.get("houses") or []
    house = houses[house_num - 1] if len(houses) >= house_num else {}
    sign = house.get("sign")
    occupants = _planets_in_house(varga, house_num)
    lord = SIGN_LORDS.get(sign) if isinstance(sign, int) else None
    lord_row = _planet_row(varga, lord) if lord else {}
    return {
        "id": related["id"],
        "name": related["name"],
        "house": house_num,
        "sign_name": SIGN_NAMES[sign] if isinstance(sign, int) and 0 <= sign < 12 else None,
        "lord": lord,
        "lord_house": lord_row.get("house"),
        "lord_sign_name": lord_row.get("sign_name"),
        "occupants": occupants,
    }


def build_sav_givers(
    birth_data: Dict[str, Any],
    chart_data: Dict[str, Any],
    house_sign: int,
) -> Dict[str, Any]:
    ashtakavarga = AshtakavargaCalculator(birth_data, chart_data)
    sav = ashtakavarga.calculate_sarvashtakavarga()
    givers = []
    for planet in CLASSICAL_PLANETS:
        chart = (sav.get("individual_charts") or {}).get(planet) or {}
        bindus = _bindu_for_sign(chart.get("bindus"), house_sign)
        givers.append({"planet": planet, "bindus": bindus})
    lagna_chart = sav.get("lagna_chart") or {}
    lagna_bindus = _bindu_for_sign(lagna_chart.get("bindus"), house_sign)
    if lagna_bindus:
        givers.append({"planet": "Lagna", "bindus": lagna_bindus})
    total = sum(item["bindus"] for item in givers)
    return {
        "house_sign": house_sign,
        "total": total,
        "givers": givers,
    }


def build_timing_windows(
    *,
    birth_data: Dict[str, Any],
    transit_date: Optional[str],
    lord: str,
    occupants: Set[str],
    aspectors: Set[str],
    current_transits: List[str],
    limit: int = 6,
) -> Dict[str, Any]:
    as_of = datetime.strptime(transit_date, "%Y-%m-%d") if transit_date else datetime.now()
    windows: List[Dict[str, Any]] = []
    try:
        dasha_calc = DashaCalculator()
        dashas = dasha_calc.calculate_current_dashas(birth_data, current_date=as_of)
        for maha in dashas.get("maha_dashas") or []:
            maha_end = _parse_dt(maha.get("end"))
            if maha_end and maha_end < as_of:
                continue
            for ad in dasha_calc.list_antardashas(maha, as_of):
                ad_end = _parse_dt(ad.get("end"))
                if ad_end and ad_end < as_of:
                    continue
                md_role = _dasha_role(maha.get("planet"), lord, occupants, aspectors)
                ad_role = _dasha_role(ad.get("planet"), lord, occupants, aspectors)
                if not md_role and not ad_role:
                    continue
                windows.append({
                    "mahadasha": maha.get("planet"),
                    "antardasha": ad.get("planet"),
                    "start": _fmt_date(ad.get("start")),
                    "end": _fmt_date(ad.get("end")),
                    "current": bool(ad.get("current")),
                    "why": ad_role or f"MD {str(md_role).lower()}",
                })
                if len(windows) >= limit:
                    break
            if len(windows) >= limit:
                break
    except Exception:
        pass
    return {
        "windows": windows,
        "current_transits": current_transits,
    }


def build_house_worksheets(
    *,
    birth_data: Dict[str, Any],
    chart_data: Dict[str, Any],
    natal_chart: Dict[str, Any],
    house_num: int,
    house_sign: int,
    chart_id: str,
    lord: str,
    lord_analysis: Dict[str, Any],
    residents: List[Dict[str, Any]],
    aspects_received: List[Dict[str, Any]],
    yogi_data: Dict[str, Any],
    shadbala_data: Dict[str, Any],
    transit_date: Optional[str],
    current_transits: List[str],
) -> Dict[str, Any]:
    occupants = {row.get("planet") for row in residents if row.get("planet")}
    aspectors = {row.get("aspecting_planet") for row in aspects_received if row.get("aspecting_planet")}
    sav: Dict[str, Any] = {}
    try:
        sav_chart = natal_chart if chart_id != "transit" else chart_data
        sav = build_sav_givers(birth_data, sav_chart, house_sign)
    except Exception:
        sav = {}
    return {
        "lord_worksheet": build_lord_worksheet(
            lord=lord,
            lord_analysis=lord_analysis,
            chart_data=chart_data,
            shadbala_data=shadbala_data,
        ),
        "argala": build_argala(chart_data, house_num),
        "points_in_house": build_points_in_house(
            natal_chart=natal_chart,
            house_num=house_num,
            yogi_data=yogi_data,
        ),
        "chara_karakas_here": build_chara_karakas_here(chart_data, natal_chart, house_num),
        "natural_karakas": build_natural_karakas(chart_data, house_num),
        "related_varga": build_related_varga(natal_chart, house_num, chart_id),
        "sav_givers": sav,
        "timing": build_timing_windows(
            birth_data=birth_data,
            transit_date=transit_date,
            lord=lord,
            occupants=occupants,
            aspectors=aspectors,
            current_transits=current_transits,
        ),
    }
