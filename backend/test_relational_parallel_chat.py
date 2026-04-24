from ai.parallel_chat.config import should_use_parallel_relational_chat
from ai.parallel_chat.relational_payloads import (
    build_relational_branch_payloads,
    build_relational_evidence_spine,
    build_relationship_profile,
)
from ai.parallel_chat.relational_orchestrator import _enabled_relational_branches
from ai.parallel_chat.relational_prompt_blocks import (
    build_relational_branch_static,
    build_relational_merge_static,
)


def _synastry_context():
    return {
        "analysis_type": "synastry",
        "relationship": {"raw_label": "Guru & Disciple"},
        "native": {"birth_details": {"name": "Native"}},
        "partner": {"birth_details": {"name": "Partner"}},
    }


def _chart_context(name, asc_sign, planet_rows, current_lords=None):
    return {
        "birth_details": {"name": name},
        "ascendant_info": {"sign_number": asc_sign + 1},
        "d1_chart": {
            "ascendant": asc_sign * 30.0,
            "houses": [{"sign": (asc_sign + i) % 12} for i in range(12)],
            "planets": planet_rows,
        },
        "divisional_charts": {
            "d9_navamsa": {
                "ascendant": ((asc_sign + 2) % 12) * 30.0,
                "houses": [{"sign": ((asc_sign + 2) + i) % 12} for i in range(12)],
                "planets": {
                    planet: {
                        "sign": (data["sign"] + 2) % 12 if isinstance(data.get("sign"), int) else data.get("sign"),
                        "house": ((data["house"] + 1) % 12) + 1 if isinstance(data.get("house"), int) else data.get("house"),
                        "longitude": (data["longitude"] + 60) % 360 if isinstance(data.get("longitude"), (int, float)) else data.get("longitude"),
                    }
                    for planet, data in planet_rows.items()
                },
            }
        },
        "ashtakavarga": {
            "d1_rashi": {
                "sarvashtakavarga": {str(i): 25 + (i % 4) for i in range(12)},
            }
        },
        "sudarshana_chakra": {
            "lagna_chart": {"Sun": 10, "Moon": 7, "Mars": 6},
            "chandra_lagna": {"Sun": 4, "Moon": 1, "Mars": 12},
            "surya_lagna": {"Sun": 1, "Moon": 10, "Mars": 9},
            "synthesis": {"patterns": ["test_pattern"]},
        },
        "sudarshana_dasha": {
            "active_house": 7,
            "year_focus": "relationship",
            "precision_triggers": [{"date": "2026-05-01", "planet": "Venus", "confirmation": "2/3", "confidence": "medium", "intensity": "moderate", "sign": "Libra", "perspectives": ["lagna", "moon"]}],
        },
        "current_dashas": {
            "mahadasha": {"planet": (current_lords or ["Jupiter"])[0]},
            "antardasha": {"planet": (current_lords or ["Jupiter", "Saturn"])[1]},
        },
        "kp_analysis": {
            "cusp_lords": {
                "2": {"sign_lord": "Venus", "star_lord": "Moon", "sub_lord": "Saturn"},
                "6": {"sign_lord": "Mercury", "star_lord": "Mars", "sub_lord": "Rahu"},
                "7": {"sign_lord": "Venus", "star_lord": "Rahu", "sub_lord": "Saturn"},
                "8": {"sign_lord": "Mars", "star_lord": "Saturn", "sub_lord": "Ketu"},
                "12": {"sign_lord": "Jupiter", "star_lord": "Saturn", "sub_lord": "Mars"},
            },
            "significators": {
                "2": ["Venus", "Rahu"],
                "6": ["Mars", "Saturn"],
                "7": ["Venus", "Saturn"],
                "8": ["Rahu", "Ketu"],
                "12": ["Saturn", "Mars"],
            },
            "planet_significators": {
                "Venus": [2, 7],
                "Saturn": [6, 7, 12],
                "Rahu": [6, 8],
                "Mars": [6, 12],
                "Ketu": [8],
            },
            "four_step_theory": {
                "Venus": {
                    "planet": {"name": "Venus", "houses": [2, 7]},
                    "star_lord": {"name": "Rahu", "houses": [6, 8]},
                    "sub_lord": {"name": "Saturn", "houses": [6, 7, 12]},
                    "sub_sub_lord": {"name": "Mars", "houses": [6, 12]},
                },
                "Saturn": {
                    "planet": {"name": "Saturn", "houses": [6, 7, 12]},
                    "star_lord": {"name": "Mars", "houses": [6, 12]},
                    "sub_lord": {"name": "Rahu", "houses": [6, 8]},
                    "sub_sub_lord": {"name": "Venus", "houses": [2, 7]},
                },
                "Rahu": {
                    "planet": {"name": "Rahu", "houses": [6, 8]},
                    "star_lord": {"name": "Saturn", "houses": [6, 7, 12]},
                    "sub_lord": {"name": "Mars", "houses": [6, 12]},
                    "sub_sub_lord": {"name": "Venus", "houses": [2, 7]},
                },
            },
        },
    }


