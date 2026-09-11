from chat.instant_chat_pipeline import _parse_speech_followups_from_answer
from utils.response_transport import strip_internal_evidence_markers


def test_valid_internal_marker_is_removed_without_joining_words():
    raw = "व्यापार [[SH_D1_H10_LORD_MARS]] शुरू करें"

    assert strip_internal_evidence_markers(raw) == "व्यापार शुरू करें"


def test_malformed_internal_marker_preserves_hindi_prose():
    raw = (
        "बुध की स्थिति [[SH_D1_H व्यापारिक सूझबूझ और साहस "
        "1_H11_OCC_GULIKA]] देती है।"
    )

    cleaned = strip_internal_evidence_markers(raw)

    assert cleaned == "बुध की स्थिति व्यापारिक सूझबूझ और साहस देती है।"
    assert "[[" not in cleaned
    assert "GULIKA" not in cleaned


def test_nested_damaged_marker_does_not_swallow_answer_prose():
    raw = (
        "शुक्र यहाँ [[SH_D1_H लाभ और सामाजिक सफलता देता है "
        "[[SH_D1_H11_OCC_GULIKA]] लेकिन धैर्य रखें।"
    )

    cleaned = strip_internal_evidence_markers(raw)

    assert cleaned == "शुक्र यहाँ लाभ और सामाजिक सफलता देता है लेकिन धैर्य रखें।"
    assert "SH_D1" not in cleaned


def test_provisional_cleanup_holds_only_an_incomplete_machine_token():
    assert (
        strip_internal_evidence_markers(
            "उत्तर तैयार है [[SH_D1_H10_OCC_", provisional=True
        )
        == "उत्तर तैयार है"
    )
    assert (
        strip_internal_evidence_markers(
            "उत्तर [[SH_D1_H आगे जारी है", provisional=True
        )
        == "उत्तर आगे जारी है"
    )


def test_orphan_speech_followup_end_marker_is_not_user_visible():
    answer, followups = _parse_speech_followups_from_answer(
        "क्या आप किसी खास क्षेत्र में व्यापार शुरू करने की सोच\\_UPS_END### \\"
    )

    assert answer == "क्या आप किसी खास क्षेत्र में व्यापार शुरू करने की सोच"
    assert followups == []


def test_complete_speech_followups_still_parse():
    answer, followups = _parse_speech_followups_from_answer(
        "मुख्य उत्तर।\n"
        "###FOLLOW_UPS_START###\n"
        '["क्या आप इस साल के व्यापार के बारे में जानना चाहेंगे?"]\n'
        "###FOLLOW_UPS_END###"
    )

    assert answer == "मुख्य उत्तर।"
    assert followups == ["क्या आप इस साल के व्यापार के बारे में जानना चाहेंगे?"]
