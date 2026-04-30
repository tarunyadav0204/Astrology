from marriage_matching.premium_report import (
    COMPATIBILITY_PREMIUM_REPORT_PROMPT,
    build_static_compatibility_report,
)


def test_compatibility_premium_prompt_covers_all_major_sections():
    assert '"key": "overall_foundation"' in COMPATIBILITY_PREMIUM_REPORT_PROMPT
    assert '"key": "ashtakoota_and_exceptions"' in COMPATIBILITY_PREMIUM_REPORT_PROMPT
    assert '"key": "manglik_and_dosha_handling"' in COMPATIBILITY_PREMIUM_REPORT_PROMPT
    assert '"key": "cross_chart_chemistry"' in COMPATIBILITY_PREMIUM_REPORT_PROMPT
    assert '"key": "person_one_marriage_support"' in COMPATIBILITY_PREMIUM_REPORT_PROMPT
    assert '"key": "person_two_marriage_support"' in COMPATIBILITY_PREMIUM_REPORT_PROMPT
    assert '"key": "navamsa_and_long_term_stability"' in COMPATIBILITY_PREMIUM_REPORT_PROMPT
    assert '"key": "timing_and_marriage_windows"' in COMPATIBILITY_PREMIUM_REPORT_PROMPT
    assert '"key": "contradictions_and_hidden_factors"' in COMPATIBILITY_PREMIUM_REPORT_PROMPT
    assert '"key": "final_guidance_and_remedies"' in COMPATIBILITY_PREMIUM_REPORT_PROMPT


def test_static_compatibility_report_has_ten_complete_sections():
    full = {
        "overall_score": {"percentage": 76, "grade": "Good"},
        "rule_profile": {"label": "Balanced Modern"},
        "ashtakoota": {
            "total_score": 22,
            "effective_total_score": 25,
            "effective_critical_issues": ["Bhakoot issue softened"],
            "exceptions": {"nadi": {"reasons": []}, "bhakoot": {"reasons": ["Friendly sign rulers soften Bhakoot"]}},
        },
        "manglik": {"compatibility": {"status": "Manageable", "score": 7, "description": "Pair-level handling is manageable", "exception_reasons": ["Shared cancellation reduces severity"]}},
        "relationship_indicators": {
            "cross_chart": {
                "band": "Supportive",
                "moon_element_match": {"score": 72},
                "venus_to_mars": {"score": 68},
                "mars_to_venus": {"score": 64},
                "navamsa_pair_support": 71,
                "positive_factors": ["Moon signs cooperate emotionally"],
                "caution_factors": ["Venus-Mars style differs slightly"],
            }
        },
        "timing_overlay": {
            "shared": {
                "joint_readiness_score": 69,
                "current_window": {"climate": "favorable"},
                "next_favorable_windows": [{"start_date": "2026-09-01", "end_date": "2027-01-01", "score": 74}],
            }
        },
        "profiles": {
            "boy": {
                "seventh_house": {"d1_strength": {"score": 66, "band": "Supportive"}, "d9_strength": {"score": 71}},
                "navamsa_synthesis": {"score": 72, "band": "Supportive", "root_vs_fruit": "improves", "supportive_factors": ["D9 Venus is strong"], "challenging_factors": ["Saturn adds seriousness"]},
            },
            "girl": {
                "seventh_house": {"d1_strength": {"score": 63, "band": "Supportive"}, "d9_strength": {"score": 69}},
                "navamsa_synthesis": {"score": 68, "band": "Supportive", "root_vs_fruit": "consistent", "supportive_factors": ["Jupiter protects D9"], "challenging_factors": ["Adjustment needed after marriage"]},
            },
        },
        "recommendation": {"verdict": "Good match with manageable differences", "timing_note": "Current joint timing is supportive for marriage decisions.", "remedies": ["Use timing intelligently"]},
        "evidence_summary": {"positive_factors": ["Current timing supports progress"], "caution_factors": ["Some temperament difference"], "contradictions": ["Raw score is lower than deeper support suggests"]},
    }
    report = build_static_compatibility_report(full, {"name": "A"}, {"name": "B"})
    assert report["report_version"] == "compatibility_premium_v1"
    assert len(report["sections"]) == 10
    assert report["sections"][0]["key"] == "overall_foundation"
    assert report["sections"][-1]["key"] == "final_guidance_and_remedies"