def _full_synastry_context():
    native = _chart_context(
        "Native",
        0,
        {
            "Moon": {"sign": 0, "house": 1, "longitude": 10},
            "Venus": {"sign": 6, "house": 7, "longitude": 190},
            "Mars": {"sign": 11, "house": 12, "longitude": 350},
            "Jupiter": {"sign": 8, "house": 9, "longitude": 250},
            "Saturn": {"sign": 11, "house": 12, "longitude": 340},
            "Rahu": {"sign": 1, "house": 2, "longitude": 40},
            "Ketu": {"sign": 7, "house": 8, "longitude": 220},
            "Mercury": {"sign": 2, "house": 3, "longitude": 70},
            "Sun": {"sign": 4, "house": 5, "longitude": 130},
        },
        ["Venus", "Saturn"],
    )
    native["divisional_charts"]["d9_navamsa"]["planets"]["Venus"]["sign"] = native["d1_chart"]["planets"]["Venus"]["sign"]
    native["divisional_charts"]["d9_navamsa"]["planets"]["Venus"]["house"] = 7
    partner = _chart_context(
        "Partner",
        6,
        {
            "Moon": {"sign": 0, "house": 7, "longitude": 12},
            "Venus": {"sign": 1, "house": 8, "longitude": 42},
            "Mars": {"sign": 6, "house": 1, "longitude": 192},
            "Jupiter": {"sign": 8, "house": 3, "longitude": 252},
            "Saturn": {"sign": 11, "house": 6, "longitude": 342},
            "Rahu": {"sign": 1, "house": 8, "longitude": 44},
            "Ketu": {"sign": 7, "house": 2, "longitude": 224},
            "Mercury": {"sign": 5, "house": 12, "longitude": 160},
            "Sun": {"sign": 9, "house": 4, "longitude": 280},
        },
        ["Saturn", "Rahu"],
    )
    partner["divisional_charts"]["d9_navamsa"]["planets"]["Moon"]["sign"] = partner["d1_chart"]["planets"]["Moon"]["sign"]
    partner["divisional_charts"]["d9_navamsa"]["planets"]["Moon"]["house"] = 7
    return {
        "analysis_type": "synastry",
        "relationship": {"raw_label": "Husband & Wife"},
        "native": native,
        "partner": partner,
    }


def test_relational_parallel_requires_flag(monkeypatch):
    monkeypatch.delenv("ASTRO_PARALLEL_RELATIONAL_CHAT", raising=False)
    monkeypatch.delenv("ASTRO_PARALLEL_CHAT_USER_IDS", raising=False)

    assert should_use_parallel_relational_chat(_synastry_context(), user_id=1) is False


def test_relational_parallel_uses_shared_allowlist(monkeypatch):
    monkeypatch.setenv("ASTRO_PARALLEL_RELATIONAL_CHAT", "1")
    monkeypatch.setenv("ASTRO_PARALLEL_CHAT_USER_IDS", "42,100")

    assert should_use_parallel_relational_chat(_synastry_context(), user_id=42) is True
    assert should_use_parallel_relational_chat(_synastry_context(), user_id=41) is False


def test_relationship_profile_preserves_relation_and_event():
    context = {
        "relationship": {"raw_label": "Guru & Disciple"},
    }

    profile = build_relationship_profile(context, "Is this guru good for my spiritual learning?")

    assert profile["raw_label"] == "Guru & Disciple"
    assert profile["relation_family"] == "guru_disciple"
    assert profile["event_topic"] == "support_guidance"
    assert 9 in profile["primary_houses"]
    assert "Jupiter" in profile["primary_karakas"]


