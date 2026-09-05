from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from calculators.badhaka_calculator import BadhakaCalculator
from calculators.chara_karaka_calculator import CharaKarakaCalculator
from calculators.divisional_chart_calculator import DivisionalChartCalculator
from calculators.gandanta_calculator import GandantaCalculator
from calculators.house_analyzer import HouseAnalyzer
from calculators.jaimini_point_calculator import JaiminiPointCalculator
from calculators.mudakku_calculator import MudakkuCalculator
from calculators.planetary_dignities_calculator import PlanetaryDignitiesCalculator
from calculators.pushkara_calculator import PushkaraCalculator
from calculators.sniper_points_calculator import SniperPointsCalculator
from calculators.transit_calculator import TransitCalculator
from calculators.yoga_calculator import YogaCalculator
from calculators.yogi_calculator import YogiCalculator
from charts.house_insight_service import (
    SIGN_LORDS,
    _birth_obj,
    _chart_display_name,
    _collect_house_factors,
    _houses_ruled_by_planet,
    _natal_chart_for_shadbala,
    _normalize_chart_data,
    _normalize_transit_chart_data,
    _preview_resident_names,
)
from shared.dasha_calculator import DashaCalculator

SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SKIP_PLANETS = {"Gulika", "Mandi", "InduLagna", "Ascendant"}


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


def _sign_name(sign: Any) -> Optional[str]:
    if isinstance(sign, int) and 0 <= sign < 12:
        return SIGN_NAMES[sign]
    if isinstance(sign, str) and sign in SIGN_NAMES:
        return sign
    return None


def _fmt_point(point: Optional[Dict[str, Any]]) -> str:
    if not isinstance(point, dict):
        return ""
    sign = _sign_name(point.get("sign") if point.get("sign") is not None else point.get("sign_name"))
    degree = point.get("degree")
    parts = [sign or ""]
    if degree is not None:
        try:
            parts.append(f"{float(degree):.1f}°")
        except (TypeError, ValueError):
            pass
    return " ".join(part for part in parts if part).strip()


def _house_tone(verdict: Dict[str, Any], timing: Dict[str, Any]) -> str:
    label = str((verdict or {}).get("label") or "")
    key = str((verdict or {}).get("key") or "")
    if key == "strong":
        return "support"
    if label == "Under stress" or (key == "mixed" and "stress" in label.lower() and "support" not in label.lower()):
        return "pressure"
    if key == "mixed":
        return "mixed"
    if (timing or {}).get("key") == "active":
        return "active"
    return "quiet"


def _safe_call(fn, fallback=None):
    try:
        return fn()
    except Exception:
        return fallback


def _planet_house(chart: Dict[str, Any], planet: str) -> Optional[int]:
    data = (chart.get("planets") or {}).get(planet) or {}
    house = data.get("house")
    if house is not None:
        return int(house)
    sign = data.get("sign")
    if sign is None:
        return None
    return _house_from_sign(int(sign), _lagna_sign(chart))


def _build_pillar(
    *,
    role: str,
    planet: str,
    chart: Dict[str, Any],
    dignities: Dict[str, Any],
    shadbala: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    data = (chart.get("planets") or {}).get(planet)
    if not isinstance(data, dict):
        return None
    sign = data.get("sign")
    dignity = (dignities.get(planet) or {}).get("dignity")
    strength = shadbala.get(planet) or {}
    return {
        "role": role,
        "planet": planet,
        "sign": sign,
        "sign_name": _sign_name(sign),
        "house": _planet_house(chart, planet),
        "degree": data.get("degree"),
        "dignity": dignity,
        "retrograde": bool(data.get("retrograde")) and planet not in {"Rahu", "Ketu"},
        "combust": (dignities.get(planet) or {}).get("combustion_status") == "combust",
        "shadbala_rupas": strength.get("total_rupas"),
        "required_rupas": strength.get("minimum_required_rupas"),
        "meets_minimum": strength.get("meets_minimum"),
    }


def _special_chip(key: str, label: str, value: str, tone: str, house: Optional[int] = None, title: str = "") -> Dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "value": value,
        "tone": tone,
        "house": house,
        "title": title or f"{label}: {value}",
    }


