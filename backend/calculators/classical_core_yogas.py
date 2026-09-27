"""Classical natal-yoga rules used by :mod:`yoga_calculator`.

This module deliberately contains formation rules, not numerical "strength"
scores.  Every result carries the rule evidence and the textual source used.
The public YogaCalculator response shape remains unchanged; the structured
fields below are additive.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable, Mapping

from .classical_combustion import calculate_chart_combustion
from .friendship_calculator import FriendshipCalculator


VISIBLE_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
NINE_GRAHAS = (*VISIBLE_PLANETS, "Rahu", "Ketu")
SUN_YOGA_PLANETS = ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")
KEMADRUMA_KENDRA_PLANETS = ("Sun", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
SIGN_LORDS = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun", 5: "Mercury",
    6: "Venus", 7: "Mars", 8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter",
}
OWN_SIGNS = {
    "Sun": {4}, "Moon": {3}, "Mars": {0, 7}, "Mercury": {2, 5},
    "Jupiter": {8, 11}, "Venus": {1, 6}, "Saturn": {9, 10},
}
EXALTATION_SIGNS = {
    "Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5,
    "Jupiter": 3, "Venus": 11, "Saturn": 6,
}
DEBILITATION_SIGNS = {
    "Sun": 6, "Moon": 7, "Mars": 3, "Mercury": 11,
    "Jupiter": 9, "Venus": 5, "Saturn": 0,
}
KENDRAS = {1, 4, 7, 10}
TRIKONAS = {1, 5, 9}
DUSTHANAS = {6, 8, 12}


def _source(work: str, reference: str, url: str, note: str | None = None) -> dict[str, Any]:
    result = {"work": work, "reference_label": reference, "url": url}
    if note:
        result["textual_note"] = note
    return result


BPHS_34 = _source(
    "Brihat Parashara Hora Shastra",
    "BPHS 34.11–15",
    "https://sanskritdocuments.org/doc_z_misc_sociology_astrology/par3140.html",
)
BPHS_35 = _source(
    "Brihat Parashara Hora Shastra",
    "BPHS 35.1–17",
    "https://sanskritdocuments.org/doc_z_misc_sociology_astrology/par3140.html",
)
BPHS_36_GAJA = _source(
    "Brihat Parashara Hora Shastra",
    "BPHS 36.3–4",
    "https://sanskritdocuments.org/doc_z_misc_sociology_astrology/par3140.html",
)
BPHS_36_AMALA = _source(
    "Brihat Parashara Hora Shastra",
    "BPHS 36.5–6",
    "https://sanskritdocuments.org/doc_z_misc_sociology_astrology/par3140.html",
)
BPHS_37_CHANDRA = _source(
    "Brihat Parashara Hora Shastra",
    "BPHS 37.5–13",
    "https://sanskritdocuments.org/doc_z_misc_sociology_astrology/par3140.html",
    "The BPHS Kemadruma reading checks a planet in a Kendra from Lagna. Other texts preserve additional cancellation readings; they are not silently merged here.",
)
BPHS_38_SURYA = _source(
    "Brihat Parashara Hora Shastra",
    "BPHS 38.1–4",
    "https://sanskritdocuments.org/doc_z_misc_sociology_astrology/par3140.html",
)
BPHS_41_DHANA = _source(
    "Brihat Parashara Hora Shastra",
    "BPHS 41.2–17",
    "https://sanskritdocuments.org/doc_z_misc_sociology_astrology/par4145.html",
)
PHALA_6_1 = _source(
    "Phaladeepika",
    "Phaladeepika 6.1",
    "https://sanskritdocuments.org/doc_z_misc_sociology_astrology/phaladIpika.html",
)
PHALA_6_26 = _source(
    "Phaladeepika",
    "Phaladeepika 6.26–27",
    "https://sanskritdocuments.org/doc_z_misc_sociology_astrology/phaladIpika.html",
)
PHALA_6_5 = _source(
    "Phaladeepika",
    "Phaladeepika 6.5",
    "https://sanskritdocuments.org/doc_z_misc_sociology_astrology/phaladIpika.html",
    "This is retained as a separately identified textual reading; it is not merged into the selected BPHS Kemadruma rule.",
)
PHALA_6_37 = _source(
    "Phaladeepika",
    "Phaladeepika 6.37",
    "https://sanskritdocuments.org/doc_z_misc_sociology_astrology/phaladIpika.html",
    "The verse says mahita-bhava (translated as an auspicious bhava) without numbering those houses. This calculator resolves it through Phaladeepika 1.17: Houses 6, 8 and 12 are difficult; the others are good.",
)
PHALA_6_57 = _source(
    "Phaladeepika",
    "Phaladeepika 6.57, 63, 65, 69",
    "https://sanskritdocuments.org/doc_z_misc_sociology_astrology/phaladIpika.html",
    "Verse 6.57 gives two formation branches: the relevant lord is in a difficult house, or it is joined/aspected by an inauspicious planet.",
)

CLASSICAL_RESULTS = {
    "Ruchaka Yoga": "Phaladeepika 6.1 gives a commanding result: courage, leadership, wealth and fame.",
    "Bhadra Yoga": "Phaladeepika 6.1 gives a learned result: eloquence, long life, skill and wealth.",
    "Hamsa Yoga": "Phaladeepika 6.1 gives a respected result: virtue, wisdom and the standing of a ruler.",
    "Malavya Yoga": "Phaladeepika 6.1 gives a life of comfort: spouse, vehicles, fine things and enjoyment.",
    "Sasa Yoga": "Phaladeepika 6.1 gives authority: command over people and wealth from land or service.",
    "Sunapha Yoga": "BPHS 37 gives self-earned wealth, intelligence and a good name.",
    "Anapha Yoga": "BPHS 37 gives a sound body, virtue, comforts and reputation.",
    "Durudhura Yoga": "BPHS 37 gives wealth, vehicles, servants and enjoyment.",
    "Kemadruma Yoga": "BPHS 37 gives want of support: hardship, unsteady fortune and little help from others.",
    "Adhi Yoga": "BPHS 37 gives a ruler's standing: health, subdued enemies and long life.",
    "Vesi Yoga": "A benefic Vesi gives truthfulness, a steady mind and modest fortune. A malefic Vesi turns those same matters the other way.",
    "Vasi Yoga": "A benefic Vasi gives fame and wealth. A malefic Vasi gives the opposite tendency.",
    "Ubhayachari Yoga": "A benefic Ubhayachari gives the rank of a ruler, eloquence and long life. A malefic formation weakens that promise.",
    "Gaja Kesari Yoga": "BPHS 36.3–4 gives lasting fame, virtue and the ability to overcome enemies.",
    "Amala Yoga": "BPHS 36.5–6 gives a lasting good name and upright conduct.",
    "Saraswati Yoga": "Phaladeepika 6.26–27 gives learning, polished speech, poetry and wealth through knowledge.",
    "Kendra-Trikona Raja Yoga": "BPHS 34 gives power, status and authority through the Kendra–Trikona connection.",
    "Dhana Yoga": "BPHS 41 gives wealth. Verse 41.16 names the 5th and 9th lords, and planets joined with them, as the periods in which it arrives. The amount follows the planets' nature and strength.",
    "Harsha Yoga": "Phaladeepika 6.63 gives happiness, friends and comforts, even though the 6th lord is involved.",
    "Sarala Yoga": "Phaladeepika 6.65 gives long life, learning, courage and prosperity.",
    "Vimala Yoga": "Phaladeepika 6.69 gives independence, modest habits and a clean end to life.",
    "Dharma-Karma Yoga": "Phaladeepika 6.37 gives righteous authority: the person acts with power and is treated as a ruler.",
    "Rajju Yoga": "BPHS 35 gives a travelling nature and a jealous disposition.",
    "Musala Yoga": "BPHS 35 gives pride, wealth and attachment to one's own place.",
    "Nala Yoga": "BPHS 35 gives skill, wealth and a changeable mind.",
    "Mala Yoga": "BPHS 35 gives comforts and virtuous conduct.",
    "Sarpa Yoga": "BPHS 35 gives a crooked course and hardship.",
    "Gada Yoga": "BPHS 35 gives wealth, ritual and practical skill.",
    "Sakata Yoga": "BPHS 35 gives illness, want and a fortune that rises and falls.",
    "Vihaga Yoga": "BPHS 35 gives a wandering life and work as a messenger.",
    "Shringataka Yoga": "BPHS 35 gives happiness and wealth.",
    "Hala Yoga": "BPHS 35 gives work on the land and a life of want.",
    "Kamala Yoga": "BPHS 35 gives fame, virtue, long life and the standing of a ruler.",
    "Yoopa Yoga": "BPHS 35 gives religious acts, wealth and charity.",
    "Shara Yoga": "BPHS 35 gives a violent livelihood and confinement.",
    "Shakti Yoga": "BPHS 35 gives laziness, unhappiness and little wealth.",
    "Danda Yoga": "BPHS 35 gives service, separation from family and poverty.",
    "Nauka Yoga": "BPHS 35 gives fame, gains and a reputation connected with travel or water.",
    "Kuta Yoga": "BPHS 35 gives falsehood and the work of a jailer.",
    "Chatra Yoga": "BPHS 35 gives help to others, long life and the standing of a ruler.",
    "Chapa Yoga": "BPHS 35 gives courage and happiness that arrives later.",
    "Chakra Yoga": "BPHS 35 gives the rank of a king.",
    "Samudra Yoga": "BPHS 35 gives stable wealth and the standing of a ruler.",
    "Vapi Yoga": "BPHS 35 gives wealth that lasts and the habit of storing it.",
    "Ardha Chandra Yoga": "BPHS 35 gives command, good looks and leadership of people.",
    "Vajra Yoga": "BPHS 35 gives happiness at the start and end of life, with struggle in the middle.",
    "Yava Yoga": "BPHS 35 gives happiness in the middle of life, with struggle at the start and end.",
    "Gola Yoga": "BPHS 35 gives poverty and little learning.",
    "Yuga Yoga": "BPHS 35 gives poverty and disregard for custom.",
    "Shula Yoga": "BPHS 35 gives cruelty and quarrels.",
    "Kedara Yoga": "BPHS 35 gives helpfulness and wealth from the land.",
    "Pasha Yoga": "BPHS 35 gives wealth through work, talk and many dependents.",
    "Dama Yoga": "BPHS 35 gives wealth, generosity and fame.",
    "Vallaki (Veena) Yoga": "BPHS 35 gives learning, happiness and many friends.",
}


def _planet(chart: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    return ((chart or {}).get("planets") or {}).get(name) or {}


def _house(chart: Mapping[str, Any], name: str) -> int | None:
    value = _planet(chart, name).get("house")
    try:
        value = int(value)
    except (TypeError, ValueError):
        return None
    return value if 1 <= value <= 12 else None


def _sign(chart: Mapping[str, Any], name: str) -> int | None:
    value = _planet(chart, name).get("sign")
    try:
        value = int(value)
    except (TypeError, ValueError):
        return None
    return value if 0 <= value <= 11 else None


def _relative_house(reference: int | None, target: int | None) -> int | None:
    if reference is None or target is None:
        return None
    return ((target - reference) % 12) + 1


def _condition(rule_id: str, description: str, matched: bool = True) -> dict[str, Any]:
    return {"rule_id": rule_id, "description": description, "matched": bool(matched)}


def _result(
    name: str,
    description: str,
    source: Mapping[str, Any],
    conditions: Iterable[Mapping[str, Any]],
    *,
    planets: Iterable[str] = (),
    houses: Iterable[int] = (),
    **extra: Any,
) -> dict[str, Any]:
    payload = {
        "name": name,
        "description": description,
        "strength": None,
        "planets": list(dict.fromkeys(planets)),
        "houses": list(dict.fromkeys(h for h in houses if h is not None)),
        "classical_conditions": list(conditions),
        "source": dict(source),
    }
    payload.update(extra)
    if not payload.get("classical_result"):
        payload["classical_result"] = CLASSICAL_RESULTS.get(name)
    return payload


def _is_waxing(chart: Mapping[str, Any]) -> bool | None:
    sun = _planet(chart, "Sun").get("longitude")
    moon = _planet(chart, "Moon").get("longitude")
    try:
        elongation = (float(moon) - float(sun)) % 360.0
    except (TypeError, ValueError):
        return None
    return 0.0 < elongation <= 180.0


def _nature(
    chart: Mapping[str, Any], *, include_nodes: bool = False,
) -> tuple[set[str], set[str], dict[str, Any]]:
    """BPHS 3.11 contextual benefics/malefics for rules using saumya/papa.

    Nabhasa geometry is expressly a seven-planet scheme, so callers can keep
    the nodes outside it.  Rules stated generally in terms of grahas/papas can
    include Rahu and Ketu through ``include_nodes=True``.
    """
    domain = NINE_GRAHAS if include_nodes else VISIBLE_PLANETS
    present = {p for p in domain if _house(chart, p) is not None}
    benefics = {p for p in ("Jupiter", "Venus") if p in present}
    malefics = {p for p in ("Sun", "Mars", "Saturn") if p in present}
    if include_nodes:
        malefics.update(p for p in ("Rahu", "Ketu") if p in present)
    waxing = _is_waxing(chart)
    if "Moon" in present:
        if waxing is True:
            benefics.add("Moon")
        elif waxing is False:
            malefics.add("Moon")

    mercury_malefic_company = []
    mercury_sign = _sign(chart, "Mercury")
    if "Mercury" in present:
        for planet in malefics:
            if planet != "Mercury" and _sign(chart, planet) == mercury_sign:
                mercury_malefic_company.append(planet)
        if mercury_malefic_company:
            malefics.add("Mercury")
        else:
            benefics.add("Mercury")
    return benefics, malefics, {
        "waxing_moon": waxing,
        "mercury_joined_malefics": sorted(mercury_malefic_company),
        "node_policy": "included as malefics under BPHS 3.11" if include_nodes else "excluded by this yoga's seven-planet domain",
        "source": {
            "work": "Brihat Parashara Hora Shastra",
            "reference_label": "BPHS 3.11",
            "url": "https://sanskritdocuments.org/doc_z_misc_sociology_astrology/par0110.html",
        },
    }


def pancha_mahapurusha(chart: Mapping[str, Any]) -> list[dict[str, Any]]:
    definitions = {
        "Mars": "Ruchaka Yoga",
        "Mercury": "Bhadra Yoga",
        "Jupiter": "Hamsa Yoga",
        "Venus": "Malavya Yoga",
        "Saturn": "Sasa Yoga",
    }
    rows = []
    for planet, yoga_name in definitions.items():
        house, sign = _house(chart, planet), _sign(chart, planet)
        own = sign in OWN_SIGNS[planet]
        exalted = sign == EXALTATION_SIGNS[planet]
        if house not in KENDRAS or not (own or exalted):
            continue
        dignity = "exaltation sign" if exalted else "own sign"
        rows.append(_result(
            yoga_name,
            f"{planet} occupies House {house}, a Kendra, in its {dignity}.",
            PHALA_6_1,
            [
                _condition(f"PD-6.1-{planet}-KENDRA", f"{planet} is in Kendra House {house}"),
                _condition(f"PD-6.1-{planet}-DIGNITY", f"{planet} is in its {dignity}"),
            ],
            planets=[planet], houses=[house], planet=planet, house=house, sign=sign,
        ))
    return rows


def chandra_yogas(chart: Mapping[str, Any]) -> list[dict[str, Any]]:
    moon_house = _house(chart, "Moon")
    if moon_house is None:
        return []
    second = [p for p in SUN_YOGA_PLANETS if _relative_house(moon_house, _house(chart, p)) == 2]
    twelfth = [p for p in SUN_YOGA_PLANETS if _relative_house(moon_house, _house(chart, p)) == 12]
    rows: list[dict[str, Any]] = []
    if second and twelfth:
        rows.append(_result(
            "Durudhura Yoga", "Planets other than the Sun occupy both the 2nd and 12th from the Moon.",
            BPHS_37_CHANDRA,
            [_condition("BPHS-37.7-DURUDHURA", f"2nd: {', '.join(second)}; 12th: {', '.join(twelfth)}")],
            planets=[*second, *twelfth], houses=[_house(chart, p) for p in [*second, *twelfth]],
        ))
    elif second:
        rows.append(_result(
            "Sunapha Yoga", "Planets other than the Sun occupy the 2nd from the Moon.", BPHS_37_CHANDRA,
            [_condition("BPHS-37.7-SUNAPHA", f"2nd from Moon: {', '.join(second)}")],
            planets=second, houses=[_house(chart, p) for p in second],
        ))
    elif twelfth:
        rows.append(_result(
            "Anapha Yoga", "Planets other than the Sun occupy the 12th from the Moon.", BPHS_37_CHANDRA,
            [_condition("BPHS-37.7-ANAPHA", f"12th from Moon: {', '.join(twelfth)}")],
            planets=twelfth, houses=[_house(chart, p) for p in twelfth],
        ))
    else:
        kendra_from_lagna = [p for p in KEMADRUMA_KENDRA_PLANETS if _house(chart, p) in KENDRAS]
        if not kendra_from_lagna:
            phaladeepika_kendra_from_moon = [
                p for p in VISIBLE_PLANETS
                if p != "Moon" and _relative_house(moon_house, _house(chart, p)) in KENDRAS
            ]
            rows.append(_result(
                "Kemadruma Yoga",
                "No qualifying planet occupies the 2nd or 12th from the Moon, and no planet other than the Moon occupies a Kendra from Lagna under the selected BPHS reading.",
                BPHS_37_CHANDRA,
                [
                    _condition("BPHS-37.11-ADJACENT", "No qualifying planet is in the 2nd or 12th from the Moon"),
                    _condition("BPHS-37.11-LAGNA-KENDRA", "No qualifying planet is in a Kendra from Lagna"),
                ],
                planets=["Moon"], houses=[moon_house], type="affliction",
                selected_reading="BPHS 37.11–12",
                variant_readings=[{
                    "source": dict(PHALA_6_5),
                    "formed": not bool(phaladeepika_kendra_from_moon),
                    "reason": (
                        "No visible planet other than the Moon occupies a Kendra from the Moon."
                        if not phaladeepika_kendra_from_moon
                        else f"Cancelled in this reading by {', '.join(phaladeepika_kendra_from_moon)} in a Kendra from the Moon."
                    ),
                }],
            ))

    benefics, _, context = _nature(chart)
    adhi_planets = [p for p in sorted(benefics) if _relative_house(moon_house, _house(chart, p)) in {6, 7, 8}]
    if adhi_planets:
        rows.append(_result(
            "Adhi Yoga",
            "Natural benefics occupy the 6th, 7th or 8th from the Moon.",
            BPHS_37_CHANDRA,
            [_condition("BPHS-37.5-ADHI", ", ".join(f"{p} is {_relative_house(moon_house, _house(chart, p))}th from Moon" for p in adhi_planets))],
            planets=adhi_planets, houses=[_house(chart, p) for p in adhi_planets], nature_context=context,
        ))
    return rows


def surya_yogas(chart: Mapping[str, Any]) -> list[dict[str, Any]]:
    sun_house = _house(chart, "Sun")
    if sun_house is None:
        return []
    second = [p for p in SUN_YOGA_PLANETS if _relative_house(sun_house, _house(chart, p)) == 2]
    twelfth = [p for p in SUN_YOGA_PLANETS if _relative_house(sun_house, _house(chart, p)) == 12]
    if second and twelfth:
        name, rule, planets = "Ubhayachari Yoga", "BPHS-38.1-UBHAYACHARI", [*second, *twelfth]
        fact = f"2nd: {', '.join(second)}; 12th: {', '.join(twelfth)}"
    elif second:
        name, rule, planets = "Vesi Yoga", "BPHS-38.1-VESI", second
        fact = f"2nd from Sun: {', '.join(second)}"
    elif twelfth:
        name, rule, planets = "Vasi Yoga", "BPHS-38.1-VASI", twelfth
        fact = f"12th from Sun: {', '.join(twelfth)}"
    else:
        return []
    benefics, malefics, context = _nature(chart)
    composition = "mixed"
    if set(planets) <= benefics:
        composition = "benefic"
    elif set(planets) <= malefics:
        composition = "malefic"
    surya_results = {
        "Vesi Yoga": {
            "benefic": "This benefic Vesi gives truthfulness, a steady mind and modest fortune.",
            "malefic": "This malefic Vesi turns truthfulness, steadiness and fortune the other way.",
            "mixed": "This mixed Vesi gives a mixed result: the benefic planets in it support fortune, and the malefic planets weaken it.",
        },
        "Vasi Yoga": {
            "benefic": "This benefic Vasi gives fame and wealth.",
            "malefic": "This malefic Vasi gives the opposite of fame and wealth.",
            "mixed": "This mixed Vasi gives a mixed result: fame and wealth where the benefics prevail, and their loss where the malefics prevail.",
        },
        "Ubhayachari Yoga": {
            "benefic": "This benefic Ubhayachari gives the rank of a ruler, eloquence and long life.",
            "malefic": "This malefic Ubhayachari weakens rank, speech and longevity.",
            "mixed": "This mixed Ubhayachari gives a mixed result: rank and long life where the benefics prevail, and their loss where the malefics prevail.",
        },
    }
    return [_result(
        name,
        f"{name} is formed by planets other than the Moon in the stated position from the Sun. Its composition is {composition}; BPHS 38.4 directs the astrologer to distinguish benefic and malefic formation.",
        BPHS_38_SURYA,
        [_condition(rule, fact), _condition(f"{rule}-NATURE", f"Formation is {composition}")],
        planets=planets, houses=[_house(chart, p) for p in planets], composition=composition, nature_context=context,
        classical_result=surya_results[name][composition],
    )]


def gaja_kesari(
    chart: Mapping[str, Any], aspecting_planets: Callable[[int], list[str]],
) -> list[dict[str, Any]]:
    jupiter_house, moon_house = _house(chart, "Jupiter"), _house(chart, "Moon")
    if jupiter_house is None or moon_house is None:
        return []
    kendra_from_lagna = jupiter_house in KENDRAS
    kendra_from_moon = _relative_house(moon_house, jupiter_house) in KENDRAS
    benefics, _, context = _nature(chart)
    other_benefics = sorted((benefics - {"Jupiter"}) & set(aspecting_planets(jupiter_house)))
    joined_benefics = sorted(p for p in benefics - {"Jupiter"} if _house(chart, p) == jupiter_house)
    supporting_benefics = sorted(set(other_benefics + joined_benefics))
    sign = _sign(chart, "Jupiter")
    sign_lord = SIGN_LORDS.get(sign)
    enemy = sign_lord in FriendshipCalculator().NATURAL_ENEMIES["Jupiter"]
    combust = bool((calculate_chart_combustion(chart).get("planets", {}).get("Jupiter") or {}).get("is_combust"))
    debilitated = sign == DEBILITATION_SIGNS["Jupiter"]
    formed = (kendra_from_lagna or kendra_from_moon) and bool(supporting_benefics) and not (enemy or combust or debilitated)
    if not formed:
        return []
    anchors = [anchor for anchor, matched in (("Lagna", kendra_from_lagna), ("Moon", kendra_from_moon)) if matched]
    anchor = " and ".join(anchors)
    return [_result(
        "Gaja Kesari Yoga",
        f"Jupiter is in a Kendra from {anchor}, receives benefic support from {', '.join(supporting_benefics)}, and is clear of the three exclusions named in BPHS 36.3.",
        BPHS_36_GAJA,
        [
            _condition("BPHS-36.3-KENDRA", f"Jupiter is in a Kendra from {anchor}"),
            _condition("BPHS-36.3-BENEFIC", f"Benefic support: {', '.join(supporting_benefics)}"),
            _condition("BPHS-36.3-EXCLUSIONS", "Jupiter is not debilitated, combust or in an enemy sign"),
        ],
        planets=["Moon", "Jupiter", *supporting_benefics], houses=[moon_house, jupiter_house], nature_context=context,
        selected_reading="Strict BPHS 36.3",
        textual_note="A Kendra relationship between Moon and Jupiter alone is insufficient here; BPHS 36.3 also requires benefic support and the stated dignity exclusions.",
    )]


def amala(chart: Mapping[str, Any]) -> list[dict[str, Any]]:
    benefics, malefics, context = _nature(chart, include_nodes=True)
    rows = []
    moon_house = _house(chart, "Moon")
    targets = [("Lagna", 10)]
    if moon_house is not None:
        targets.append(("Moon", ((moon_house + 8) % 12) + 1))
    seen = set()
    for anchor, target in targets:
        occupants = {p for p in NINE_GRAHAS if _house(chart, p) == target}
        qualifying = sorted(occupants & benefics)
        disqualifying = sorted(occupants & malefics)
        if not qualifying or disqualifying:
            continue
        fingerprint = (target, tuple(qualifying))
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        rows.append(_result(
            "Amala Yoga",
            f"Only natural benefic planet(s) occupy the 10th from {anchor}: {', '.join(qualifying)}.",
            BPHS_36_AMALA,
            [_condition(f"BPHS-36.5-AMALA-{anchor.upper()}", f"House {target} contains {', '.join(qualifying)} and no natural malefic")],
            planets=qualifying, houses=[target], anchor=anchor, nature_context=context,
        ))
    return rows


def saraswati(chart: Mapping[str, Any]) -> list[dict[str, Any]]:
    planets = ("Mercury", "Jupiter", "Venus")
    if any(_house(chart, p) is None for p in planets):
        return []
    allowed = KENDRAS | {2, 5, 9}
    placements_ok = all(_house(chart, p) in allowed for p in planets)
    jupiter_sign = _sign(chart, "Jupiter")
    jupiter_sign_lord = SIGN_LORDS.get(jupiter_sign)
    jupiter_strong = (
        jupiter_sign == EXALTATION_SIGNS["Jupiter"]
        or jupiter_sign in OWN_SIGNS["Jupiter"]
        or jupiter_sign_lord in FriendshipCalculator().NATURAL_FRIENDS["Jupiter"]
    )
    if not (placements_ok and jupiter_strong):
        return []
    return [_result(
        "Saraswati Yoga",
        "Mercury, Jupiter and Venus occupy the Kendras, trines or House 2, while Jupiter is in exaltation, own or a friendly sign.",
        PHALA_6_26,
        [
            _condition("PD-6.26-PLACEMENTS", ", ".join(f"{p}: House {_house(chart, p)}" for p in planets)),
            _condition("PD-6.26-JUPITER", f"Jupiter is in sign {jupiter_sign + 1}, ruled by {jupiter_sign_lord}"),
        ],
        planets=planets, houses=[_house(chart, p) for p in planets],
    )]


def raj_yogas(
    chart: Mapping[str, Any],
    house_lord: Callable[[int], str | None],
    aspecting_planets: Callable[[int], list[str]],
) -> list[dict[str, Any]]:
    rows = []
    processed: set[tuple[str, str]] = set()
    lordships = {p: {h for h in range(1, 13) if house_lord(h) == p} for p in VISIBLE_PLANETS}
    # BPHS 34.13 separately recognizes one planet owning a Kendra and a
    # Trikona.  House 1 is both by nature; requiring distinct Kendra and
    # Trikona lordships prevents every Lagna lord from becoming this yoga.
    for planet, owned in lordships.items():
        kendra_owned = sorted(owned & {4, 7, 10})
        trikona_owned = sorted(owned & {5, 9})
        placed = _house(chart, planet)
        if not kendra_owned or not trikona_owned or placed not in KENDRAS | TRIKONAS:
            continue
        rows.append(_result(
            "Kendra-Trikona Raja Yoga",
            f"{planet} owns Kendra House {kendra_owned[0]} and Trikona House {trikona_owned[0]} and occupies House {placed}, a Kendra or Trikona.",
            BPHS_34,
            [_condition("BPHS-34.13-SINGLE-YOGAKARAKA", f"{planet} joins distinct Kendra and Trikona lordships in House {placed}")],
            planets=[planet], houses=[placed], kendra_house=kendra_owned[0], trikona_house=trikona_owned[0],
            relation_type="single planet with distinct Kendra and Trikona lordships",
            lordships=sorted(owned),
            exclusion_evaluation={
                "reference": "BPHS 34.15",
                "excluded": False,
                "reason": "This is BPHS 34.13's single-planet Yogakaraka condition; its distinct Kendra and Trikona lordships are stated explicitly.",
            },
        ))
    for kendra in sorted(KENDRAS):
        for trikona in sorted(TRIKONAS):
            k_lord, t_lord = house_lord(kendra), house_lord(trikona)
            if not k_lord or not t_lord or k_lord == t_lord:
                continue
            pair = tuple(sorted((k_lord, t_lord)))
            if pair in processed:
                continue
            processed.add(pair)
            k_house, t_house = _house(chart, k_lord), _house(chart, t_lord)
            conjunction = k_house is not None and k_house == t_house
            exchange = k_house == trikona and t_house == kendra
            mutual_aspect = (
                k_house is not None and t_house is not None
                and t_lord in aspecting_planets(k_house)
                and k_lord in aspecting_planets(t_house)
            )
            if not (conjunction or exchange or mutual_aspect):
                continue
            both_also_dusthana_lords = bool(lordships[k_lord] & DUSTHANAS) and bool(lordships[t_lord] & DUSTHANAS)
            if both_also_dusthana_lords:
                continue
            relation = "conjunction" if conjunction else "exchange" if exchange else "mutual full aspect"
            rows.append(_result(
                "Kendra-Trikona Raja Yoga",
                f"The lord of House {kendra} ({k_lord}) and lord of House {trikona} ({t_lord}) form a {relation}.",
                BPHS_34,
                [
                    _condition("BPHS-34.11-12-RELATION", f"Classical relationship: {relation}"),
                    _condition("BPHS-34.15-EXCLUSION", "The paired lords do not both simultaneously own a dusthana"),
                ],
                planets=[k_lord, t_lord], houses=[k_house, t_house], kendra_house=kendra, trikona_house=trikona,
                relation_type=relation,
                lordships={
                    k_lord: sorted(lordships[k_lord]),
                    t_lord: sorted(lordships[t_lord]),
                },
                exclusion_evaluation={
                    "reference": "BPHS 34.15",
                    "excluded": False,
                    "reason": "The two related lords are not both simultaneously lords of difficult houses.",
                },
            ))
    return rows


def dhana_yogas(
    chart: Mapping[str, Any], aspecting_planets: Callable[[int], list[str]],
) -> list[dict[str, Any]]:
    """BPHS 41.2–15 special wealth combinations, without a 2/11 shortcut."""
    rows = []
    fifth_sign = None
    houses = (chart or {}).get("houses") or []
    if len(houses) >= 5:
        fifth_sign = houses[4].get("sign")
    patterns = {
        2: ({1, 6}, "Venus", ("Mars",)),
        3: ({2, 5}, "Mercury", ("Moon", "Mars", "Jupiter")),
        4: ({4}, "Sun", ("Saturn", "Moon", "Jupiter")),
        5: ({9, 10}, "Saturn", ("Sun", "Moon")),
        6: ({8, 11}, "Jupiter", ("Mercury",)),
        7: ({0, 7}, "Mars", ("Venus",)),
        8: ({3}, "Moon", ("Saturn",)),
    }
    for verse, (signs, fifth_planet, eleventh_planets) in patterns.items():
        if fifth_sign not in signs or _house(chart, fifth_planet) != 5:
            continue
        if not all(_house(chart, p) == 11 for p in eleventh_planets):
            continue
        rows.append(_result(
            "Dhana Yoga",
            f"The special wealth combination in BPHS 41.{verse} is complete.",
            BPHS_41_DHANA,
            [_condition(f"BPHS-41.{verse}", f"{fifth_planet} is in House 5 in its stated sign; {', '.join(eleventh_planets)} occup{'y' if len(eleventh_planets) > 1 else 'ies'} House 11")],
            planets=[fifth_planet, *eleventh_planets], houses=[5, 11], rule_id=f"BPHS-41.{verse}",
            delivery_rule={
                "reference": "BPHS 41.16",
                "description": "The fifth and ninth lords, and planets joined to them, are named as wealth-givers in their own periods.",
            },
            qualification_rule={
                "reference": "BPHS 41.17",
                "description": "Judge the result through the planets' benefic or malefic nature and strength; no synthetic High/Medium/Low grade is assigned.",
            },
        ))

    asc_sign = int((chart or {}).get("ascendant", 0) / 30) if (chart or {}).get("ascendant") is not None else None
    lagna_patterns = {
        9: ({4}, "Sun", ("Mars", "Jupiter")),
        10: ({3}, "Moon", ("Mercury", "Jupiter")),
        11: ({0, 7}, "Mars", ("Mercury", "Venus", "Saturn")),
        12: ({2, 5}, "Mercury", ("Saturn", "Jupiter")),
        13: ({8, 11}, "Jupiter", ("Mercury", "Mars")),
        14: ({1, 6}, "Venus", ("Saturn", "Mercury")),
        15: ({9, 10}, "Saturn", ("Mars", "Jupiter")),
    }
    for verse, (signs, lagna_lord, influencers) in lagna_patterns.items():
        if asc_sign not in signs or _house(chart, lagna_lord) != 1:
            continue
        present_influence = set(aspecting_planets(1)) | {p for p in VISIBLE_PLANETS if _house(chart, p) == 1}
        if not set(influencers) <= present_influence:
            continue
        rows.append(_result(
            "Dhana Yoga",
            f"The Lagna-based wealth combination in BPHS 41.{verse} is complete.",
            BPHS_41_DHANA,
            [_condition(f"BPHS-41.{verse}", f"{lagna_lord} occupies its stated Lagna and receives conjunction/aspect from {', '.join(influencers)}")],
            planets=[lagna_lord, *influencers], houses=[1], rule_id=f"BPHS-41.{verse}",
            delivery_rule={
                "reference": "BPHS 41.16",
                "description": "The fifth and ninth lords, and planets joined to them, are named as wealth-givers in their own periods.",
            },
            qualification_rule={
                "reference": "BPHS 41.17",
                "description": "Judge the result through the planets' benefic or malefic nature and strength; no synthetic High/Medium/Low grade is assigned.",
            },
        ))
    return rows


def viparita_yogas(
    chart: Mapping[str, Any],
    house_lord: Callable[[int], str | None],
    aspecting_planets: Callable[[int], list[str]],
) -> list[dict[str, Any]]:
    """Phaladeepika 6.57's two explicit formation branches."""
    definitions = {
        6: ("Harsha Yoga", "Phaladeepika 6.63"),
        8: ("Sarala Yoga", "Phaladeepika 6.65"),
        12: ("Vimala Yoga", "Phaladeepika 6.69"),
    }
    _, malefics, nature_context = _nature(chart, include_nodes=True)
    rows = []
    for ruled_house, (name, result_reference) in definitions.items():
        lord = house_lord(ruled_house)
        lord_house = _house(chart, lord) if lord else None
        if not lord or lord_house is None:
            continue
        dusthana_branch = lord_house in DUSTHANAS
        joined_malefics = sorted(
            p for p in malefics if p != lord and _house(chart, p) == lord_house
        )
        aspecting_malefics = sorted(
            (set(aspecting_planets(lord_house)) & malefics) - {lord}
        )
        association_branch = bool(joined_malefics or aspecting_malefics)
        if not (dusthana_branch or association_branch):
            continue
        branches = []
        conditions = []
        if dusthana_branch:
            branches.append("difficult-house placement")
            conditions.append(_condition(
                f"PD-6.57-{name.split()[0].upper()}-DUSTHANA",
                f"{lord}, lord of House {ruled_house}, occupies difficult House {lord_house}",
            ))
        if association_branch:
            branches.append("malefic conjunction/aspect")
            association_parts = []
            if joined_malefics:
                association_parts.append(f"joined by {', '.join(joined_malefics)}")
            if aspecting_malefics:
                association_parts.append(f"aspected by {', '.join(aspecting_malefics)}")
            conditions.append(_condition(
                f"PD-6.57-{name.split()[0].upper()}-MALEFIC",
                f"{lord} is {' and '.join(association_parts)}",
            ))
        rows.append(_result(
            name,
            f"{lord}, lord of House {ruled_house}, satisfies Phaladeepika 6.57 through {' and '.join(branches)}.",
            PHALA_6_57,
            conditions,
            planets=[lord, *joined_malefics, *aspecting_malefics],
            houses=[lord_house],
            ruled_house=ruled_house,
            lord=lord,
            formation_branches=branches,
            result_reference=result_reference,
            nature_context=nature_context,
        ))
    return rows