def test_relationship_profile_handles_event_specific_spouse_question():
    context = {
        "relationship": {"raw_label": "Husband & Wife"},
    }

    profile = build_relationship_profile(context, "Will my wife go to jail?")

    assert profile["relation_family"] == "spouse_romantic"
    assert profile["event_topic"] == "legal_confinement"
    assert profile["question_mode"] == "predictive_yes_no"
    assert profile["answer_policy"]["do_not_force_compatibility_sections"] is True
    assert profile["native_role_house"] == 7
    assert profile["derived_event_houses_from_role"] == {
        "6_from_role": 12,
        "8_from_role": 2,
        "12_from_role": 6,
    }


def test_relationship_profile_infers_day_level_timing_request():
    profile = build_relationship_profile(
        {"relationship": {"raw_label": "Husband & Wife"}},
        "Will she come back tomorrow?",
    )

    assert profile["timing_request"]["requested_granularity"] == "day"


def test_relationship_profile_handles_messy_infidelity_language():
    context = {
        "relationship": {"raw_label": "Husband & Wife"},
    }

    profile = build_relationship_profile(context, "My cheating whife, when will she be betryade by their lover?")

    assert profile["relation_family"] == "spouse_romantic"
    assert profile["event_topic"] == "trust_infidelity"
    assert profile["answer_policy"]["state_limits_for_fact_claims"] is True


def test_relationship_profile_expanded_event_taxonomy():
    cases = [
        ("Business Partner", "Did my business partner commit fraud?", "business_betrayal"),
        ("Guru & Disciple", "Is this a fake guru or spiritual fraud?", "guru_trust_breach"),
        ("Mother & Son", "Why are my son and I estranged and not talking?", "parent_child_estrangement"),
        ("Brother & Sister", "Will this brother dispute end?", "sibling_conflict"),
        ("Husband & Wife", "Will my mother in law create in-law problems?", "in_law_friction"),
        ("Husband & Wife", "My partner is violent and I feel unsafe", "abuse_safety"),
        ("Husband & Wife", "Will she come back and reconcile?", "reconciliation_return"),
    ]

    for relation, question, expected_topic in cases:
        profile = build_relationship_profile({"relationship": {"raw_label": relation}}, question)
        assert profile["event_topic"] == expected_topic


