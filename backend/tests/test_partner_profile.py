from datetime import datetime, timedelta
from types import SimpleNamespace

from calculators.chart_calculator import ChartCalculator
from partner_profile.evidence_builder import build_partner_evidence
from partner_profile.prompt_builder import build_full_body_prompt, build_portrait_prompt
from partner_profile.routes import _progress_stage
from partner_profile.rules import PLANET_RULES, SIGN_RULES
from partner_profile.service import build_partner_profile
from partner_profile.synthesizer import synthesize_partner_profile


def _chart():
    birth = SimpleNamespace(
        name="Example",
        date="1980-04-02",
        time="14:55:00",
        latitude=29.2396596,
        longitude=75.8174505,
        timezone="UTC+5:30",
        place="Hisar, Haryana, India",
    )
    return ChartCalculator({}).calculate_chart(birth)


def test_partner_profile_resolves_d1_d9_and_source_trace():
    profile = build_partner_profile(_chart())

    assert profile["schema_version"] == "partner-profile/v1"
    assert profile["portrait_readiness"] == "ready"
    assert profile["evidence"]["d1"]["seventh_house"]["sign"]
    assert profile["evidence"]["d9"]["seventh_house"]["sign"]
    assert profile["evidence"]["d1"]["darakaraka"]["planet"]
    assert profile["appearance"]
    assert profile["factor_readings"]
    assert all(ref["work"] == "Brihat Parashara Hora Shastra" for ref in profile["references"])
    assert all((entry.get("primary") or {}).get("concept") for entry in profile["appearance"].values())

    seventh_sign = profile["evidence"]["d1"]["seventh_house"]["sign"]
    seventh_sign_reading = next(
        row for row in profile["factor_readings"]
        if row["channel"] == "d1_seventh_sign" and row["factor"] == seventh_sign
    )
    assert seventh_sign_reading["factor_type"] == "sign"
    assert seventh_sign_reading["appearance"]
    assert seventh_sign_reading["personality"]
    assert seventh_sign_reading["source_id"] == "bphs.rashi_forms"
    assert seventh_sign_reading["verse"]
    assert all(row["source_id"] and row["verse"] for row in profile["factor_readings"])


def test_classical_spouse_karaka_follows_native_gender():
    chart = _chart()
    female_profile = build_partner_profile(chart, native_gender="female")
    male_profile = build_partner_profile(chart, native_gender="male")

    assert female_profile["evidence"]["d1"]["spouse_karaka"]["planet"] == "Jupiter"
    assert male_profile["evidence"]["d1"]["spouse_karaka"]["planet"] == "Venus"
    assert any(
        row["channel"] == "spouse_karaka" and row["factor"] == "Jupiter"
        for row in female_profile["factor_readings"]
    )
    assert any(
        row["channel"] == "spouse_karaka" and row["factor"] == "Venus"
        for row in male_profile["factor_readings"]
    )


def test_partner_portrait_does_not_use_disputed_node_aspects():
    profile = build_partner_profile(_chart())
    assert "Rahu" not in profile["evidence"]["d1"]["seventh_house"]["aspecting_planets"]
    assert "Ketu" not in profile["evidence"]["d1"]["seventh_house"]["aspecting_planets"]
    assert "Rahu" not in profile["evidence"]["d9"]["seventh_house"]["aspecting_planets"]
    assert "Ketu" not in profile["evidence"]["d9"]["seventh_house"]["aspecting_planets"]


def test_image_prompt_uses_resolved_traits_without_identity_claims():
    profile = build_partner_profile(_chart())
    prompt = build_portrait_prompt(
        profile,
        presentation="feminine",
        age_band="25-34",
        clothing_style="contemporary",
        visual_context="european",
    )

    assert "Resolved visual archetype" in prompt
    assert "Do not infer caste" in prompt
    assert "not a photograph of a real or future person" in prompt
    assert "Example" not in prompt
    assert "1980-04-02" not in prompt
    assert "waist: slender" not in prompt  # one unconfirmed Darakaraka indication
    assert "European regional appearance" in prompt
    assert "Indian visual context" not in prompt
    assert "adult woman" in prompt
    assert "complexion:" in prompt
    assert "do not default a South Asian person to wheatish" in prompt

    body_prompt = build_full_body_prompt(
        profile,
        presentation="feminine",
        age_band="25-34",
        clothing_style="contemporary",
        visual_context="european",
    )
    assert "including body build" in body_prompt
    assert "artistic completion" in body_prompt
    assert "European regional appearance" in body_prompt
    assert "Preserve the reference portrait's complexion exactly" in body_prompt


