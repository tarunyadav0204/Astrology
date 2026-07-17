"""Tests for lifespan dasha spines + deterministic timing evidence pack."""

from datetime import datetime

from shared.dasha_calculator import DashaCalculator
from chat.lifespan_timing_evidence import (
    _build_candidate_windows,
    _double_transit_cite_instruction,
    _double_transit_status,
    build_lifespan_timing_evidence,
    compact_lifespan_timing_evidence_for_prompt,
    force_divisional_codes_for_lifespan,
    is_promotion_topic,
    topic_spec_for_family,
    topic_spec_for_key,
)
from ai.prediction_anchor import career_timing_prompt_for_topic, infer_topic_key
from ai.prediction_anchor import (
    build_anchor_from_lifespan_evidence,
    enrich_anchor_fingerprint_from_pack,
    merge_anchor_candidates,
)


BIRTH = {
    "name": "Test Native",
    "date": "1998-07-15",
    "time": "10:30",
    "latitude": 28.6139,
    "longitude": 77.2090,
    "place": "New Delhi",
    "timezone": 5.5,
}


def test_ad_spine_covers_ketu_venus_sun_through_2051():
    calc = DashaCalculator()
    ads = calc.iter_ad_periods(BIRTH, datetime(2016, 1, 1), datetime(2051, 12, 31))
    assert ads, "AD spine should not be empty"
    assert ads[0]["start_date"] <= "2016-12-31"
    assert ads[-1]["end_date"] >= "2030-01-01"
    chains = {(r["mahadasha"], r["antardasha"]) for r in ads}
    assert ("Ketu", "Venus") in chains
    assert ("Ketu", "Sun") in chains
    # Must extend past the old ~2023 truncation
    assert any(r["start_date"] >= "2025-01-01" for r in ads)


def test_pd_near_includes_mercury_pd_aug_oct_2026():
    calc = DashaCalculator()
    pds = calc.iter_pd_periods(BIRTH, datetime(2025, 1, 1), datetime(2027, 12, 31))
    mercury = [
        r
        for r in pds
        if r.get("mahadasha") == "Ketu"
        and r.get("antardasha") == "Venus"
        and r.get("pratyantardasha") == "Mercury"
    ]
    assert mercury, "Expected Ketu-Venus-Mercury PD in near band"
    m = mercury[0]
    assert m["start_date"] <= "2026-08-15"
    assert m["end_date"] >= "2026-09-01"


def test_get_dasha_periods_for_range_covers_full_requested_span():
    """Real PD ends yield fewer rows than the old 30-day probe, but must reach end_date."""
    calc = DashaCalculator()
    rows = calc.get_dasha_periods_for_range(
        BIRTH, datetime(2016, 1, 1), datetime(2032, 12, 31)
    )
    assert rows
    assert rows[0]["start_date"] <= "2016-12-31"
    assert rows[-1]["end_date"] >= "2032-01-01"
    assert not rows[-1].get("_truncated")
    # Must include post-2023 Ketu MD (old 100×30d trap stopped ~2023)
    assert any(r.get("mahadasha") == "Ketu" for r in rows)


def test_force_divisionals_career_on_timing_category():
    codes = force_divisional_codes_for_lifespan(
        mode="LIFESPAN_EVENT_TIMING",
        category="timing",
        question="When will I get my first job?",
        existing=["D1", "D9"],
    )
    assert "D10" in codes
    marriage = force_divisional_codes_for_lifespan(
        mode="LIFESPAN_EVENT_TIMING",
        category="general",
        question="When will I get married?",
        existing=["D1", "D9"],
    )
    assert "D9" in marriage
    assert "D7" in marriage


def test_topic_spec_split_career_vs_marriage():
    career = topic_spec_for_family("career")
    marriage = topic_spec_for_family("marriage")
    assert 10 in career["primary_houses"]
    assert 7 in marriage["primary_houses"]
    assert "D10" in career["divisionals"]
    assert "D7" in marriage["divisionals"]