def test_relational_evidence_spine_computes_role_event_and_cross_contacts():
    spine = build_relational_evidence_spine(_full_synastry_context(), "Will my wife go to jail?")

    assert spine["profile"]["event_topic"] == "legal_confinement"
    assert spine["native_role_house"]["house"] == 7
    assert [row["label"] for row in spine["native_derived_event_houses"]] == [
        "6_from_role",
        "8_from_role",
        "12_from_role",
    ]
    assert [row["house"] for row in spine["native_derived_event_houses"]] == [12, 2, 6]
    assert [row["label"] for row in spine["partner_event_houses"]] == [
        "partner_6",
        "partner_8",
        "partner_12",
    ]
    assert [row["house"] for row in spine["partner_event_houses"]] == [6, 8, 12]
    assert any(
        c["native_planet"] == "Moon"
        and c["partner_planet"] == "Moon"
        and c["relation"] == "same_sign"
        for c in spine["cross_chart_contacts"]
    )
    assert spine["cross_chart_contact_summary"]["total"] > 0
    assert spine["cross_chart_contact_summary"]["nodal"] > 0
    assert spine["cross_chart_contact_summary"]["weighted_support"] > 0
    assert spine["mutual_overlays"]["lagna_to_lagna"]["relation"] == "opposition"
    assert spine["mutual_overlays"]["native_7th_to_partner_lagna"]["relation"] == "same_sign"
    assert spine["mutual_overlays"]["spouse_axis_detail"]["partner_lagna_in_native_chart_house"] == 7
    assert spine["mutual_overlays"]["spouse_axis_detail"]["native_lagna_in_partner_chart_house"] == 7
    assert spine["mutual_overlays"]["navamsa_d9"]["available"] is True
    assert spine["mutual_overlays"]["navamsa_d9"]["native_d9_lagna_to_partner_d9_lagna"]["relation"] == "opposition"
    assert any(
        row["planet"] == "Saturn" and row["target_house"] == 12
        for row in spine["mutual_overlays"]["partner_planets_in_native_focus_houses"]
    )
    assert any(
        row["planet"] == "Venus" and row["target_house"] == 2
        for row in spine["mutual_overlays"]["navamsa_d9"]["partner_d9_planets_in_native_d9_focus"]
    )
    assert spine["timing_alignment"]["one_active"] is True
    assert spine["timing_alignment"]["native"]["current_stack"][0]["level"] == "MD"
    assert spine["timing_alignment"]["native"]["current_stack"][1]["level"] == "AD"
    assert spine["branch_activation"]["kp_relational"]["priority"] == "primary"
    assert spine["branch_activation"]["kp_relational"]["data_available"] is True
    assert spine["kp_relational_cusps"]["available"] is True
    assert spine["kp_relational_cusps"]["native_targets"][0]["label"] == "native_role_cusp"
    assert spine["kp_relational_cusps"]["native_targets"][0]["cusp_lords"]["sub_lord"] == "Saturn"
    assert spine["kp_relational_cusps"]["native_four_step_trigger"]["dasha_lords"] == ["Venus", "Saturn"]
    assert spine["kp_relational_cusps"]["native_four_step_trigger"]["active_trigger_planets"]
    assert spine["kp_relational_cusps"]["native_four_step_trigger"]["strongest_trigger_planets"][0]["planet"] in {"Venus", "Saturn"}
    first_target = spine["kp_relational_cusps"]["native_four_step_trigger"]["targets"][0]
    assert first_target["candidates"][0]["step_hit_count"] > 0
    assert spine["kuta_compatibility"]["available"] is True
    assert spine["kuta_compatibility"]["max_score"] == 36
    assert spine["branch_activation"]["ashtakoota_relational"]["priority"] == "primary"
    assert spine["ashtakavarga_relational_evidence"]["available"] is True
    assert spine["ashtakavarga_relational_evidence"]["focus_houses"] == [2, 5, 6, 7, 8, 12]
    assert spine["ashtakavarga_relational_evidence"]["native"]["rows"]
    assert spine["ashtakavarga_relational_evidence"]["partner"]["rows"]
    assert all(isinstance(row["sav"], int) for row in spine["ashtakavarga_relational_evidence"]["native"]["rows"])
    assert all(isinstance(row["sav"], int) for row in spine["ashtakavarga_relational_evidence"]["partner"]["rows"])
    assert spine["ashtakavarga_relational_evidence"]["comparative"]["support"] in {
        "both_supportive",
        "native_supportive_partner_mixed",
        "partner_supportive_native_mixed",
        "mixed_or_weak",
    }
    assert spine["sudarshana_relational_evidence"]["available"] is True
    assert spine["sudarshana_relational_evidence"]["focus_category"] == "relationship"
    assert spine["sudarshana_relational_evidence"]["native"]["rows"]
    assert spine["sudarshana_relational_evidence"]["partner"]["rows"]
    assert isinstance(spine["sudarshana_relational_evidence"]["native"]["triggers"], list)
    assert isinstance(spine["sudarshana_relational_evidence"]["partner"]["triggers"], list)
    assert spine["d1_d9_confirmation"]["native_confirmed_count"] > 0
    assert spine["d1_d9_confirmation"]["partner_confirmed_count"] > 0
    assert spine["relationship_vargottama"]["native_count"] > 0
    assert spine["relationship_vargottama"]["partner_count"] > 0
    assert spine["relationship_tone_summary"]["bond_score"] > 0
    assert spine["relationship_tone_summary"]["tone"] in {
        "bond_dominant",
        "bond_with_pressure",
        "mixed_unstable",
        "pressure_volatility_dominant",
    }
    spouse = spine["relation_specific_evidence"]
    assert spouse["sign_flavor_native"]
    assert spouse["sign_flavor_partner"]
    assert any(row["house"] == 2 and row["sign_flavor"] for row in spouse["sign_flavor_native"])
    assert spouse["nakshatra_flavor_native"]["moon"]["nakshatra"]
    assert spouse["nakshatra_flavor_partner"]["moon"]["nakshatra"]
    assert spouse["nakshatra_flavor_native"]["relationship_planets"]
    assert spouse["nakshatra_flavor_partner"]["relationship_planets"]
    moon_moon = next(c for c in spine["cross_chart_contacts"] if c["native_planet"] == "Moon" and c["partner_planet"] == "Moon")
    assert moon_moon["strength_score"] >= 5
    assert moon_moon["strength_band"] == "very_supportive"