def test_complexion_is_classical_evidence_not_a_regional_default():
    profile = {
        "appearance": {
            "complexion": {
                "primary": {
                    "value": "fair or light complexion",
                    "confidence": "suggestive",
                    "independent_repetitions": 1,
                    "evidence": [{"source_id": "bphs.graha_forms", "verse": "3.16"}],
                }
            }
        }
    }
    prompt = build_portrait_prompt(
        profile,
        presentation="feminine",
        age_band="25-34",
        clothing_style="contemporary",
        visual_context="south_asian",
    )

    assert "complexion: fair or light complexion" in prompt
    assert "South Asian regional appearance and setting" in prompt
    assert "Regional context must never determine, darken, lighten, or override skin tone" in prompt
    assert PLANET_RULES["Moon"]["appearance"]["complexion"] == "fair or light complexion"
    assert PLANET_RULES["Moon"]["appearance_verses"]["complexion"] == "3.16"
    assert PLANET_RULES["Jupiter"]["appearance_verses"]["complexion"] == "3.17"


def test_explicit_classical_hair_signal_reaches_image_prompt_without_fake_repetition():
    profile = {
        "appearance": {
            "hair": {
                "primary": {
                    "value": "curly hair",
                    "confidence": "suggestive",
                    "independent_repetitions": 1,
                    "evidence": [{"source_id": "bphs.graha_forms", "verse": "3.28"}],
                }
            },
            "build": {
                "primary": {
                    "value": "rounded and soft",
                    "confidence": "suggestive",
                    "independent_repetitions": 1,
                    "evidence": [{"source_id": "bphs.graha_forms", "verse": "3.24"}],
                }
            },
        }
    }
    prompt = build_portrait_prompt(
        profile,
        presentation="feminine",
        age_band="25-34",
        clothing_style="contemporary",
        visual_context="south_asian",
    )

    assert "hair: curly hair" in prompt
    assert "build: rounded and soft" not in prompt


def test_sun_hair_description_cannot_be_rendered_as_baldness():
    profile = {
        "appearance": {
            "head_hair": {
                "primary": {
                    "value": "less abundant hair",
                    "confidence": "suggestive",
                    "independent_repetitions": 1,
                    "evidence": [{"source_id": "bphs.graha_forms", "verse": "3.23"}],
                }
            }
        }
    }
    prompt = build_portrait_prompt(
        profile,
        presentation="feminine",
        age_band="25-34",
        clothing_style="contemporary",
        visual_context="south_asian",
    )

    assert "normal scalp coverage" in prompt
    assert "not bald, balding, shaved, or visibly hairless" in prompt
    assert PLANET_RULES["Sun"]["appearance"]["head_hair"] == "less abundant hair"
    assert "hair" not in PLANET_RULES["Sun"]["appearance"]
    assert SIGN_RULES["Scorpio"]["appearance"]["body_hair"] == "noticeable body hair"
    assert "head_hair" not in SIGN_RULES["Scorpio"]["appearance"]


def _jupiter_seventh_evidence(*, cancelled: bool) -> dict:
    jupiter = {
        "planet": "Jupiter",
        "sign": "Capricorn",
        "dignity": "debilitated",
        "neecha_bhanga": cancelled,
    }
    if cancelled:
        jupiter["neecha_bhanga_rules"] = ["PD_7_30_DEBILITATED_PLANET_KENDRA_FROM_LAGNA"]
        jupiter["neecha_bhanga_source"] = "Phaladeepika 7.26-30"
    return {
        "d1": {
            "seventh_house": {"sign": "Capricorn"},
            "seventh_house_occupants": [jupiter],
            "seventh_lord": {"planet": "Saturn", "sign": "Aquarius", "dignity": "own_sign"},
        },
        "d9": {"seventh_house": {"sign": "Leo"}},
    }


def _appearance_factors(profile: dict, attribute: str) -> set[str]:
    primary = ((profile.get("appearance") or {}).get(attribute) or {}).get("primary") or {}
    return {row.get("factor") for row in primary.get("evidence") or []}