def test_promotion_spec_differs_from_first_job():
    job = topic_spec_for_key("career_first_job", family="career")
    promo = topic_spec_for_key("career_promotion", family="career", category="promotion")
    assert job["primary_houses"] == [10, 6, 2, 11]
    assert promo["primary_houses"] == [10, 11, 2]
    assert 6 not in promo["primary_houses"]
    assert 6 in (promo.get("support_houses") or [])
    assert promo["ranking_bias"] == "promotion"
    assert is_promotion_topic("career_promotion", category="promotion")
    assert infer_topic_key("When will I get a promotion?") == "career_promotion"
    promo_prompt = career_timing_prompt_for_topic(
        "career_promotion", category="promotion", question="When will I get a promotion?"
    )
    job_prompt = career_timing_prompt_for_topic(
        "career_first_job", category="career", question="When will I get my first job?"
    )
    assert "Visibility" in promo_prompt
    assert "Formalization" in promo_prompt
    assert "Activation = more calls" not in promo_prompt
    assert "Activation = more calls" in job_prompt
    assert "Settle" in promo_prompt


def test_pack_dt_none_caps_confidence(monkeypatch=None):
    """Build a minimal pack-like context where DT is none → ceiling != high."""
    pack = build_lifespan_timing_evidence(
        {
            "timing_focus": {
                "focus_date": datetime(2026, 7, 1),
                "judgment_year": 2026,
                "scan_start_year": 2016,
                "scan_end_year": 2051,
                "open_ended_lifespan": True,
                "mode": "LIFESPAN_EVENT_TIMING",
            },
            "intent": {
                "mode": "LIFESPAN_EVENT_TIMING",
                "category": "career",
                "transit_request": {"startYear": 2016, "endYear": 2051},
            },
            "ascendant_info": {"sign_id": 5},
            "planetary_analysis": {
                "Mercury": {
                    "basic_info": {
                        "planet": "Mercury",
                        "house": 11,
                        "sign": 3,
                        "sign_name": "Cancer",
                        "avastha": "Bal (Infant)",
                    },
                    "dignity_analysis": {"dignity": "neutral"},
                    "combustion_status": {"is_combust": False},
                },
                "Venus": {
                    "basic_info": {
                        "planet": "Venus",
                        "house": 10,
                        "sign": 2,
                        "sign_name": "Gemini",
                        "avastha": "Bal (Infant)",
                    },
                    "dignity_analysis": {"dignity": "neutral"},
                    "combustion_status": {"is_combust": False},
                },
                "Saturn": {
                    "basic_info": {
                        "planet": "Saturn",
                        "house": 8,
                        "sign": 0,
                        "sign_name": "Aries",
                        "avastha": "Yuva",
                    },
                    "dignity_analysis": {"dignity": "debilitated"},
                    "combustion_status": {"is_combust": False},
                },
            },
            "macro_transits_timeline": {
                # Saturn in 7th, Jupiter in 11th — partial at best for career 10th;
                # force none by empty houses for a stricter unit check via empty macro.
            },
            "current_dashas": {
                "mahadasha": {"planet": "Ketu", "start": "2025-04-04", "end": "2032-04-04"},
                "antardasha": {"planet": "Venus", "start": "2025-08-31", "end": "2026-10-31"},
                "pratyantardasha": {"planet": "Mercury"},
            },
            "requested_dasha_summary": {
                "ad_spine": [
                    {
                        "start_date": "2025-08-31",
                        "end_date": "2026-10-31",
                        "mahadasha": "Ketu",
                        "antardasha": "Venus",
                        "ad_start": "2025-08-31",
                        "ad_end": "2026-10-31",
                    },
                    {
                        "start_date": "2026-10-31",
                        "end_date": "2027-03-08",
                        "mahadasha": "Ketu",
                        "antardasha": "Sun",
                        "ad_start": "2026-10-31",
                        "ad_end": "2027-03-08",
                    },
                ],
                "pd_near_band": {
                    "periods": [
                        {
                            "start_date": "2026-08-06",
                            "end_date": "2026-10-06",
                            "mahadasha": "Ketu",
                            "antardasha": "Venus",
                            "pratyantardasha": "Mercury",
                        }
                    ]
                },
                "period_coverage_actual": "2016-01-01→2051-12-31",
                "truncated": False,
            },
            "divisional_charts": {
                "d10_dasamsa": {
                    "divisional_chart": {
                        "ascendant": 48.0,
                        "planets": {
                            "Mercury": {
                                "sign_name": "Scorpio",
                                "house": 7,
                                "dignity": "neutral",
                            }
                        },
                    }
                }
            },
            "chara_dasha": {"periods": []},
            "chara_karakas": {
                "chara_karakas": {
                    "Amatyakaraka": {"planet": "Mercury", "sign": 3},
                }
            },
            "kp_analysis": {
                "planet_significators": {
                    "Mercury": [1, 2, 10, 11],
                    "Venus": [3, 9, 10],
                    "Ketu": [6, 12],
                }
            },
            "sniper_points": {"mrityu_bhaga": {"afflicted_points": []}},
        },
        birth_data=BIRTH,
        user_question="When will I get my first job?",
        intent_result={
            "mode": "LIFESPAN_EVENT_TIMING",
            "category": "career",
            "transit_request": {"startYear": 2016, "endYear": 2051},
        },
    )
    assert pack is not None
    assert pack["topic"]["family"] == "career"
    assert "D10" in pack["topic"]["divisionals_required"]
    assert pack["divisional_topic"]["present"] is True
    # Empty macro → DT none → ceiling cannot be high
    assert pack["confidence_ceiling"] != "high"
    assert pack["double_transit"]["near_band"]["status"] == "none"
    assert pack["candidate_windows"], "expected at least one candidate from Ketu-Venus"
    top = pack["candidate_windows"][0]
    assert "Mercury" in (top.get("dasha_chain") or "") or top.get("dasha_chain", "").startswith("Ketu-Venus")
    # Afflictions should surface debilitated Saturn and/or Bal Mercury/Venus
    planets = {a["planet"] for a in pack["afflictions"]}
    assert "Saturn" in planets or "Mercury" in planets or "Venus" in planets
    rules = " ".join(pack.get("cite_rules") or [])
    assert "HARD RANK ORDER" in rules
    assert "Soft override is FORBIDDEN" in rules
    assert "Full Double Transit" in rules
    assert "final trigger required" in rules


