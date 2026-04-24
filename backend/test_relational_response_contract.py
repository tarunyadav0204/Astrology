from ai.relational_response_contract import RelationalResponseContract


def test_relational_response_contract_accepts_safe_event_answer():
    profile = {
        "relation_family": "spouse_romantic",
        "event_topic": "trust_infidelity",
    }
    text = """
**Direct Answer**: The chart suggests trust strain and secrecy risk, but it does not prove cheating as a fact.

**Main Astrological Evidence**: Rahu-Venus and Saturn-Moon patterns indicate emotional turbulence and confusion.

**Limits & Uncertainty**: Astrology shows indication, not proof. Real-world verification and direct conversation are still needed.

FAQ_META: {"category":"marriage","canonical_question":"Trust and infidelity risk in marriage"}
""".strip()

    ok, errors = RelationalResponseContract.validate(text, profile)

    assert ok is True
    assert errors == []


def test_relational_response_contract_rejects_generic_compatibility_sections_for_event_question():
    profile = {
        "relation_family": "spouse_romantic",
        "event_topic": "legal_confinement",
    }
    text = """
### Overall Compatibility
The relationship is strong.

### Emotional Bond
There is a strong connection.

FAQ_META: {"category":"marriage","canonical_question":"Marriage legal issue"}
""".strip()

    ok, errors = RelationalResponseContract.validate(text, profile)

    assert ok is False
    assert any(err.startswith("forbidden_generic_section:overall compatibility") for err in errors)
    assert any(err.startswith("forbidden_generic_section:emotional bond") for err in errors)


def test_relational_response_contract_rejects_overclaiming_accusation_language():
    profile = {
        "relation_family": "business_work",
        "event_topic": "business_betrayal",
    }
    text = """
**Direct Answer**: This proves that your partner definitely committed fraud and they absolutely cheated you.

FAQ_META: {"category":"general","canonical_question":"Business betrayal and fraud"}
""".strip()

    ok, errors = RelationalResponseContract.validate(text, profile)

    assert ok is False
    assert "unsafe_overclaim_language" in errors
    assert "missing_safety_uncertainty_cue" in errors


def test_relational_response_contract_requires_faq_meta():
    profile = {
        "relation_family": "guru_disciple",
        "event_topic": "guru_trust_breach",
    }
    text = "The chart suggests trust concerns, but this is not proof."

    ok, errors = RelationalResponseContract.validate(text, profile)

    assert ok is False
    assert "missing_faq_meta" in errors


def test_relational_response_contract_blocks_generic_sections_for_behavior_question():
    profile = {
        "relation_family": "spouse_romantic",
        "event_topic": "general_relationship",
    }
    text = """
### Overall Compatibility
The relationship is moderate.

### Emotional Bond
There is affection.

FAQ_META: {"category":"marriage","canonical_question":"Marriage behavior dynamics"}
""".strip()

    ok, errors = RelationalResponseContract.validate(
        text,
        profile,
        question="Tell me in detail what is Tarun's behaviour towards Deepika and Deepika's behaviour about Tarun",
    )

    assert ok is False
    assert any(err.startswith("forbidden_generic_section:overall compatibility") for err in errors)
    assert "missing_behavior_texture_nakshatra" in errors
    assert "missing_behavior_texture_sign" in errors
