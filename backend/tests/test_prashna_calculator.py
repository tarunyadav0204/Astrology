from __future__ import annotations

from calculators.prashna_calculator import (
    PrashnaCalculator,
    infer_category,
    kp_sub_at_longitude,
    kp_sub_for_number,
    kp_vimshottari_subs,
)


SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def _planet(sign, degree, house, *, retrograde=False, speed=None, name=None):
    longitude = sign * 30 + degree
    row = {
        "longitude": longitude,
        "sign": sign,
        "sign_name": SIGN_NAMES[sign],
        "degree": degree,
        "house": house,
        "retrograde": retrograde,
    }
    if speed is not None:
        row["speed"] = speed
    if name:
        row["name"] = name
    return row


def _houses(asc_sign):
    return [
        {"sign": (asc_sign + i) % 12, "sign_name": SIGN_NAMES[(asc_sign + i) % 12], "longitude": ((asc_sign + i) % 12) * 30}
        for i in range(12)
    ]


def _chart(*, asc_sign=0, asc_degree=10.0, planets=None):
    bodies = planets or {}
    return {
        "ascendant": asc_sign * 30 + asc_degree,
        "houses": _houses(asc_sign),
        "planets": bodies,
    }


def test_infer_category_maps_marriage_and_career():
    assert infer_category("Will I get this job?")[1] == 10
    assert infer_category("Should we marry this year?", "marriage") == ("marriage", 7)


def test_house_lord_uses_zero_indexed_signs():
    # Aries lagna: 1st Mars, 10th Saturn. The old calculator did sign_num - 1.
    chart = _chart(
        asc_sign=0,
        planets={
            "Sun": _planet(4, 12, 5),
            "Moon": _planet(3, 8, 4, speed=13.0),
            "Mars": _planet(0, 14, 1, speed=0.5),
            "Mercury": _planet(2, 10, 3, speed=1.2),
            "Jupiter": _planet(8, 5, 9, speed=0.08),
            "Venus": _planet(1, 20, 2, speed=1.1),
            "Saturn": _planet(9, 18, 10, speed=0.03),
            "Rahu": _planet(5, 4, 6, speed=-0.05),
            "Ketu": _planet(11, 4, 12, speed=-0.05),
        },
    )
    calc = PrashnaCalculator(chart)
    assert calc.lagna_lord_name == "Mars"
    assert calc._house_lord_name(10) == "Saturn"
    result = calc.analyze("Will I get the promotion?", category="career")
    assert result["question"]["karya_house"] == 10
    assert result["significators"]["karyesha"]["planet"] == "Saturn"


def test_ithasala_applying_conjunction_uses_remaining_degrees():
    # Moon at 10° Aries applying to Saturn at 12° Aries.
    chart = _chart(
        planets={
            "Sun": _planet(4, 10, 5, speed=1.0),
            "Moon": _planet(0, 10, 1, speed=13.0),
            "Mars": _planet(0, 10, 1, speed=0.5),
            "Mercury": _planet(2, 4, 3, speed=1.2),
            "Jupiter": _planet(8, 2, 9, speed=0.08),
            "Venus": _planet(6, 8, 7, speed=1.1),
            "Saturn": _planet(0, 12, 1, speed=0.03),
            "Rahu": _planet(10, 6, 11, speed=-0.05),
            "Ketu": _planet(4, 6, 5, speed=-0.05),
        },
    )
    link = PrashnaCalculator(chart)._tajika_link(
        PrashnaCalculator(chart)._planet("Moon"),
        PrashnaCalculator(chart)._planet("Saturn"),
    )
    assert link["type"] == "Ithasala"
    assert link["aspect"] == "Conjunction"
    assert abs(link["remaining_degrees"] - 2.0) < 0.05


def test_retrograde_planet_can_still_apply():
    # Venus retrograde at 15° Taurus moving back toward Jupiter at 10° Taurus.
    # The old deg_fast < deg_slow test called this Easarpha.
    chart = _chart(
        planets={
            "Sun": _planet(4, 10, 5, speed=1.0),
            "Moon": _planet(3, 8, 4, speed=13.0),
            "Mars": _planet(0, 4, 1, speed=0.5),
            "Mercury": _planet(2, 6, 3, speed=1.2),
            "Jupiter": _planet(1, 10, 2, speed=0.08),
            "Venus": _planet(1, 15, 2, retrograde=True, speed=-1.2),
            "Saturn": _planet(9, 12, 10, speed=0.03),
            "Rahu": _planet(10, 6, 11, speed=-0.05),
            "Ketu": _planet(4, 6, 5, speed=-0.05),
        },
    )
    calc = PrashnaCalculator(chart)
    link = calc._tajika_link(calc._planet("Venus"), calc._planet("Jupiter"))
    assert link["type"] == "Ithasala"
    assert abs(link["remaining_degrees"] - 5.0) < 0.2


def test_lagna_sandhi_blocks_verdict():
    chart = _chart(
        asc_sign=0,
        asc_degree=0.2,
        planets={
            "Sun": _planet(4, 10, 5),
            "Moon": _planet(1, 12, 2, speed=13.0),
            "Mars": _planet(9, 8, 10, speed=0.5),
            "Mercury": _planet(2, 6, 3, speed=1.2),
            "Jupiter": _planet(8, 4, 9, speed=0.08),
            "Venus": _planet(6, 8, 7, speed=1.1),
            "Saturn": _planet(9, 14, 10, speed=0.03),
            "Rahu": _planet(10, 6, 11, speed=-0.05),
            "Ketu": _planet(4, 6, 5, speed=-0.05),
        },
    )
    result = PrashnaCalculator(chart).analyze("Will this work?", category="career")
    assert result["readable"] is False
    assert result["verdict"]["answer"] == "unclear"
    assert any(gate["id"] == "lagna_sandhi" and gate["status"] == "block" for gate in result["gates"])