def test_relational_timing_strategy_degrades_precision_to_available_level():
    context = _full_synastry_context()
    context["native"]["period_dasha_activations"] = {
        "period_type": "monthly",
        "start_date": "2026-05-01",
        "end_date": "2026-05-31",
        "sampled_activations": [
            {"date": "2026-05-03", "activations": [{"planet": "Venus"}, {"planet": "Saturn"}]},
        ],
        "analysis_depth": "medium",
    }
    context["native"]["transit_activations"] = [
        {
            "transit_planet": "Venus",
            "natal_planet": "Moon",
            "transit_house": 7,
            "start_date": "2026-05-02",
            "end_date": "2026-05-18",
            "dasha_significance": "supportive",
        }
    ]
    spine = build_relational_evidence_spine(context, "Will she come back tomorrow?")

    assert spine["timing_strategy"]["requested_granularity"] == "day"
    assert spine["timing_strategy"]["delivery_granularity"] == "month"
    assert spine["timing_strategy"]["native"]["period_dasha"]["available"] is True
    assert spine["timing_strategy"]["native"]["transit_windows"]["available"] is True
    assert spine["timing_strategy"]["native"]["transit_windows"]["rows"][0]["transit_house"] == 7


def test_relational_branch_payloads_include_evidence_spine_for_every_method():
    payloads = build_relational_branch_payloads(_full_synastry_context(), "Will my wife go to jail?")

    assert set(payloads) == {
        "parashari_relational",
        "jaimini_relational",
        "nadi_relational",
        "kp_relational",
        "nakshatra_relational",
        "timing_relational",
        "ashtakavarga_relational",
        "sudarshan_relational",
    }
    for payload in payloads.values():
        assert payload["relational_evidence"]["profile"]["event_topic"] == "legal_confinement"
        assert payload["relational_evidence"]["native_role_house"]["house"] == 7
        assert payload["relational_evidence"]["branch_activation"]["parashari_relational"]["priority"] == "primary"
        assert payload["relational_evidence"]["relation_specific_evidence"]["family"] == "spouse_romantic"


def test_relational_merge_prompt_blocks_irrelevant_sections_for_events():
    prompt = build_relational_merge_static("english")

    assert "Never include generic sections" in prompt
    assert "Overall Compatibility" in prompt
    assert "event questions about jail, cheating, betrayal" in prompt
    assert "never present astrology as proof" in prompt
    assert "branch_activation marks a method as skipped" in prompt
    assert "Ashtakoota/Guna Milan" in prompt
    assert "relation_specific_evidence" in prompt
    assert "Method Cross-Checks" in prompt
    assert "concrete numbers from SAV/BAV rows" in prompt
    assert "If Jaimini or Nadi materially contributed, name them explicitly" in prompt
    assert "sign_flavor_*" in prompt
    assert "nakshatra_flavor_*" in prompt
    assert "timing_strategy" in prompt
    assert "deliverable granularity" in prompt
    assert "do not stop at Mahadasha" in prompt
    assert "MD + AD" in prompt


def test_relational_branch_prompts_require_explicit_method_reasoning():
    jaimini = build_relational_branch_static("jaimini_relational")
    nadi = build_relational_branch_static("nadi_relational")
    av = build_relational_branch_static("ashtakavarga_relational")
    sx = build_relational_branch_static("sudarshan_relational")

    assert "Static Promise, Current Timing, Manifestation Filter" in jaimini
    assert "UL and A7" in jaimini
    assert "dominant graha(s) -> linkage web -> topic meaning -> activation/timing -> verdict" in nadi
    assert "Nakshatra is a primary interpretive layer here" in build_relational_branch_static("nakshatra_relational")
    assert "cite actual SAV values and relevant planet BAV values" in av
    assert "Lagna, Moon, and Sun perspectives agree 3/3, 2/3, or are mixed" in sx


