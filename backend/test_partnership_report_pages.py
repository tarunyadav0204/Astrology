from datetime import datetime

import pytest

from reports.assembly.page_assembler import assemble_partnership_pages
from reports.pdf_service import render_report_pdf_bytes


def _sample_chart():
    return {
        "ascendant": 42.0,
        "houses": [{"sign": index} for index in range(12)],
        "planets": {
            "Sun": {"sign": 1},
            "Moon": {"sign": 3},
            "Mars": {"sign": 6},
            "Mercury": {"sign": 4},
            "Jupiter": {"sign": 8},
            "Venus": {"sign": 1},
            "Saturn": {"sign": 10},
            "Rahu": {"sign": 11},
            "Ketu": {"sign": 5},
        },
    }


def _premium_report():
    section_keys = [
        "overall_foundation",
        "ashtakoota_and_exceptions",
        "manglik_and_dosha_handling",
        "cross_chart_chemistry",
        "person_one_marriage_support",
        "person_two_marriage_support",
        "navamsa_and_long_term_stability",
        "timing_and_marriage_windows",
        "contradictions_and_hidden_factors",
        "final_guidance_and_remedies",
    ]
    return {
        "headline": "Promising match with timing-sensitive responsibilities",
        "compatibility_verdict": "Proceed with maturity and clear family expectations.",
        "priority_actions": [
            "Discuss finances before engagement.",
            "Use supportive windows for formal decisions.",
            "Avoid impulsive decisions during pressure periods.",
        ],
        "follow_up_questions": [
            "Which window is best for engagement?",
            "What should both families align on first?",
        ],
        "sections": [
            {
                "key": key,
                "static_summary": f"{key} deterministic summary.",
                "ai_interpretation": f"{key} detailed AI interpretation with relationship-specific judgement.",
                "practical_meaning": f"{key} practical meaning for daily married life.",
                "decision_guidance": f"{key} decision guidance for the couple.",
                "facts": [f"{key} fact {idx}" for idx in range(1, 5)],
            }
            for key in section_keys
        ],
    }


def _engine_result():
    return {
        "overall_score": {"percentage": 78},
        "recommendation": {
            "verdict": "Good with manageable cautions",
            "timing_note": "Use the next supportive period for formal talks.",
            "risk_level": "medium",
            "remedies": ["Keep communication structured.", "Take family blessings."],
        },
        "timing_overlay": {
            "shared": {
                "joint_readiness_score": 74,
                "current_window": {"climate": "supportive"},
                "next_favorable_windows": [
                    {"start_date": "2027-02-01", "end_date": "2027-05-30", "climate": "strong", "reason": "mutual dasha support"},
                    {"start_date": "2028-01-10", "end_date": "2028-04-12", "climate": "moderate", "reason": "transit support"},
                ],
            }
        },
        "relationship_indicators": {
            "cross_chart": {
                "moon_element_match": {"score": "good"},
                "overall_relationship_quality": {"score": "strong"},
                "venus_to_mars": {"score": "warm"},
                "marriage_alignment": {"score": "steady"},
            }
        },
        "ashtakoota": {
            "total_score": 27,
            "effective_total_score": 29,
            "breakdown": [
                {"name": "Varna", "score": 1, "max_score": 1, "meaning": "Basic temperament support"},
                {"name": "Nadi", "score": 8, "max_score": 8, "meaning": "Health and lineage compatibility"},
            ],
        },
        "profiles": {
            "boy": {"marriage_support": {"seventh_house": "stable spouse indicators"}},
            "girl": {"marriage_support": {"venus": "warm relationship expectations"}},
        },
        "evidence_summary": {
            "positive_factors": ["D9 support is present.", "Moon comfort is workable.", "Family stability indicators are helpful."],
            "caution_factors": ["Timing needs patience.", "Communication must be handled consciously."],
            "neutral_factors": ["Career priorities need planning."],
        },
    }


def _context():
    branch_summary = {
        "jaimini": {"relationship_note": "Jaimini supports formal alliance after maturity."},
        "kp": {"materialization_note": "KP shows event materialization in supportive windows."},
        "nakshatra": {"emotional_note": "Nakshatra rhythm is emotionally responsive."},
        "nadi": {"relationship_note": "Nadi shows one repeated communication pattern."},
        "d60": {"summary": "D60 indicates karmic responsibility.", "lagna_deity": "Protective deity signal."},
    }
    return {
        "pair": {
            "boy": {"name": "Tarun", "date": "1990-01-01", "time": "10:00", "place": "Delhi"},
            "girl": {"name": "Deepika", "date": "1992-02-02", "time": "11:30", "place": "Mumbai"},
        },
        "chart_style": "both",
        "summaries": {"boy": branch_summary, "girl": branch_summary},
        "faq_items": [{"question": "Should we proceed?", "answer": "Proceed with timing awareness."}],
    }


def test_partnership_report_assembles_dense_twenty_page_document():
    pages = assemble_partnership_pages(_context(), _premium_report(), _engine_result())

    assert len(pages) == 24
    assert all(page["page_number"] == index for index, page in enumerate(pages, start=1))
    assert not any("Show North Indian" in " ".join(page.get("bullets", [])) for page in pages)
    assert all(
        len(page.get("bullets", []))
        + len(page.get("notes", []))
        + len(page.get("tables", []))
        + len(page.get("metrics", []))
        >= 4
        for page in pages[:19]
    )
    assert pages[6]["chart_refs"] == ["boy_d1"]
    assert pages[10]["chart_refs"] == ["boy_d9"]
    assert pages[16]["chart_refs"] == ["boy_d7", "girl_d7"]


def test_partnership_report_pdf_renderer_handles_dense_pages():
    pytest.importorskip("reportlab")
    pages = assemble_partnership_pages(_context(), _premium_report(), _engine_result())
    report_document = {
        "report_id": "test-report",
        "report_type": "partnership",
        "language": "english",
        "generated_at": datetime.now().isoformat(),
        "report_version": "test",
        "pair": _context()["pair"],
        "score_summary": {"percentage": 78, "guna_milan": {"effective_total_score": 29}},
        "pages": pages,
        "premium_report": _premium_report(),
        "chart_data": {
            "boy": _sample_chart(),
            "girl": _sample_chart(),
            "boy_d9": _sample_chart(),
            "girl_d9": _sample_chart(),
        },
    }

    pdf_bytes = render_report_pdf_bytes(report_document)

    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 10_000