def test_anchor_fingerprint_from_pack():
    pack = {
        "topic": {"family": "career", "topic_key": "career_first_job"},
        "confidence_ceiling": "medium",
        "double_transit": {"near_band": {"status": "none"}},
        "candidate_windows": [
            {
                "rank": 1,
                "label": "2026-08-06 – 2026-10-06",
                "start": "2026-08-06",
                "end": "2026-10-06",
                "dasha_chain": "Ketu-Venus-Mercury",
                "double_transit": "none",
                "confidence_ceiling": "medium",
                "why": ["AD Venus occupies house 10"],
                "score": 6,
            }
        ],
    }
    anchor = build_anchor_from_lifespan_evidence(pack, question="first job?")
    assert anchor is not None
    assert anchor["window_1"]["dasha_chain"] == "Ketu-Venus-Mercury"
    assert anchor["verdict_fingerprint"]["double_transit"] == "none"
    assert anchor["confidence"] == "medium"

    meta_anchor = {
        "topic_key": "career",
        "topic_family": "career",
        "confidence": "high",
        "window_1": {"label": "Aug 2026", "dasha_chain": "", "rank": 1},
        "verdict_fingerprint": {},
    }
    enriched = enrich_anchor_fingerprint_from_pack(meta_anchor, pack)
    assert enriched["verdict_fingerprint"]["double_transit"] == "none"
    assert enriched["confidence"] == "medium"
    assert enriched["window_1"]["dasha_chain"] == "Ketu-Venus-Mercury"

    merged = merge_anchor_candidates(
        question="When will I get my first job?",
        mode="LIFESPAN_EVENT_TIMING",
        category="career",
        faq_category=None,
        answer_text="**Window 1**: August 2026 – October 2026",
        prediction_anchor_meta=None,
        event_timing_verdict=None,
        lifespan_timing_evidence=pack,
    )
    assert merged is not None
    assert merged["source"] == "lifespan_timing_evidence"
    assert merged["window_1"]["dasha_chain"] == "Ketu-Venus-Mercury"


