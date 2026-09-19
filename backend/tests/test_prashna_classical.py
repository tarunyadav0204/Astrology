from datetime import date

import pytest

from calculators.prashna_classical_chart import hayanaratna_ayanamsa, house_junctions, locate_house, sripati_cusps
from calculators.tajika_classical_engine import TajikaClassicalEngine
from calculators.prashna_v2_calculator import PrashnaV2Calculator
from prashna.question_interpreter import GUIDED_QUESTIONS, public_topics, resolve_guided_question


SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")


def planet(longitude, speed=1.0, house=None):
    return {"longitude": longitude % 360, "speed": speed, "retrograde": speed < 0,
            "sign": int(longitude % 360 // 30), "degree": longitude % 30,
            "house": house or int(longitude % 360 // 30) + 1, "house_strength": 10}


def chart(**overrides):
    placements = {
        "Sun": planet(130, 1.0, 5), "Moon": planet(10, 13, 1), "Mars": planet(75, .5, 3),
        "Mercury": planet(35, 1.2, 2), "Jupiter": planet(15, .08, 1),
        "Venus": planet(65, 1.1, 3), "Saturn": planet(15, .03, 1),
        "Rahu": planet(305, -.05, 11), "Ketu": planet(125, -.05, 5),
    }
    placements.update(overrides)
    return {"ascendant": 0.0, "midheaven": 270.0, "planets": placements,
            "houses": [{"house": i + 1, "cusp": i * 30, "cusp_sign": i,
                        "begin_junction": (i * 30 - 15) % 360, "end_junction": (i * 30 + 15) % 360}
                       for i in range(12)]}


def test_hayanaratna_profile_uses_quadrant_cusps_and_junction_strength():
    cusps = sripati_cusps(0, 270)
    assert cusps == pytest.approx([0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330])
    junctions = house_junctions(cusps)
    assert locate_house(0, cusps, junctions) == (1, 20.0)
    # A junction belongs to the house that begins there; either side has zero strength.
    assert locate_house(15, cusps, junctions) == (2, 0.0)
    assert locate_house(16, cusps, junctions)[0] == 2


def test_hayanaratna_precession_is_reproducible_and_not_lahiri_alias():
    assert hayanaratna_ayanamsa(date(2026, 9, 19), 176.45) == pytest.approx(22.91235, abs=1e-4)


def test_contact_is_order_independent_and_uses_swifter_planet_orb():
    e = TajikaClassicalEngine(chart(Moon=planet(10, 13, 1), Saturn=planet(15, .03, 1)))
    forward = e.contact("Moon", "Saturn")
    reverse = TajikaClassicalEngine(chart(Moon=planet(10, 13, 1), Saturn=planet(15, .03, 1))).contact("Saturn", "Moon")
    assert forward["state"] == reverse["state"] == "itthasala"
    assert forward["swifter"] == "Moon"
    assert forward["orb"] == 12


def test_impending_contact_is_seen_across_a_sign_boundary():
    e = TajikaClassicalEngine(chart(Moon=planet(29, 13, 1), Saturn=planet(31, .03, 2)))
    assert e.contact("Moon", "Saturn")["state"] == "itthasala"


def test_enemy_domicile_uses_declared_hayanaratna_friendship_scheme():
    # Capricorn belongs to Saturn, an enemy of the Sun in the selected
    # constant twofold table. This is the inferior Kamboola condition.
    dignity = TajikaClassicalEngine(chart(Sun=planet(280, 1.0, 10))).dignity("Sun")
    assert dignity["grade"] == "inferior"
    assert dignity["sign_ruler"] == "Saturn"
    assert dignity["sign_relation"] == "enemy"
    assert dignity["friendship_scheme"] == "Hayanaratna 2.4.1 constant twofold"


def test_all_sixteen_tajika_configurations_are_always_reported():
    rows = TajikaClassicalEngine(chart()).all_configurations("Mars", "Jupiter")
    assert {row["name"] for row in rows} == {
        "ikkavala", "induvara", "itthasala", "isarapha", "nakta", "yamaya", "manau",
        "kambula", "gairikambula", "khallasara", "radda", "duhphalikutta",
        "dutthotthadabira", "tambira", "kuttha", "duruhpha",
    }
    assert all(row["source"]["url"].startswith("https://") for row in rows)


def test_nakta_matches_samjnatantra_2_26_degree_pattern():
    e = TajikaClassicalEngine(chart(Mercury=planet(130, 1.3, 5),
                                    Jupiter=planet(342, .08, 12), Moon=planet(251, 13, 9)))
    row = next(r for r in e.all_configurations("Mercury", "Jupiter", 7) if r["name"] == "nakta")
    assert row["matched"] is True
    assert row["evidence"]["intermediaries"] == ["Moon"]


def test_yamaya_matches_samjnatantra_2_29_degree_pattern():
    e = TajikaClassicalEngine(chart(Venus=planet(16, 1.1, 1), Moon=planet(36, 13, 2),
                                    Jupiter=planet(100, .08, 4)))
    row = next(r for r in e.all_configurations("Venus", "Moon", 10) if r["name"] == "yamaya")
    assert row["matched"] is True
    assert "Jupiter" in row["evidence"]["intermediaries"]


def test_topic_resolution_preserves_conflict_and_absence():
    result = PrashnaV2Calculator(chart()).calculate("career")
    assert result["result"] in {"favorable", "unfavorable", "mixed", "cannot_judge"}
    assert result["coverage"]["implementation_complete_for_declared_scope"] is True
    assert result["coverage"]["independent_textual_review"] == "pending"
    assert all("source_section" in row for row in result["rules"])


@pytest.mark.parametrize("topic", ["career", "wealth", "relationship", "marriage", "travel", "lost", "property"])
def test_each_enabled_topic_has_a_closed_source_module(topic):
    result = PrashnaV2Calculator(chart()).calculate(topic, "buy")
    assert result["topic"] == topic
    assert result["coverage"]["declared_sections"]
    assert result["rules"]


def test_guided_question_id_determines_topic_intent_and_wording():
    selected = resolve_guided_question("property_sale")
    assert selected["status"] == "selected"
    assert selected["topic"] == "property"
    assert selected["intent"] == "sell"
    assert selected["original_question"] == "Will this specific property sale complete profitably?"


@pytest.mark.parametrize("question_id,intent", [
    ("relationship_contact", "contact"),
    ("relationship_unblock", "unblock"),
    ("relationship_reconcile", "reconcile"),
    ("relationship_return", "return"),
])
def test_relationship_questions_use_seventh_house_fulfilment_module(question_id, intent):
    selected = resolve_guided_question(question_id)
    assert selected["topic"] == "relationship"
    assert selected["intent"] == intent
    assert {role["house"] for role in selected["roles"]} == {1, 7}


def test_will_this_person_marry_me_uses_specific_marriage_module():
    selected = resolve_guided_question("relationship_marriage")
    assert selected["topic"] == "marriage"
    assert selected["intent"] == "marriage"


def test_relationship_presentation_names_the_selected_outcome():
    from prashna.presenter import build_presentation
    result = PrashnaV2Calculator(chart()).calculate("relationship", "unblock")
    presentation = build_presentation(result)
    assert "contact being reopened" in presentation["heading"]
    assert result["coverage"]["declared_sections"] == ["I.25", "II.1", "II.3-4", "II.9", "II.13"]


def test_catalogue_exposes_every_guided_question_once():
    exposed = [question["id"] for topic in public_topics() for question in topic["questions"]]
    assert len(exposed) == len(set(exposed)) == len(GUIDED_QUESTIONS) == 20
    with pytest.raises(ValueError, match="supported Prashna questions"):
        resolve_guided_question("general_relationship")