def _collect_special_marks(
    *,
    birth_data: Dict[str, Any],
    natal: Dict[str, Any],
    dignities: Dict[str, Any],
) -> List[Dict[str, Any]]:
    lagna = _lagna_sign(natal)
    chips: List[Dict[str, Any]] = []

    yogi = _safe_call(lambda: YogiCalculator(natal).calculate_yogi_points(birth_data), {}) or {}
    for key, label, tone in (
        ("yogi", "Yogi", "yogi"),
        ("avayogi", "Avayogi", "ava"),
        ("dagdha_rashi", "Dagdha", "dagdha"),
        ("tithi_shunya_rashi", "Tithi Śūnya", "shunya"),
    ):
        point = yogi.get(key) or {}
        sign = point.get("sign")
        if sign is None:
            continue
        chips.append(_special_chip(
            key,
            label,
            _fmt_point(point) or _sign_name(sign) or "—",
            tone,
            _house_from_sign(int(sign), lagna) if isinstance(sign, int) else None,
            f"{label} lord {point.get('lord') or '—'}",
        ))

    gandanta = _safe_call(lambda: GandantaCalculator(natal).calculate_gandanta_analysis(), {}) or {}
    lagna_gan = gandanta.get("lagna_gandanta") or {}
    if lagna_gan.get("is_gandanta"):
        info = lagna_gan.get("gandanta_info") or lagna_gan
        chips.append(_special_chip(
            "gandanta-lagna",
            "Gandanta",
            f"Lagna · {info.get('gandanta_name') or 'junction'}",
            "gandanta",
            1,
            info.get("intensity") or "",
        ))
    for row in gandanta.get("planets_in_gandanta") or []:
        planet = row.get("planet")
        info = row.get("gandanta_info") or {}
        if not planet or planet in SKIP_PLANETS or not info.get("is_gandanta"):
            continue
        chips.append(_special_chip(
            f"gandanta-{planet}",
            "Gandanta",
            f"{planet} · {info.get('gandanta_name') or 'junction'}",
            "gandanta",
            _planet_house(natal, planet),
            info.get("intensity") or "",
        ))

    mt_planets = []
    for planet, info in dignities.items():
        if (info or {}).get("dignity") != "moolatrikona":
            continue
        mt_planets.append(planet)
        chips.append(_special_chip(
            f"mt-{planet}",
            "Mūlatrikona",
            f"{planet} · {_sign_name((natal.get('planets') or {}).get(planet, {}).get('sign')) or '—'}",
            "moola",
            _planet_house(natal, planet),
            f"{planet} in mūlatrikona",
        ))

    badhaka = BadhakaCalculator(natal)
    badhaka_house = _safe_call(lambda: badhaka.get_badhaka_house(lagna))
    badhaka_lord = _safe_call(lambda: badhaka.get_badhaka_lord(lagna))
    if badhaka_house and badhaka_lord:
        chips.append(_special_chip(
            "badhaka",
            "Badhaka",
            f"H{badhaka_house} {badhaka_lord}",
            "badhaka",
            int(badhaka_house),
        ))
    maraka = _safe_call(lambda: badhaka.get_maraka_lords(lagna), []) or []
    maraka_names = []
    for row in maraka:
        planet = row.get("planet")
        if row.get("type") != "primary" or not planet or planet in maraka_names:
            continue
        maraka_names.append(planet)
    if maraka_names:
        chips.append(_special_chip(
            "maraka",
            "Maraka",
            " · ".join(maraka_names),
            "maraka",
            2,
        ))

    try:
        d9 = _normalize_chart_data(DivisionalChartCalculator(natal).calculate_divisional_chart(9))
        d3 = _normalize_chart_data(DivisionalChartCalculator(natal).calculate_divisional_chart(3))
        ak = (
            (CharaKarakaCalculator(natal).calculate_chara_karakas().get("chara_karakas") or {})
            .get("Atmakaraka", {})
            .get("planet")
        )
        if ak:
            jaimini = JaiminiPointCalculator(natal, d9, ak).calculate_jaimini_points()
            for key, label, tone in (
                ("arudha_lagna", "AL", "point"),
                ("hora_lagna", "HL", "point"),
                ("upapada_lagna", "UL", "point"),
                ("ghatika_lagna", "GL", "point"),
            ):
                point = jaimini.get(key) or {}
                sign_id = point.get("sign_id")
                if sign_id is None:
                    continue
                chips.append(_special_chip(
                    key,
                    label,
                    point.get("sign_name") or _sign_name(sign_id) or "—",
                    tone,
                    _house_from_sign(int(sign_id), lagna),
                    point.get("description") or label,
                ))
        sniper = SniperPointsCalculator(natal, d3, d9)
        bb = _safe_call(sniper.calculate_bhrigu_bindu, {}) or {}
        if bb and not bb.get("error") and bb.get("sign") in SIGN_NAMES:
            chips.append(_special_chip(
                "bhrigu",
                "Bhrigu",
                _fmt_point({"sign_name": bb.get("sign"), "degree": bb.get("degree")}),
                "bb",
                _house_from_sign(SIGN_NAMES.index(bb["sign"]), lagna),
            ))
        mb = _safe_call(sniper.calculate_mrityu_bhaga, {}) or {}
        afflicted = [
            row.get("planet") or row.get("point")
            for row in (mb.get("afflicted_points") or [])
            if row.get("planet") or row.get("point")
        ]
        if afflicted:
            chips.append(_special_chip(
                "mrityu",
                "Mṛtyu",
                " · ".join(str(name) for name in afflicted[:4]),
                "mb",
            ))
        push = PushkaraCalculator().analyze_chart(natal, lagna)
        push_names = [
            row.get("planet")
            for row in (push.get("pushkara_planets") or [])
            if row.get("planet")
        ]
        if push_names:
            chips.append(_special_chip(
                "pushkara",
                "Pushkara",
                " · ".join(push_names[:4]),
                "push",
                _planet_house(natal, push_names[0]),
            ))
    except Exception:
        pass

    mudakku = _safe_call(lambda: MudakkuCalculator(natal).calculate(), {}) or {}
    mud_nak = (mudakku.get("mudakku_nakshatra") or {}).get("name")
    if mud_nak:
        mud_sign = (mudakku.get("mudakku_point") or {}).get("sign")
        chips.append(_special_chip(
            "mudakku",
            "Mudakku",
            " · ".join(part for part in [mud_nak, mudakku.get("mudakku_rashi")] if part),
            "mudakku",
            _house_from_sign(int(mud_sign), lagna) if isinstance(mud_sign, int) else None,
        ))

    doshas = _safe_call(
        lambda: YogaCalculator(_birth_obj(birth_data), natal).calculate_major_doshas(),
        {},
    ) or {}
    for key, label in (
        ("mangal_dosha", "Mangal Dosha"),
        ("kaal_sarp_dosha", "Kaal Sarp Dosha"),
        ("pitra_dosha", "Pitra Dosha"),
    ):
        info = doshas.get(key) or {}
        if info.get("present"):
            chips.append(_special_chip(
                key,
                "Dosha",
                label,
                "dagdha",
                title=str(info.get("type") or info.get("description") or label),
            ))

    return chips