def dharma_karma_yoga(
    chart: Mapping[str, Any], house_lord: Callable[[int], str | None],
) -> list[dict[str, Any]]:
    """Phaladeepika 6.37, preserving the verse's two-lord conjunction."""
    ninth_lord, tenth_lord = house_lord(9), house_lord(10)
    if not ninth_lord or not tenth_lord or ninth_lord == tenth_lord:
        # The verse says two lords (dvau). A single planet owning both houses
        # belongs under BPHS 34.13's Yogakaraka rule, not this named yoga.
        return []
    ninth_house, tenth_house = _house(chart, ninth_lord), _house(chart, tenth_lord)
    adopted_mahita_houses = set(range(1, 13)) - DUSTHANAS
    if ninth_house is None or ninth_house != tenth_house or ninth_house not in adopted_mahita_houses:
        return []
    return [_result(
        "Dharma-Karma Yoga",
        f"The distinct lords of Houses 9 and 10, {ninth_lord} and {tenth_lord}, are conjoined in House {ninth_house}.",
        PHALA_6_37,
        [
            _condition("PD-6.37-TWO-LORDS", f"Distinct lords: House 9 {ninth_lord}; House 10 {tenth_lord}"),
            _condition("PD-6.37-CONJUNCTION", f"Both occupy House {ninth_house}"),
            _condition("PD-6.37-MAHITA-ADOPTED", f"House {ninth_house} is not one of the difficult Houses 6, 8 or 12 under Phaladeepika 1.17"),
        ],
        planets=[ninth_lord, tenth_lord],
        houses=[ninth_house],
        adopted_reading={
            "term": "mahita-bhava",
            "rendered_as": "an auspicious/good house, excluding Houses 6, 8 and 12",
            "houses": sorted(adopted_mahita_houses),
            "status": "resolved through Phaladeepika's own house classification in 1.17; 6.37 itself does not enumerate house numbers",
        },
        classical_name="Raja Yoga of the conjoined 9th and 10th lords",
        compatibility_name="Dharma-Karma Yoga",
    )]