def test_double_transit_full_requires_both_on_main_house():
    ctx = {
        "macro_transits_timeline": {
            "Jupiter": [
                {"start_date": "2027-01-01", "end_date": "2028-06-01", "house": 5},
            ],
            "Saturn": [
                {"start_date": "2027-01-01", "end_date": "2029-01-01", "house": 5},
            ],
        }
    }
    full = _double_transit_status(
        ctx,
        primary_houses=[5, 2, 9],
        asc_sign=5,
        start=datetime(2027, 1, 1),
        end=datetime(2028, 6, 1),
    )
    assert full["status"] == "full"

    # Occupy + support (not aspecting main) → partial
    partial = _double_transit_status(
        {
            "macro_transits_timeline": {
                "Jupiter": [
                    {"start_date": "2027-01-01", "end_date": "2028-06-01", "house": 5},
                ],
                "Saturn": [
                    {"start_date": "2027-01-01", "end_date": "2029-01-01", "house": 2},
                ],
            }
        },
        primary_houses=[5, 2, 9],
        asc_sign=5,
        start=datetime(2027, 1, 1),
        end=datetime(2028, 6, 1),
    )
    assert partial["status"] == "partial"

    # Aspect-only from both (no occupy) must not be High-grade full
    aspect_only = _double_transit_status(
        {
            "macro_transits_timeline": {
                # House 1 trines 5; house 9 trines 5 — no occupy of 5
                "Jupiter": [
                    {"start_date": "2027-01-01", "end_date": "2028-06-01", "house": 1},
                ],
                "Saturn": [
                    {"start_date": "2027-01-01", "end_date": "2029-01-01", "house": 9},
                ],
            }
        },
        primary_houses=[5, 2, 9],
        asc_sign=5,
        start=datetime(2027, 1, 1),
        end=datetime(2028, 6, 1),
    )
    assert aspect_only["status"] == "partial"

    none = _double_transit_status(
        {"macro_transits_timeline": {}},
        primary_houses=[5, 2, 9],
        asc_sign=5,
        start=datetime(2027, 1, 1),
        end=datetime(2028, 6, 1),
    )
    assert none["status"] == "none"


def test_marriage_ad_first_prefers_ad_band_not_micro_pd():
    """Marriage Window 1 should be AD-level ripe band; short PD is execution only."""
    ctx = {
        "ascendant_info": {"sign_id": 5},
        "planetary_analysis": {
            "Venus": {"basic_info": {"house": 7, "sign": 11, "sign_name": "Pisces"}},
            "Moon": {"basic_info": {"house": 7, "sign": 11, "sign_name": "Pisces"}},
            "Sun": {"basic_info": {"house": 11, "sign": 3, "sign_name": "Cancer"}},
            "Jupiter": {"basic_info": {"house": 2, "sign": 6, "sign_name": "Libra"}},
        },
        "macro_transits_timeline": {
            # Prefer Ketu-Moon AD via full DT on 7th during 2027
            "Jupiter": [
                {"start_date": "2027-03-01", "end_date": "2027-12-01", "house": 7},
            ],
            "Saturn": [
                {"start_date": "2027-03-01", "end_date": "2028-01-01", "house": 7},
            ],
        },
        "kp_analysis": {"planet_significators": {}},
    }
    ad_spine = [
        {
            "mahadasha": "Ketu",
            "antardasha": "Sun",
            "start_date": "2026-10-31",
            "end_date": "2027-03-08",
            "ad_start": "2026-10-31",
            "ad_end": "2027-03-08",
        },
        {
            "mahadasha": "Ketu",
            "antardasha": "Moon",
            "start_date": "2027-03-08",
            "end_date": "2027-10-08",
            "ad_start": "2027-03-08",
            "ad_end": "2027-10-08",
        },
    ]
    pd_near = [
        {
            "mahadasha": "Ketu",
            "antardasha": "Sun",
            "pratyantardasha": "Moon",
            "start_date": "2026-11-07",
            "end_date": "2026-11-17",
        },
        {
            "mahadasha": "Ketu",
            "antardasha": "Moon",
            "pratyantardasha": "Venus",
            "start_date": "2027-05-01",
            "end_date": "2027-07-15",
        },
    ]
    ranked, _ = _build_candidate_windows(
        ctx,
        family="marriage",
        primary_houses=[7, 2, 11],
        asc_sign=5,
        ad_spine=ad_spine,
        pd_near=pd_near,
        judgment=datetime(2026, 7, 1),
        scan_start=datetime(2016, 1, 1),
        divisional_present=True,
        chara_hit=False,
    )
    assert ranked, "expected marriage candidates"
    top = ranked[0]
    assert top["ranking_mode"] == "ad_first"
    assert top["dasha_chain"].startswith("Ketu-Moon")
    assert top["start"] == "2027-03-08"
    assert top["end"] == "2027-10-08"
    # Micro PD must not become the ripe label
    assert top["label"] != "2026-11-07 – 2026-11-17"
    assert top.get("execution_start")
    # Full DT + occupy/rule should allow high when divisional present
    assert top["double_transit"] == "full"
    assert top["confidence_ceiling"] in {"high", "medium"}