def test_enabled_relational_branches_include_optional_methods_when_data_exists():
    spine = build_relational_evidence_spine(_full_synastry_context(), "Will my wife go to jail?")
    enabled = _enabled_relational_branches(spine)

    assert "ashtakavarga_relational" in enabled
    assert "sudarshan_relational" in enabled


def test_enabled_relational_branches_skip_low_relevance_core_branches():
    spine = build_relational_evidence_spine(_full_synastry_context(), "Tell me in detail what is Taruns behaviour towards Deepika and Deepika's behaviour about Tarun")
    enabled = _enabled_relational_branches(spine)

    assert "parashari_relational" in enabled
    assert "nakshatra_relational" in enabled
    assert "jaimini_relational" in enabled
    assert "timing_relational" not in enabled


def test_enabled_relational_branches_skip_optional_methods_without_data():
    context = _full_synastry_context()
    context["native"].pop("ashtakavarga", None)
    context["partner"].pop("ashtakavarga", None)
    context["native"].pop("sudarshana_chakra", None)
    context["native"].pop("sudarshana_dasha", None)
    context["partner"].pop("sudarshana_chakra", None)
    context["partner"].pop("sudarshana_dasha", None)

    spine = build_relational_evidence_spine(context, "Will my wife go to jail?")
    enabled = _enabled_relational_branches(spine)

    assert "ashtakavarga_relational" not in enabled
    assert "sudarshan_relational" not in enabled


def test_relational_optional_evidence_reports_missing_data_cleanly():
    context = _full_synastry_context()
    context["native"].pop("ashtakavarga", None)
    context["partner"].pop("ashtakavarga", None)
    context["native"].pop("sudarshana_chakra", None)
    context["native"].pop("sudarshana_dasha", None)
    context["partner"].pop("sudarshana_chakra", None)
    context["partner"].pop("sudarshana_dasha", None)

    spine = build_relational_evidence_spine(context, "Will my wife go to jail?")

    assert spine["ashtakavarga_relational_evidence"]["available"] is False
    assert "missing" in spine["ashtakavarga_relational_evidence"]["reason"].lower()
    assert spine["sudarshana_relational_evidence"]["available"] is False
    assert "missing" in spine["sudarshana_relational_evidence"]["reason"].lower()


def test_relational_ashtakavarga_prompt_requires_no_fabricated_numbers():
    av = build_relational_branch_static("ashtakavarga_relational")
    merge = build_relational_merge_static("english")

    assert "do not invent numbers" in av
    assert "numeric Ashtakavarga support is unavailable" in av
    assert "If SAV/BAV numbers are unavailable, do not fabricate them" in merge


def test_relation_specific_evidence_for_non_romantic_families():
    cases = [
        (
            "Guru & Disciple",
            "Is this guru good for my spiritual learning?",
            "teaching_guidance_axis",
            "native_learning_houses",
        ),
        (
            "Business Partner",
            "Did my business partner commit fraud?",
            "work_trust_hierarchy_axis",
            "native_business_houses",
        ),
        (
            "Mother & Son",
            "Why are my son and I estranged and not talking?",
            "caregiving_authority_axis",
            "native_family_houses",
        ),
        (
            "Brother & Sister",
            "Will this brother dispute end?",
            "support_rivalry_axis",
            "native_sibling_houses",
        ),
        (
            "Friend & Friend",
            "Did my friend betray my secret?",
            "trust_network_axis",
            "native_social_houses",
        ),
    ]

    for relation, question, focus, key in cases:
        context = _full_synastry_context()
        context["relationship"]["raw_label"] = relation
        spine = build_relational_evidence_spine(context, question)
        block = spine["relation_specific_evidence"]
        assert block["focus"] == focus
        assert block[key]
        assert "overlay_focus" in block


def test_in_law_question_uses_spouse_specific_block_with_in_law_topic():
    context = _full_synastry_context()
    spine = build_relational_evidence_spine(context, "Will my mother in law create in-law problems?")

    assert spine["profile"]["event_topic"] == "in_law_friction"
    assert spine["relation_specific_evidence"]["focus"] == "spouse_axis"