def test_moon_in_eighth_is_a_warning_not_a_block():
    chart = _chart(
        planets={
            "Sun": _planet(4, 10, 5),
            "Moon": _planet(7, 12, 8, speed=13.0),
            "Mars": _planet(0, 14, 1, speed=0.5),
            "Mercury": _planet(2, 6, 3, speed=1.2),
            "Jupiter": _planet(8, 4, 9, speed=0.08),
            "Venus": _planet(6, 8, 7, speed=1.1),
            "Saturn": _planet(9, 14, 10, speed=0.03),
            "Rahu": _planet(10, 6, 11, speed=-0.05),
            "Ketu": _planet(4, 6, 5, speed=-0.05),
        },
    )
    result = PrashnaCalculator(chart).analyze("Will I get the job?", category="career")
    assert result["readable"] is True
    moon_gate = next(gate for gate in result["gates"] if gate["id"] == "moon_dusthana")
    assert moon_gate["status"] == "warn"


def test_easarpha_gives_no():
    # Moon already past Saturn — separating conjunction.
    chart = _chart(
        planets={
            "Sun": _planet(4, 10, 5, speed=1.0),
            "Moon": _planet(0, 14, 1, speed=13.0),
            "Mars": _planet(6, 8, 7, speed=0.5),
            "Mercury": _planet(2, 4, 3, speed=1.2),
            "Jupiter": _planet(8, 2, 9, speed=0.08),
            "Venus": _planet(6, 20, 7, speed=1.1),
            "Saturn": _planet(0, 12, 1, speed=0.03),
            "Rahu": _planet(10, 6, 11, speed=-0.05),
            "Ketu": _planet(4, 6, 5, speed=-0.05),
        },
    )
    calc = PrashnaCalculator(chart)
    result = calc.analyze("Will I get the job?", category="career")
    # Lagnesha Mars in 7, Karyesha Saturn in 1 — use direct moon-saturn as the yoga under test
    link = calc._tajika_link(calc._planet("Moon"), calc._planet("Saturn"))
    assert link["type"] == "Easarpha"
    assert result["chat_evidence"]["kind"] == "prashna"
    assert result["chat_evidence"]["clock"] == "question"


def test_kp_number_one_is_aswini_ketu_sub():
    subs = kp_vimshottari_subs()
    assert len(subs) == 243
    first = kp_sub_for_number(1)
    assert first["star_lord"] == "Ketu"
    assert first["sub_lord"] == "Ketu"
    assert first["start_longitude"] == 0
    wrapped = kp_sub_for_number(244)
    assert wrapped["wrapped"] is True
    assert wrapped["sub_lord"] == first["sub_lord"]
    at_zero = kp_sub_at_longitude(0.1)
    assert at_zero["sub_lord"] == "Ketu"


def test_kp_overlay_does_not_override_tajika_verdict():
    chart = _chart(
        asc_degree=10.0,
        planets={
            "Sun": _planet(4, 10, 5),
            "Moon": _planet(1, 12, 2, speed=13.0),
            "Mars": _planet(0, 14, 1, speed=0.5),
            "Mercury": _planet(2, 6, 3, speed=1.2),
            "Jupiter": _planet(8, 4, 9, speed=0.08),
            "Venus": _planet(6, 8, 7, speed=1.1),
            "Saturn": _planet(9, 14, 10, speed=0.03),
            "Rahu": _planet(10, 6, 11, speed=-0.05),
            "Ketu": _planet(4, 6, 5, speed=-0.05),
        },
    )
    without = PrashnaCalculator(chart).analyze("Will I get the job?", category="career")
    with_kp = PrashnaCalculator(chart).analyze("Will I get the job?", category="career", horary_number=17)
    assert with_kp["kp_overlay"]["school"] == "kp"
    assert with_kp["kp_overlay"]["number"] == 17
    assert with_kp["verdict"]["answer"] == without["verdict"]["answer"]
    assert any(layer["id"] == "kp" for layer in with_kp["layers"])


def test_explanation_for_no_ithasala_is_plain_language():
    # Libra lagna: Venus for the querent, Jupiter for house 6 (health).
    chart = _chart(
        asc_sign=6,
        asc_degree=9.6189,
        planets={
            "Sun": _planet(5, 10, 12, speed=1.0),
            "Moon": _planet(7, 11.3136, 2, speed=13.0),
            "Mars": _planet(4, 14, 11, speed=0.5),
            "Mercury": _planet(5, 6, 12, speed=1.2),
            "Jupiter": _planet(3, 22.757, 10, speed=0.08),
            "Venus": _planet(6, 9.777, 1, speed=1.1),
            "Saturn": _planet(10, 14, 5, speed=0.03),
            "Rahu": _planet(1, 6, 8, speed=-0.05),
            "Ketu": _planet(7, 6, 2, speed=-0.05),
        },
    )
    result = PrashnaCalculator(chart).analyze(
        "Will I recover?",
        category="health",
        horary_number=2,
    )
    explanation = result["explanation"]
    why = explanation["why"]
    assert explanation["headline"].startswith("No")
    assert explanation["confidence_label"] == "Tentative"
    assert "Lagnesha" not in why
    assert "Karyesha" not in why
    assert "Tajika" not in why
    assert "Confidence" not in explanation["headline"]
    assert "Venus" in why
    assert "Jupiter" in why
    assert "moving toward" in why.lower()
    assert "you" in explanation["you"]["body"].lower()
    assert "health" in explanation["matter"]["body"].lower()
    assert result["kp_overlay"]["number"] == 2
    assert "override" in (explanation["kp"] or "").lower()