def test_children_dt_full_boosts_later_ad_over_weak_near_pd():
    ctx = {
        "ascendant_info": {"sign_id": 5},
        "planetary_analysis": {
            "Venus": {"basic_info": {"house": 10, "sign": 2}},
            "Saturn": {"basic_info": {"house": 5, "sign": 9}},
            "Jupiter": {"basic_info": {"house": 5, "sign": 9}},
            "Mars": {"basic_info": {"house": 5, "sign": 9}},
        },
        "macro_transits_timeline": {
            "Jupiter": [
                {"start_date": "2027-06-01", "end_date": "2028-12-01", "house": 5},
            ],
            "Saturn": [
                {"start_date": "2027-06-01", "end_date": "2029-01-01", "house": 5},
            ],
        },
        "kp_analysis": {"planet_significators": {}},
    }
    ad_spine = [
        {
            "mahadasha": "Ketu",
            "antardasha": "Venus",
            "ad_start": "2025-08-31",
            "ad_end": "2026-10-31",
            "start_date": "2025-08-31",
            "end_date": "2026-10-31",
        },
        {
            "mahadasha": "Ketu",
            "antardasha": "Mars",
            "ad_start": "2027-10-08",
            "ad_end": "2028-10-08",
            "start_date": "2027-10-08",
            "end_date": "2028-10-08",
        },
    ]
    pd_near = [
        {
            "mahadasha": "Ketu",
            "antardasha": "Venus",
            "pratyantardasha": "Saturn",
            "start_date": "2026-06-01",
            "end_date": "2026-08-01",
        }
    ]
    ranked, _ = _build_candidate_windows(
        ctx,
        family="children",
        primary_houses=[5, 2, 9, 11],
        asc_sign=5,
        ad_spine=ad_spine,
        pd_near=pd_near,
        judgment=datetime(2026, 7, 1),
        scan_start=datetime(2016, 1, 1),
        divisional_present=True,
        chara_hit=False,
    )
    assert ranked
    top = ranked[0]
    assert top["ranking_mode"] == "ad_first"
    assert "Mars" in (top.get("dasha_chain") or "")
    assert top["double_transit"] == "full"
    assert str(top.get("start") or "").startswith("2027")


def test_high_ceiling_forbidden_without_full_dt():
    ctx = {
        "ascendant_info": {"sign_id": 5},
        "planetary_analysis": {
            "Venus": {"basic_info": {"house": 10, "sign": 2}},
            "Mercury": {"basic_info": {"house": 11, "sign": 3}},
        },
        "macro_transits_timeline": {},
        "kp_analysis": {"planet_significators": {}},
    }
    ranked, _ = _build_candidate_windows(
        ctx,
        family="career",
        primary_houses=[10, 6, 2, 11],
        asc_sign=5,
        ad_spine=[
            {
                "mahadasha": "Ketu",
                "antardasha": "Venus",
                "ad_start": "2025-08-31",
                "ad_end": "2026-10-31",
                "start_date": "2025-08-31",
                "end_date": "2026-10-31",
            }
        ],
        pd_near=[
            {
                "mahadasha": "Ketu",
                "antardasha": "Venus",
                "pratyantardasha": "Mercury",
                "start_date": "2026-08-06",
                "end_date": "2026-10-06",
            }
        ],
        judgment=datetime(2026, 7, 1),
        scan_start=datetime(2016, 1, 1),
        divisional_present=True,
        chara_hit=True,
    )
    assert ranked
    assert ranked[0]["confidence_ceiling"] != "high"
    assert ranked[0]["double_transit"] == "none"