def _now_block(
    *,
    birth_data: Dict[str, Any],
    natal: Dict[str, Any],
    transit_date: Optional[str],
) -> Dict[str, Any]:
    current_date = None
    if transit_date:
        try:
            current_date = datetime.strptime(transit_date[:10], "%Y-%m-%d")
        except ValueError:
            current_date = None
    dashas = _safe_call(
        lambda: DashaCalculator().calculate_current_dashas(birth_data, current_date=current_date),
        {},
    ) or {}
    md = (dashas.get("mahadasha") or {}).get("planet")
    ad = (dashas.get("antardasha") or {}).get("planet")
    pd = (dashas.get("pratyantardasha") or {}).get("planet")
    houses: List[int] = []
    for planet in (md, ad):
        if not planet:
            continue
        houses.extend(_houses_ruled_by_planet(natal, planet))
        occupied = _planet_house(natal, planet)
        if occupied:
            houses.append(occupied)
    unique_houses = sorted({house for house in houses if house})

    transits: List[Dict[str, Any]] = []
    try:
        transit_raw = TransitCalculator({}).calculate_transits(
            _birth_obj(birth_data),
            transit_date or datetime.now().strftime("%Y-%m-%d"),
        )
        transit_chart = _normalize_transit_chart_data(transit_raw)
        for planet, data in (transit_chart.get("planets") or {}).items():
            if planet in SKIP_PLANETS or not isinstance(data, dict):
                continue
            transits.append({
                "planet": planet,
                "house": data.get("house"),
                "sign_name": data.get("sign_name") or _sign_name(data.get("sign")),
            })
        transits = [row for row in transits if row.get("house") in unique_houses][:8] or transits[:6]
    except Exception:
        transits = []

    return {
        "mahadasha": md,
        "antardasha": ad,
        "pratyantardasha": pd,
        "mahadasha_start": (dashas.get("mahadasha") or {}).get("start"),
        "mahadasha_end": (dashas.get("mahadasha") or {}).get("end"),
        "antardasha_start": (dashas.get("antardasha") or {}).get("start"),
        "antardasha_end": (dashas.get("antardasha") or {}).get("end"),
        "houses": unique_houses,
        "transits": transits,
    }


