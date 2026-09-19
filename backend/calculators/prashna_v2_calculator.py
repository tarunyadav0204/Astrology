"""Question-family judgements for the frozen Praśnatantra–Tājika profile."""
from __future__ import annotations

from typing import Dict, List

from calculators.tajika_classical_engine import ANGLES, SIGN_RULERS, TajikaClassicalEngine
from prashna.source_ledger import TOPIC_SOURCES


TOPIC_HOUSE = {"career": 10, "wealth": 2, "relationship": 7, "marriage": 7,
               "travel": 9, "lost": 4, "property": 4}


class PrashnaV2Calculator:
    RULESET_VERSION = "prashnatantra-tajika-2.0.0"

    def __init__(self, chart: Dict):
        self.chart = chart
        self.e = TajikaClassicalEngine(chart)
        self.rules: List[Dict] = []

    def add(self, rule_id: str, matched: bool, polarity: str, plain: str, technical: str,
            source_section: str, **evidence) -> None:
        self.rules.append({"id": rule_id, "matched": bool(matched), "polarity": polarity,
                           "plain": plain, "technical": technical,
                           "source_section": source_section, "evidence": evidence})

    def lord(self, house: int) -> str:
        return self.e.house_lord(house)

    def applies(self, first: str, second: str) -> bool:
        return first != second and self.e.applies(first, second)

    def aspects(self, first: str, second: str) -> bool:
        return first != second and self.e.aspects(first, second)

    def occupied_by(self, house: int, names) -> bool:
        return any(self.e.house(name) == house for name in names)

    def house_cusp(self, house: int) -> float:
        return float(self.chart["houses"][house - 1]["cusp"])

    def house_supported(self, house: int) -> bool:
        return any(self.e.aspects_longitude(name, self.house_cusp(house)) for name in self.e.benefics)

    def supported(self, name: str) -> bool:
        return any(self.aspects(name, other) for other in self.e.benefics - {name})

    def afflicted(self, name: str) -> bool:
        return bool(self.e.afflictions(name))

    def strong(self, name: str) -> bool:
        return self.e.dignity(name)["grade"] in {"superior", "middling"} and not self.afflicted(name)

    def _career(self, asc: str, matter: str) -> List[str]:
        moon = "Moon"
        self.add("PT-II-108", ((self.e.house(asc) == 1 and self.applies(asc, matter)) or
                 (self.e.house(moon) == 1 and self.applies(moon, matter))) and self.house_supported(10), "support",
                 "You are directly connected with the professional outcome.",
                 "Ascendant lord or Moon in the ascendant applies to the tenth lord.", "II.108")
        exchange = asc != matter and self.e.house(asc) == 10 and self.e.house(matter) == 1
        self.add("PT-II-109a", exchange and not self.afflicted(asc) and not self.afflicted(matter), "support",
                 "The chart strongly links you and the position without a major affliction.",
                 "Unafflicted exchange of first and tenth lords.", "II.109")
        self.add("PT-II-109b", self.e.house(matter) == 1 and self.supported(matter), "support",
                 "The professional outcome comes to you and receives help.",
                 "Tenth lord in the ascendant with benefic application.", "II.109")
        slower = matter if abs(self.e.planets[matter]["speed"]) < abs(self.e.planets[asc]["speed"]) else asc
        self.add("PT-II-109c", self.applies(asc, matter) and self.afflicted(slower), "obstruction",
                 "The connection exists, but the planet expected to complete it is seriously weakened.",
                 "The slower significator in the application is afflicted.", "II.109", slower=slower,
                 afflictions=self.e.afflictions(slower))
        link = self.e.contact(asc, matter) if asc != matter else {"aspect": None}
        self.add("PT-II-110-hostile", self.applies(asc, matter) and self.e.house(slower) == 4 and
                 link.get("aspect") == "square" and self.strong(slower),
                 "obstruction", "The professional matter carries conflict and risk to standing.",
                 "Strong slower planet in hostile square, with affliction qualification.", "II.110")
        self.add("PT-II-110-trine", self.applies(asc, matter) and self.e.house(slower) == 4 and
                 link.get("aspect") == "trine" and self.strong(slower),
                 "support", "The professional connection is harmonious and the completing planet is capable.",
                 "Favourable trine to an unafflicted strong slower planet.", "II.110")
        moon_weak = self.e.dignity(moon)["grade"] in {"neutral", "inferior"} or self.afflicted(moon)
        self.add("PT-II-111-travel", moon_weak and self.strong(slower), "description",
                 "The text associates attainment with travel or movement first.",
                 "Weak Moon and a slower planet not devoid of strength.", "II.111", slower=slower)
        mars_exalted = self.e.dignity("Mars")["grade"] == "superior" and "exaltation" in self.e.dignity("Mars")["dignities"]
        self.add("PT-II-111-estate", self.e.house(asc) == 1 and mars_exalted, "support",
                 "The chart gives an additional strong indication for securing the position or estate.",
                 "Ascendant lord in ascendant and Mars exalted.", "II.111")
        yogas = self.e.all_configurations(asc, matter, 10)
        kambula = next(row for row in yogas if row["name"] == "kambula")["matched"]
        self.add("PT-II-112", kambula and self.e.house(moon) in ANGLES, "support",
                 "The flow of events reinforces the job connection.",
                 "Kambūla between first and tenth significators with angular Moon.", "II.112")
        dispositor = SIGN_RULERS[self.e.planets[asc]["sign"]]
        self.add("PT-II-113", self.e.house(dispositor) in {6, 8, 12} or self.e.solar_condition(asc) == "set" or
                 (self.applies(asc, matter) and link.get("aspect") == "square"), "obstruction",
                 "The chart shows substantial difficulty or contention around obtaining the position.",
                 "Dispositor of ascendant lord is in an unfavourable house, ascendant lord is set, or the application is square.", "II.113",
                 dispositor=dispositor, dispositor_house=self.e.house(dispositor))
        sixth, twelfth, seventh = self.lord(6), self.lord(12), self.lord(7)
        asc_major_dignity = bool({"domicile", "exaltation"} & set(self.e.dignity(asc)["dignities"]))
        current = self.e.house(asc) in ANGLES and asc_major_dignity and not self.afflicted(asc) and self.applies(asc, moon)
        self.add("PT-III-72", self.e.house(asc) in ANGLES and (self.applies(asc, sixth) or self.applies(asc, twelfth)),
                 "support", "The present work can benefit an existing employer.",
                 "Angular ascendant lord applies to the sixth or twelfth lord.", "III.72")
        self.add("PT-III-73", current, "support",
                 "The present position has a specific indication for improvement.",
                 "Strong unafflicted angular ascendant lord applies to the Moon.", "III.73")
        seventh_major_dignity = bool({"domicile", "exaltation"} & set(self.e.dignity(seventh)["dignities"]))
        self.add("PT-III-74", self.e.house(seventh) in ANGLES and seventh_major_dignity and
                 not self.afflicted(seventh) and self.applies(seventh, moon) and self.supported(seventh),
                 "support", "A new employer or counterpart is shown as capable and helpful.",
                 "Strong angular seventh lord applies to the Moon with benefic condition.", "III.74")
        self.add("PT-III-75", self.e.asc_sign in {1, 3, 5, 7, 9, 11}, "description",
                 "The rising sign supplies a traditional contextual clue; it does not decide the job outcome by itself.",
                 "Prishtodaya rising-sign statement retained with the text's instruction to weigh all pros and cons.", "III.75")
        return ["II.108-113", "III.72-75"]

    def _wealth(self, asc: str, matter: str) -> List[str]:
        moon = "Moon"
        benefic_help = self.supported(matter)
        self.add("PT-II-6-8", self.applies(matter, asc) or self.applies(matter, moon) or benefic_help,
                 "support", "The payment or gain is connected to you or receives help.",
                 "Second lord applies to ascendant lord or Moon, or receives benefic contact.", "II.6-8")
        malefics_in_second = [p for p in self.e.malefics if self.e.house(p) == 2]
        self.add("PT-II-7", bool(malefics_in_second), "obstruction",
                 "The gain is shown with difficulty, distance, or an accompanying problem.",
                 "Malefic occupation of the second house qualifies the gain.", "II.7", planets=malefics_in_second)
        self.add("PT-II-9", self.applies(asc, matter), "support",
                 "You and the expected payment are directly connected.",
                 "Ascendant lord applies to the second lord.", "II.9")
        mercury_condition = self.e.house("Mercury") == 1 and any(self.aspects("Mercury", p) for p in {"Moon"} | self.e.malefics - {"Mercury"})
        self.add("PT-II-9-mercury", mercury_condition, "support",
                 "Mercury in the ascendant gives a gain indication.",
                 "Mercury in ascendant aspected by Moon or a malefic.", "II.9")
        self.add("PT-II-9-qualification", mercury_condition, "obstruction",
                 "The same rule warns that the gain comes with an untoward circumstance.",
                 "Mercury rule explicitly combines gain with trouble.", "II.9")
        trio = all(self.e.house(name) in {1, 2, 4, 5, 7, 9, 10} for name in {asc, matter, moon})
        connected = self.aspects(asc, matter) and (self.aspects(moon, asc) or self.aspects(moon, matter))
        self.add("PT-II-10", trio and connected, "support",
                 "You, the gain, and the unfolding events are jointly connected in effective houses.",
                 "Ascendant lord, second lord and Moon join or mutually connect in second, angle, or trine.", "II.10")
        self.add("PT-II-11", self.strong(asc) and (self.occupied_by(1, self.e.benefics) or self.house_supported(1)), "description",
                 "You are shown with enough strength and assistance to receive the gain.",
                 "Ascendant lord meets the selected five-dignity strength proxy and a benefic occupies/aspects the ascendant.", "II.11",
                 textual_note="The English edition says benefic shadvargas; production exposes the selected Hayanaratna dignity reading.")
        immediate = self.e.house(moon) in {4, 7} or self.e.house("Sun") == 10 or self.occupied_by(1, self.e.benefics)
        self.add("PT-II-12", immediate, "support",
                 "The text gives an additional indication of prompt receipt.",
                 "Moon in fourth/seventh, Sun in tenth, or benefic in ascendant.", "II.12")
        return ["II.6-12"]

    def _relationship(self, asc: str, matter: str) -> List[str]:
        """Judge a defined contact/reconciliation outcome without inventing a phone-specific rule.

        Prashna Tantra I.25 assigns spouse/partner and disputes to the seventh;
        II.1, 3-4, 9 and 13 supply the declared fulfilment test for the selected object.
        """
        moon = "Moon"
        cusp = self.house_cusp(7)
        lord_support = self.e.house(matter) == 7 or self.e.aspects_longitude(matter, cusp)
        benefic_support = self.occupied_by(7, self.e.benefics) or self.house_supported(7)
        malefic_pressure = [name for name in self.e.malefics
                            if self.e.house(name) == 7 or self.e.aspects_longitude(name, cusp)]
        self.add("PT-II-1-support", lord_support or benefic_support, "support",
                 "The other person and the relationship receive a strengthening influence.",
                 "The seventh house is joined or aspected by its lord or a benefic.", "II.1",
                 seventh_lord=matter, lord_support=lord_support, benefic_support=benefic_support)
        self.add("PT-II-1-obstruction", bool(malefic_pressure), "obstruction",
                 "Conflict or pressure continues to weigh on the connection.",
                 "A malefic joins or aspects the seventh house.", "II.1", planets=malefic_pressure)

        same_lord = asc == matter
        asc_to_seventh = self.e.aspects_longitude(asc, cusp)
        matter_to_ascendant = self.e.aspects_longitude(matter, float(self.chart["ascendant"]))
        direct_link = same_lord or self.aspects(asc, matter)
        moon_link = (self.aspects(moon, asc) if moon != asc else True) and (
            self.aspects(moon, matter) if moon != matter else True)
        fulfilment = ((self.e.aspects_longitude(asc, float(self.chart["ascendant"])) and lord_support) or
                       (asc_to_seventh and matter_to_ascendant) or direct_link or moon_link)
        self.add("PT-II-3-4", fulfilment, "support",
                 "The chart connects you, the other person, and the requested outcome.",
                 "The ascendant lord and seventh-house significator connect through the houses, each other, or the Moon.",
                 "II.3-4", same_lord=same_lord, direct_link=direct_link, moon_link=moon_link,
                 asc_to_seventh=asc_to_seventh, matter_to_ascendant=matter_to_ascendant)

        matter_afflictions = self.e.afflictions(matter)
        verse_nine_adversity = [condition for condition in matter_afflictions
                                if condition == "set" or condition.startswith("hostile_contact_")]
        self.add("PT-II-9", bool(verse_nine_adversity), "obstruction",
                 "The other person's indicator is weakened, making the hoped-for response unreliable.",
                 "The matter significator is combust or receives a hostile malefic contact.", "II.9",
                 afflictions=verse_nine_adversity)
        absent = not same_lord and not matter_to_ascendant and not self.aspects(matter, asc)
        self.add("PT-II-13", absent, "obstruction",
                 "The required connection between the other person and you is absent.",
                 "The matter significator does not aspect the ascendant or its lord.", "II.13")
        return ["I.25", "II.1", "II.3-4", "II.9", "II.13"]

    def _marriage(self, asc: str, matter: str) -> List[str]:
        moon = "Moon"
        link = self.applies(matter, asc) or self.applies(matter, moon)
        self.add("PT-II-62", link, "support", "The proposal or prospective spouse is connected to you.",
                 "Seventh lord applies to ascendant lord or Moon.", "II.62")
        self.add("PT-II-63-effort", self.e.house(asc) == 7 or self.e.house(moon) == 7, "support",
                 "Your own effort is central to moving the proposal forward.",
                 "Ascendant lord or Moon occupies the seventh.", "II.63")
        musaripha = asc != moon and self.e.contact(asc, moon)["state"] == "isarapha"
        self.add("PT-II-64-without-effort", musaripha or self.applies(asc, matter), "support",
                 "The matter may come forward without extensive searching.",
                 "Ascendant lord separates from Moon or applies to seventh lord.", "II.64")
        afflictions = self.e.afflictions(matter)
        self.add("PT-II-64-66", link and bool(afflictions), "obstruction",
                 "The connection is present, but the prospective-spouse indicator is seriously weakened.",
                 "The contacted seventh lord is set or afflicted; the eighth-lord obstruction is also evaluated.",
                 "II.64-66", afflictions=afflictions)
        eighth = self.lord(8)
        defeated = eighth in self.e.malefics
        self.add("PT-II-66", defeated, "obstruction", "A separate obstructing factor overpowers the proposal indicator.",
                 "The eighth lord is a malefic.", "II.66", eighth_lord=eighth)
        family_obstructors = [house for house in (3, 4) if self.lord(house) in self.e.malefics]
        self.add("PT-II-66-family", bool(family_obstructors), "description",
                 "The text attributes possible family involvement in an obstruction; this is not treated as proof about a person.",
                 "Malefic third/fourth lord denotes sibling/father source in the text.", "II.66", houses=family_obstructors)
        return ["II.62-66"]

    def _travel(self, asc: str, matter: str) -> List[str]:
        link = self.applies(asc, matter)
        angular = self.e.house(asc) in ANGLES or self.e.house(matter) in ANGLES
        self.add("PT-II-95", link and angular, "support", "The planned journey is connected to you and shown as able to proceed.",
                 "First and ninth lords apply with one significator angular.", "II.95")
        contact = self.e.contact(asc, matter) if asc != matter else {"aspect": None}
        self.add("PT-II-96", self.e.house(matter) == 1 and link and contact.get("aspect") != "trine", "obstruction",
                 "The present pattern favours remaining where you are.",
                 "Ninth lord in ascendant applies without the stated trinal exception.", "II.96")
        third_planets = [p for p in self.e.planets if self.e.house(p) == 3 and self.applies(asc, p)]
        self.add("PT-II-97", self.e.house(asc) in ANGLES and bool(third_planets) and not any(self.afflicted(p) for p in third_planets),
                 "support", "A movement indicator supports departure without a major affliction.",
                 "Angular ascendant lord applies to an unafflicted planet in the third.", "II.97", planets=third_planets)
        angular_malefics = [p for p in self.e.malefics if self.e.house(p) in ANGLES]
        self.add("PT-II-97-malefics", bool(angular_malefics), "obstruction", "Strong obstacles around the circumstances can prevent departure.",
                 "Malefics occupy angles.", "II.97", planets=angular_malefics)
        self.add("PT-II-98", self.occupied_by(7, self.e.malefics) or self.occupied_by(10, self.e.malefics), "obstruction",
                 "The destination or the journey's purpose faces obstruction.",
                 "Malefic in seventh obstructs the object; in tenth shows authority or elder obstruction.", "II.98")
        self.add("PT-II-99", link and (self.afflicted(asc) or self.afflicted(matter)), "obstruction",
                 "The journey link exists, but it carries a traditional warning of loss or difficulty.",
                 "The first/ninth application is afflicted by a malefic.", "II.99")
        self.add("PT-II-100", link and (self.e.house(asc) in {7, 8} or self.e.house(matter) in {7, 8}), "obstruction",
                 "The journey connection falls in a house associated here with affliction.",
                 "First/ninth application has reference to seventh or eighth.", "II.100")
        self.add("PT-II-101-104", self.occupied_by(4, self.e.benefics) or self.occupied_by(7, self.e.benefics) or self.occupied_by(10, self.e.benefics),
                 "support", "The destination, purpose, or conclusion receives a helpful influence.",
                 "Benefic occupation of destination, purpose, or conclusion houses.", "II.101-104")
        return ["II.95-104"]

    def _lost(self, asc: str, matter: str) -> List[str]:
        moon, fourth, seventh, second = "Moon", self.lord(4), self.lord(7), self.lord(2)
        self.add("PT-III-76", self.e.house(fourth) == 1 or (self.e.house(moon) == 1 and self.aspects(fourth, moon)),
                 "support", "The missing possession remains connected to you and its expected place.",
                 "Fourth lord in ascendant, or Moon there aspected by fourth lord.", "III.76")
        self.add("PT-III-77-support", self.e.house(second) in {2, 4}, "support",
                 "The possessions indicator supports recovery.", "Second lord in second or fourth.", "III.77")
        self.add("PT-III-77-obstruction", self.occupied_by(4, self.e.malefics), "obstruction",
                 "A difficult influence in the item's house works against recovery.", "Malefic occupation of fourth.", "III.77")
        no_recovery = self.e.house("Mars") in {7, 8} or (self.e.house("Rahu") == 1 and self.e.house("Sun") == 8)
        self.add("PT-III-78-obstruction", no_recovery, "obstruction", "The text gives a direct non-recovery indication.",
                 "Mars in seventh/eighth, or Rahu in ascendant with Sun in eighth.", "III.78")
        favourable_lords = any(self.lord(house) in {"Moon", "Jupiter"} for house in (7, 8, 10))
        self.add("PT-III-78-recovery", favourable_lords, "support", "A recovery indicator is present through the relevant house ruler.",
                 "Moon or Jupiter rules the seventh, eighth, or tenth.", "III.78")
        exchange = asc != seventh and self.e.house(asc) == 7 and self.e.house(seventh) == 1
        seventh_join = asc != seventh and self.e.house(asc) == self.e.house(seventh) == 7 and self.applies(asc, seventh)
        self.add("PT-III-79", exchange or seventh_join, "support", "The chart directly connects you with the person or route through which the item can return.",
                 "First/seventh exchange, or their lords apply in seventh.", "III.79")
        self.add("PT-III-80-support", self.applies(asc, seventh), "support", "Contact with another party supports return.",
                 "First and seventh lords apply.", "III.80")
        self.add("PT-III-80-obstruction", self.e.house("Sun") == 1 and self.e.house(moon) == 7, "obstruction",
                 "The Sun–Moon placement is a direct obstacle to recovery.", "Sun in ascendant and Moon in seventh.", "III.80")
        tenth, third, ninth = self.lord(10), self.lord(3), self.lord(9)
        self.add("PT-III-83-authority", self.applies(tenth, asc), "support",
                 "Recovery may come through an authority or formal channel.", "Tenth lord applies to ascendant lord.", "III.83")
        self.add("PT-III-83-elsewhere", self.applies(third, seventh) or self.applies(ninth, seventh), "support",
                 "The item may be recovered away from the original place.", "Third or ninth lord applies to seventh lord.", "III.83")
        moon_benefic = self.e.house(moon) in {1, 10} and any(self.applies(moon, b) or self.aspects(moon, b) for b in self.e.benefics - {moon})
        self.add("PT-III-84", moon_benefic, "support", "The Moon receives the helpful contact specified for recovery.",
                 "Moon in ascendant/tenth has benefic application or friendly benefic aspect.", "III.84")
        self.add("PT-III-91", self.e.house(asc) == 7 and self.applies(asc, seventh), "support",
                 "A direct first/seventh connection supports recovery.", "Ascendant lord in seventh applies to seventh lord.", "III.91")
        asc_weak = self.e.dignity(asc)["grade"] in {"neutral", "inferior"} or self.afflicted(asc)
        authority_conjunction = self.e.planets[asc]["sign"] == self.e.planets[tenth]["sign"]
        self.add("PT-III-94-95", self.applies(asc, seventh) or (not self.applies(asc, seventh) and asc_weak) or authority_conjunction,
                 "support", "The text indicates return directly or recovery through an authority.",
                 "First/seventh application, weak first lord without it, or first/tenth conjunction.", "III.94-95")
        self.add("PT-III-96-obstruction", self.e.house(second) in {7, 8}, "obstruction",
                 "The possessions ruler is placed in a house that denies recovery in this rule.", "Second lord in seventh or eighth.", "III.96")
        self.add("PT-III-96-recovery", self.applies(second, ninth), "support",
                 "A second/ninth connection supports getting the item back.", "Second and ninth lords apply.", "III.96")
        self.add("PT-III-97", not self.aspects(asc, second), "obstruction",
                 "The chart may bring news of the item without recovery.", "No mutual aspect between first and second lords.", "III.97")
        # III.81-97 primarily describe location, distance, custody, direction and the
        # character of another party. They are retained as descriptive evidence and
        # are never used to accuse a named person.
        self.add("PT-III-81-97-location", True, "description", "The technical details include traditional location clues; treat them only as search prompts.",
                 "Location/direction/custody indications are descriptive and do not decide recovery.", "III.81-97",
                 item_house=self.e.house(fourth), item_sign=self.e.planets[fourth]["sign"],
                 item_lord=fourth, direction=("east", "south", "west", "north")[self.e.planets[fourth]["sign"] % 4])
        return ["III.76-97"]

    def _property(self, asc: str, matter: str, intent: str) -> List[str]:
        strong_buyer = self.strong(asc)
        self.add("PT-III-183-184", intent == "buy" and strong_buyer, "support",
                 "The buyer is shown with enough strength to complete the purchase.",
                 "Strong ascendant and ascendant lord support purchase and benefit.", "III.183-184")
        self.add("PT-III-183-184-weak", intent == "buy" and not strong_buyer, "obstruction",
                 "The buyer's indicator lacks the strength required by this purchase rule.",
                 "Ascendant or its lord does not meet the stated strength condition.", "III.183-184")
        eleventh_planets = [p for p in self.e.planets if self.e.house(p) == 11 and self.strong(p)]
        self.add("PT-III-185", intent == "sell" and bool(eleventh_planets), "support",
                 "The sale has a traditional indication of profit.",
                 "Strong planet or planets occupy the eleventh for a sale.", "III.185", planets=eleventh_planets)
        self.add("PT-III-185-no-profit", intent == "sell" and not eleventh_planets, "obstruction",
                 "The chart does not show the strength required for profit from this sale.",
                 "No strong planet occupies the eleventh in the sale rule.", "III.185")
        return ["III.183-185"]

    def calculate(self, topic: str, intent: str = "outcome") -> Dict:
        if topic not in TOPIC_HOUSE:
            raise ValueError(f"The {topic} module is not available in this Prashna ruleset.")
        asc, matter = self.lord(1), self.lord(TOPIC_HOUSE[topic])
        coverage = getattr(self, f"_{topic}")(asc, matter, intent) if topic == "property" else getattr(self, f"_{topic}")(asc, matter)
        yogas = self.e.all_configurations(asc, matter, TOPIC_HOUSE[topic])
        # Destructive qualifications modify an otherwise relevant application;
        # they do not create a free-standing negative answer.
        for name in ("radda", "khallasara", "manau"):
            yoga = next(row for row in yogas if row["name"] == name)
            self.add(f"HR-{name}", yoga["matched"], "obstruction",
                     {"radda": "The connection is present, but the receiving planet cannot carry it through reliably.",
                      "khallasara": "The main connection lacks participation from the Moon, so completion is weakened.",
                      "manau": "A difficult outside influence interferes with the connection."}[name],
                     yoga["source"]["implementation_gloss"], yoga["source"]["section"], **yoga["evidence"])
        supports = [r for r in self.rules if r["matched"] and r["polarity"] == "support"]
        obstacles = [r for r in self.rules if r["matched"] and r["polarity"] == "obstruction"]
        if supports and obstacles:
            result = "mixed"
        elif supports:
            result = "favorable"
        elif obstacles:
            result = "unfavorable"
        else:
            result = "cannot_judge"
        roles = []
        from prashna.question_interpreter import TOPICS
        for house, role in TOPICS[topic]["roles"].items():
            roles.append({"house": house, "role": role, "lord": self.lord(house)})
        return {"method": "Praśnatantra–Tājika", "ruleset_version": self.RULESET_VERSION,
                "topic": topic, "intent": intent, "result": result, "roles": roles,
                "significators": {"you": asc, "matter": matter, "moon": "Moon"},
                "rules": self.rules, "yogas": yogas, "contacts": self.e.contact_records(),
                "coverage": {"declared_sections": coverage, "source_records": TOPIC_SOURCES[topic],
                             "implementation_complete_for_declared_scope": True,
                             "independent_textual_review": "pending"},
                "supporting_rule_ids": [r["id"] for r in supports],
                "obstructing_rule_ids": [r["id"] for r in obstacles]}
