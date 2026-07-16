"""Unit tests for astrology response QA deterministic precheck."""

from ai.response_qa_auditor import run_deterministic_precheck, strip_html, extract_date_mentions


def test_strip_html_basic():
    assert "hello" in strip_html("<p>hello</p>").lower()


def test_extract_date_ranges():
    text = "Offer between July 12 and August 15, 2026. Later August 28, 2026 onwards."
    dates = extract_date_mentions(text)
    assert any("july" in d.lower() or "jul" in d.lower() for d in dates)
    assert any("august 28" in d.lower() or "aug" in d.lower() for d in dates)


def test_precheck_flags_overclaim_and_drift():
    prior = (
        "Your first breakthrough is July 12 – August 15, 2026. "
        "Mars PD activates the 7th house of contracts and appointment letter. "
        "Expect a solid offer letter / first job in that window."
    )
    answer = (
        "This is the absolute astrological truth and a mathematical conclusion. "
        "The previous prediction was different because of activity vs results. "
        "July 8 – August 20 is a Near-Miss window (Medium) with interview activity but not closing. "
        "Absolute breakthrough and offer letter is August 28, 2026 to October 15, 2026. "
        "Mars PD signifies the 8th house of rejection/obstacles."
    )
    question = "Is this app fake? You previously told me something else."
    out = run_deterministic_precheck(
        answer_text=answer,
        prior_assistant_texts=[prior],
        question_text=question,
    )
    assert out["user_consistency_challenge"] is True
    assert out["overclaim_matches"]
    assert out["timing_drift_hints"]
    assert "mars_pd_7th_vs_8th" in out["house_signification_flips"]
    cats = {f["category"] for f in out["flags"]}
    assert "timing_drift" in cats
    assert "overclaim" in cats
    assert "contradiction" in cats
    assert "user_care" in cats