def nabhasa_yogas(chart: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    planets = (chart or {}).get("planets") or {}
    if any(p not in planets or _house(chart, p) is None or _sign(chart, p) is None for p in VISIBLE_PLANETS):
        return {}
    occupied_houses = {_house(chart, p) for p in VISIBLE_PLANETS}
    occupied_signs = {_sign(chart, p) for p in VISIBLE_PLANETS}
    result: dict[str, list[dict[str, Any]]] = {"ashraya_yogas": [], "dala_yogas": [], "akriti_yogas": [], "sankhya_yogas": []}

    modalities = [({0, 3, 6, 9}, "Rajju Yoga"), ({1, 4, 7, 10}, "Musala Yoga"), ({2, 5, 8, 11}, "Nala Yoga")]
    for signs, name in modalities:
        if all(_sign(chart, p) in signs for p in VISIBLE_PLANETS):
            result["ashraya_yogas"].append(_result(
                name, f"All seven visible planets occupy {name.split()[0].lower()}-class signs.", BPHS_35,
                [_condition(f"BPHS-35.7-{name.split()[0].upper()}", f"Occupied signs: {', '.join(str(s + 1) for s in sorted(occupied_signs))}")],
                planets=VISIBLE_PLANETS, houses=sorted(occupied_houses),
            ))

    benefics, malefics, nature_context = _nature(chart)
    for nature, candidates, name in (("benefics", benefics, "Mala Yoga"), ("malefics", malefics, "Sarpa Yoga")):
        candidate_houses = {_house(chart, p) for p in candidates}
        if candidates and candidate_houses <= KENDRAS and len(candidate_houses) == 3:
            result["dala_yogas"].append(_result(
                name, f"The chart's contextual natural {nature} occupy three Kendras.", BPHS_35,
                [_condition(f"BPHS-35.8-{name.split()[0].upper()}", f"{', '.join(sorted(candidates))} occupy Houses {', '.join(map(str, sorted(candidate_houses)))}")],
                planets=sorted(candidates), houses=sorted(candidate_houses), nature_context=nature_context,
            ))

    patterns: list[tuple[str, list[set[int]]]] = [
        ("Gada Yoga", [{1, 4}, {4, 7}, {7, 10}, {1, 10}]),
        ("Sakata Yoga", [{1, 7}]), ("Vihaga Yoga", [{4, 10}]),
        ("Shringataka Yoga", [{1, 5, 9}]),
        ("Hala Yoga", [{2, 6, 10}, {3, 7, 11}, {4, 8, 12}]),
        ("Kamala Yoga", [{1, 4, 7, 10}]),
        ("Yoopa Yoga", [{1, 2, 3, 4}]), ("Shara Yoga", [{4, 5, 6, 7}]),
        ("Shakti Yoga", [{7, 8, 9, 10}]), ("Danda Yoga", [{1, 10, 11, 12}]),
        ("Nauka Yoga", [{1, 2, 3, 4, 5, 6, 7}]),
        ("Kuta Yoga", [{4, 5, 6, 7, 8, 9, 10}]),
        ("Chatra Yoga", [{1, 7, 8, 9, 10, 11, 12}]),
        ("Chapa Yoga", [{1, 2, 3, 4, 10, 11, 12}]),
        ("Chakra Yoga", [{1, 3, 5, 7, 9, 11}]),
        ("Samudra Yoga", [{2, 4, 6, 8, 10, 12}]),
    ]
    for name, alternatives in patterns:
        if occupied_houses in alternatives:
            result["akriti_yogas"].append(_result(
                name, f"All seven visible planets occupy the complete {name.replace(' Yoga', '')} house pattern.", BPHS_35,
                [_condition(f"BPHS-35-AKRITI-{name.split()[0].upper()}", f"Occupied Houses: {', '.join(map(str, sorted(occupied_houses)))}")],
                planets=VISIBLE_PLANETS, houses=sorted(occupied_houses),
            ))

    if occupied_houses and occupied_houses.isdisjoint(KENDRAS):
        result["akriti_yogas"].append(_result(
            "Vapi Yoga", "All seven visible planets occupy houses other than Kendras.", BPHS_35,
            [_condition("BPHS-35.12-VAPI", f"Occupied Houses: {', '.join(map(str, sorted(occupied_houses)))}")],
            planets=VISIBLE_PLANETS, houses=sorted(occupied_houses),
        ))

    for start in (2, 3, 5, 6, 8, 9, 11, 12):
        pattern = {((start - 1 + offset) % 12) + 1 for offset in range(7)}
        if occupied_houses == pattern:
            result["akriti_yogas"].append(_result(
                "Ardha Chandra Yoga", f"All seven visible planets occupy seven consecutive houses beginning from House {start}, a non-Kendra.", BPHS_35,
                [_condition("BPHS-35-ARDHACHANDRA", f"Occupied Houses: {', '.join(map(str, sorted(occupied_houses)))}")],
                planets=VISIBLE_PLANETS, houses=sorted(occupied_houses),
            ))
            break

    benefic_houses = {_house(chart, p) for p in benefics}
    malefic_houses = {_house(chart, p) for p in malefics}
    for name, good_axis, bad_axis in (
        ("Vajra Yoga", {1, 7}, {4, 10}), ("Yava Yoga", {4, 10}, {1, 7}),
    ):
        if benefics and malefics and benefic_houses == good_axis and malefic_houses == bad_axis:
            result["akriti_yogas"].append(_result(
                name, f"Contextual benefics occupy Houses {sorted(good_axis)} and contextual malefics Houses {sorted(bad_axis)}.", BPHS_35,
                [_condition(f"BPHS-35.11-{name.split()[0].upper()}", "Both specified axes are fully occupied by the stated planet classes")],
                planets=VISIBLE_PLANETS, houses=sorted(occupied_houses), nature_context=nature_context,
            ))

    # BPHS 35.17 explicitly makes Sankhya the residual class after the other
    # Nabhasa forms have been excluded.
    if not any(result[key] for key in ("ashraya_yogas", "dala_yogas", "akriti_yogas")):
        names = {1: "Gola Yoga", 2: "Yuga Yoga", 3: "Shula Yoga", 4: "Kedara Yoga", 5: "Pasha Yoga", 6: "Dama Yoga", 7: "Vallaki (Veena) Yoga"}
        count = len(occupied_signs)
        if count in names:
            result["sankhya_yogas"].append(_result(
                names[count], f"After excluding the named Ashraya, Dala and Akriti patterns, the seven visible planets occupy {count} signs.", BPHS_35,
                [_condition(f"BPHS-35.16-17-SANKHYA-{count}", f"Occupied signs: {', '.join(str(s + 1) for s in sorted(occupied_signs))}")],
                planets=VISIBLE_PLANETS, houses=sorted(occupied_houses),
            ))
    return {key: value for key, value in result.items() if value}