def _overview_summary(houses: List[Dict[str, Any]], now: Dict[str, Any]) -> str:
    support = sum(1 for row in houses if row.get("tone") == "support")
    pressure = sum(1 for row in houses if row.get("tone") == "pressure")
    mixed = sum(1 for row in houses if row.get("tone") == "mixed")
    md = now.get("mahadasha") or "the current mahadasha"
    ad = now.get("antardasha")
    timing = f"{md}/{ad}" if ad else str(md)
    if support >= pressure + 2:
        shape = "The kundli is carrying more support than pressure."
    elif pressure >= support + 2:
        shape = "Pressure is more visible than clean support in this kundli."
    elif mixed:
        shape = "Support and pressure sit together in several houses."
    else:
        shape = "The chart is not loudly marked in either direction."
    lit = now.get("houses") or []
    if lit:
        live = ", ".join(f"H{n}" for n in lit[:4])
        return f"{shape} {timing} is lighting {live}."
    return f"{shape} {timing} is running, without a heavy house pile-up."


def build_chart_overview(
    birth_data: Dict[str, Any],
    chart_id: str = "lagna",
    transit_date: Optional[str] = None,
) -> Dict[str, Any]:
    birth_obj = _birth_obj(birth_data)
    natal = _natal_chart_for_shadbala(birth_obj)
    analyzer = HouseAnalyzer(natal, birth_obj, shadbala_chart_data=natal)
    dignities = PlanetaryDignitiesCalculator(natal).calculate_planetary_dignities()
    shadbala = getattr(analyzer.planet_analyzer, "shadbala_data", {}) or {}
    chara = _safe_call(lambda: CharaKarakaCalculator(natal).calculate_chara_karakas(), {}) or {}
    ak_planet = (chara.get("chara_karakas") or {}).get("Atmakaraka", {}).get("planet")
    lagna = _lagna_sign(natal)
    lagna_lord = SIGN_LORDS.get(lagna)

    houses: List[Dict[str, Any]] = []
    for house_num in range(1, 13):
        insight = _collect_house_factors(
            birth_data=birth_data,
            chart_data=natal,
            house_num=house_num,
            chart_id="lagna",
            transit_date=transit_date,
            shadbala_chart_data=natal,
            analyzer=analyzer,
            include_worksheets=False,
        )
        verdict = insight.get("verdict") or {}
        timing = insight.get("timing_verdict") or {}
        houses.append({
            "house": house_num,
            "sign_name": insight.get("sign_name"),
            "lord": insight.get("house_lord"),
            "verdict": verdict,
            "timing": timing,
            "tone": _house_tone(verdict, timing),
            "active": timing.get("key") == "active",
            "occupants": _preview_resident_names(natal, house_num)[:4],
            "marks": [],
        })

    special = _collect_special_marks(birth_data=birth_data, natal=natal, dignities=dignities)
    marks_by_house: Dict[int, List[str]] = {n: [] for n in range(1, 13)}
    for chip in special:
        house = chip.get("house")
        if house in marks_by_house and chip.get("label"):
            short = {
                "Gandanta": "Gan",
                "Mūlatrikona": "MT",
                "Yogi": "Yogi",
                "Avayogi": "Ava",
                "Dagdha": "Dag",
                "Tithi Śūnya": "Śūnya",
                "Badhaka": "Badh",
                "Maraka": "Mar",
                "AL": "AL",
                "HL": "HL",
                "UL": "UL",
                "GL": "GL",
                "Mudakku": "Mud",
                "Bhrigu": "BB",
                "Pushkara": "Push",
                "Mṛtyu": "MB",
                "Dosha": "Dosha",
            }.get(chip["label"])
            if short and short not in marks_by_house[house]:
                marks_by_house[house].append(short)
    for row in houses:
        row["marks"] = marks_by_house.get(row["house"]) or []

    now = _now_block(birth_data=birth_data, natal=natal, transit_date=transit_date)
    pillars = [
        item for item in (
            _build_pillar(role="Lagna lord", planet=lagna_lord, chart=natal, dignities=dignities, shadbala=shadbala)
            if lagna_lord else None,
            _build_pillar(role="Moon", planet="Moon", chart=natal, dignities=dignities, shadbala=shadbala),
            _build_pillar(role="Atmakaraka", planet=ak_planet, chart=natal, dignities=dignities, shadbala=shadbala)
            if ak_planet else None,
        ) if item
    ]

    return {
        "chart_id": "lagna",
        "chart_name": _chart_display_name(chart_id or "lagna"),
        "lagna_sign": _sign_name(lagna),
        "summary": _overview_summary(houses, now),
        "houses": houses,
        "pillars": pillars,
        "now": now,
        "special_marks": special,
    }