def test_cite_rules_forbid_soft_override_and_invented_full_dt():
    none_line = _double_transit_cite_instruction("none", main_house=7)
    assert "NONE" in none_line
    assert "Never synthesize Full Double Transit" in none_line
    assert "different houses" in none_line

    pack = {
        "topic": {"family": "marriage", "topic_key": "marriage", "primary_houses": [7]},
        "timing_focus": {},
        "dasha_spine": {"current": {}, "pd_near": [], "ad_spine": []},
        "double_transit": {
            "near_band": {"status": "none", "main_house": 7},
            "top_window": {"status": "full", "main_house": 7},
            "claim_allowed": "full",
            "cite_line": _double_transit_cite_instruction("full", main_house=7),
        },
        "candidate_windows": [
            {
                "rank": 1,
                "label": "2028-08 – 2031-08",
                "start": "2028-08-01",
                "end": "2031-08-01",
                "dasha_chain": "Rahu-Venus",
                "double_transit": "full",
                "score": 19,
                "confidence_ceiling": "high",
                "same_arc_hint": "same_arc",
                "why": ["Full DT on 7th"],
            },
            {
                "rank": 2,
                "label": "2024 – 2027",
                "start": "2024-01-01",
                "end": "2027-07-01",
                "dasha_chain": "Rahu-Mercury",
                "double_transit": "none",
                "score": 11,
                "confidence_ceiling": "medium",
                "same_arc_hint": "alternate_path",
                "why": ["Nearer but weaker"],
            },
        ],
        "confidence_ceiling": "high",
        "cite_rules": [
            "HARD RANK ORDER: Present candidate_windows strictly by their `rank` field",
            "Soft override is FORBIDDEN.",
            "Never claim 'Full Double Transit' / 'Double Transit activated' for a window "
            "unless that exact candidate_window.double_transit == 'full'.",
            "final trigger required",
        ],
    }
    compact = compact_lifespan_timing_evidence_for_prompt(pack)
    assert compact is not None
    assert compact["candidate_windows"][0]["rank"] == 1
    assert compact["candidate_windows"][0]["score"] == 19
    assert compact["candidate_windows"][0]["double_transit"] == "full"
    assert compact["candidate_windows"][1]["double_transit"] == "none"
    assert compact["candidate_windows"][1]["score"] == 11
    rules = " ".join(compact["cite_rules"] or [])
    assert "Soft override is FORBIDDEN" in rules
    assert "double_transit == 'full'" in rules or 'double_transit == "full"' in rules or "double_transit == 'full'" in rules


def test_pack_cite_rules_include_hard_rank_when_built():
    full = _double_transit_cite_instruction("full", main_house=7)
    assert "candidate_window" in full
    assert "SAME main event house" in full
    from ai.parallel_chat.prompt_blocks import free_question_elaborate_instruction
    from chat.system_instruction_config import LIFESPAN_MERGE_TIMING_RULE, SYNTHESIS_RULES

    assert "Soft override / re-ranking is FORBIDDEN" in LIFESPAN_MERGE_TIMING_RULE or "Soft override" in LIFESPAN_MERGE_TIMING_RULE
    assert "FORBIDDEN" in LIFESPAN_MERGE_TIMING_RULE
    assert "candidate_window.double_transit" in SYNTHESIS_RULES or "each `candidate_window.double_transit`" in SYNTHESIS_RULES
    elab = free_question_elaborate_instruction()
    assert "exact rank order" in elab
    assert "final trigger required" in elab