def test_uncancelled_debilitation_does_not_supply_the_graha_form():
    profile = synthesize_partner_profile(_jupiter_seventh_evidence(cancelled=False))

    assert "Jupiter" not in _appearance_factors(profile, "complexion")
    assert "Jupiter" not in _appearance_factors(profile, "head_hair")
    assert all(row.get("factor") != "Jupiter" or row.get("withheld") for row in profile["factor_readings"])
    withheld = [row for row in profile["factor_readings"] if row.get("withheld")]
    assert withheld
    assert withheld[0]["verse"] == "45.5-6"
    assert any(
        row["channel"] == "d1_seventh_sign" and row["factor"] == "Capricorn" and row["appearance"]
        for row in profile["factor_readings"]
    )
    prompt = build_portrait_prompt(
        profile, presentation="feminine", age_band="25-34", clothing_style="contemporary",
    )
    assert "fair or light golden complexion" not in prompt
    assert "golden-brown hair" not in prompt


def test_chart_screen_neecha_bhanga_restores_the_graha_form():
    profile = synthesize_partner_profile(_jupiter_seventh_evidence(cancelled=True))

    assert "Jupiter" in _appearance_factors(profile, "complexion")
    jupiter = next(
        row for row in profile["factor_readings"]
        if row["factor"] == "Jupiter" and row["channel"] == "d1_occupant"
    )
    assert jupiter["condition_state"] == "debilitation_cancelled"
    assert jupiter["neecha_bhanga_rules"] == ["PD_7_30_DEBILITATED_PLANET_KENDRA_FROM_LAGNA"]
    assert any(ref["source_id"] == "phaladeepika.neecha_bhanga" for ref in profile["references"])


def test_uncancelled_debilitation_stays_false_and_is_not_copied_into_d9():
    from calculators.classical_neecha_bhanga import calculate_classical_neecha_bhanga
    from partner_profile.evidence_builder import _planet_row

    asc = 11  # Pisces. Saturn is debilitated in Aries, and the known placement has no cancellation.
    signs = {"Saturn": 0, "Mars": 0, "Moon": 11, "Sun": 0, "Venus": 1, "Mercury": 2, "Jupiter": 8}
    planets = {
        name: {"sign": sign, "house": ((sign - asc) % 12) + 1, "longitude": sign * 30 + 4}
        for name, sign in signs.items()
    }
    planets["Saturn"]["neecha_bhanga"] = True  # a stale flag must not override the classical result
    chart = {"ascendant": asc * 30 + 10, "planets": planets}
    results = calculate_classical_neecha_bhanga(chart)
    stamped = _planet_row(chart, "Saturn", neecha_results=results)
    untouched = _planet_row(chart, "Saturn")

    assert results["Saturn"]["neecha_bhanga_present"] is False
    assert stamped["dignity"] == "debilitated"
    assert stamped["neecha_bhanga"] is False
    assert "neecha_bhanga_rules" not in stamped
    assert "neecha_bhanga" not in untouched


def test_d1_evidence_uses_the_chart_screen_neecha_bhanga_rules():
    asc = 3  # Cancer, so the seventh house is Capricorn
    signs = {
        "Sun": 4, "Moon": 2, "Mars": 0, "Mercury": 2,
        "Jupiter": 9, "Venus": 1, "Saturn": 10, "Rahu": 5, "Ketu": 11,
    }
    planets = {
        name: {
            "sign": sign,
            "house": ((sign - asc) % 12) + 1,
            "longitude": sign * 30 + 8 + index,
            "dignity": "debilitated" if name == "Jupiter" else "neutral",
        }
        for index, (name, sign) in enumerate(signs.items())
    }
    chart = {
        "ascendant": asc * 30 + 5,
        "houses": [{"house_number": house, "sign": (asc + house - 1) % 12} for house in range(1, 13)],
        "planets": planets,
    }
    evidence = build_partner_evidence(chart, native_gender="male")
    jupiter = next(row for row in evidence["d1"]["seventh_house_occupants"] if row["planet"] == "Jupiter")

    assert jupiter["dignity"] == "debilitated"
    assert jupiter["neecha_bhanga"] is True
    assert "PD_7_30_DEBILITATED_PLANET_KENDRA_FROM_LAGNA" in jupiter["neecha_bhanga_rules"]
    assert jupiter["neecha_bhanga_source"] == "Phaladeepika 7.26-30"


def test_partner_portrait_progress_stages_follow_persisted_work():
    assert _progress_stage("pending") == "queued"
    assert _progress_stage("processing") == "reading_chart"
    assert _progress_stage("processing", started_at=datetime.now() - timedelta(seconds=6)) == "creating_portrait"
    assert _progress_stage("processing", '{"appearance": {}}') == "creating_portrait"
    assert _progress_stage(
        "processing",
        '{"appearance": {}}',
        '[{"kind": "portrait", "stored_uri": "private://portrait"}]',
    ) == "creating_full_body"
    assert _progress_stage("completed") == "ready"
