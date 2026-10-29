import pytest

from ai.response_parser import ResponseParser
from chat.verified_chat_pipeline import (
    _premium_writer_system,
    _verified_final_writer_instruction,
    _verified_sentiment_instruction,
    redact_verified_internal_transport,
)
from utils.response_transport import strip_internal_evidence_markers


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_verified_redaction_preserves_simple_sections_and_ranked_choices(newline):
    answer = newline.join([
        'Thank you for consulting AstroRoshni.', '',
        '## Best-fit fields', '',
        '1. **Business Analytics**', 'A practical choice.', '',
        '2. **Applied Data Science**', 'Build real projects.', '',
        '## Why this direction fits', '',
        'The supplied education branch shows strong learning potential.', '',
        '## Final verdict', '', 'Choose a practical program.',
    ])
    expected = answer.replace('The supplied education branch shows', 'The education analysis shows')
    assert redact_verified_internal_transport(answer) == expected


def test_verified_redaction_preserves_technical_html_and_markdown_spacing():
    answer = '#### The Parashari View\n\n<span class="chat-sentiment-positive">Supported</span>  \nNext line.\n\n    Indented text'
    assert redact_verified_internal_transport(answer) == answer


def test_verified_redaction_still_removes_internal_delivery_language():
    assert redact_verified_internal_transport('The supplied packet shows a favorable period.') == 'The chart shows a favorable period.'


def test_verified_redaction_removes_legacy_support_and_caution_badges():
    answer = '**✓ Support · This period is active.** **! Caution · Saturn makes it slower.**'
    assert redact_verified_internal_transport(answer) == 'This period is active. Saturn makes it slower.'


def test_verified_editorial_guard_rejects_a_rewrite_that_loses_timing_facts():
    from chat.verified_chat_pipeline import _verified_editorial_preserves_timing

    source = 'Rank 1: 17 October–3 December 2027. The child house has 20 points.'
    assert _verified_editorial_preserves_timing(source, source)
    assert not _verified_editorial_preserves_timing(source, 'Rank 1: October 2027.')


def test_verified_final_response_cleanup_keeps_visible_layout():
    answer = 'A practical degree fits best.\n\n## Best-fit fields\n\n1. **Analytics**\nApply your skills.\n\n## Final verdict\n\nChoose industry projects.'
    parsed = ResponseParser.parse_images_in_chat_response(answer)
    content, _ = ResponseParser.parse_prediction_anchor_metadata(parsed['content'])
    final = redact_verified_internal_transport(strip_internal_evidence_markers(content))
    assert final == answer


@pytest.mark.parametrize('style', ['simple', 'technical'])
def test_verified_writer_requests_existing_positive_and_negative_highlighting(style):
    system = _premium_writer_system('default', 'english', response_style=style)
    assert _verified_sentiment_instruction() in system
    assert '<span class="chat-sentiment-positive">' in system
    assert '<span class="chat-sentiment-negative">' in system
    assert 'Never create a\nsentiment tag merely to make the answer look balanced' in system


def test_simple_final_instruction_keeps_sections_and_allows_sentiment_spans():
    instruction = _verified_final_writer_instruction('simple')
    assert '## Heading' in instruction
    assert 'permitted HTML exception' in instruction
    assert _verified_sentiment_instruction() in instruction


def test_verified_cleanup_preserves_both_sentiment_colors_and_sections():
    answer = (
        '## Why this direction fits\n\n'
        'Mercury supports <span class="chat-sentiment-positive">strong analytical ability</span>.\n\n'
        '## Important qualification\n\n'
        'Watch for <span class="chat-sentiment-negative">mental overload</span>.'
    )
    parsed = ResponseParser.parse_images_in_chat_response(answer)
    final = redact_verified_internal_transport(strip_internal_evidence_markers(parsed['content']))
    assert final == answer


@pytest.mark.parametrize('style', ['simple', 'technical'])
def test_verified_emphasis_is_required_in_system_and_final_turn(style):
    from chat.verified_chat_pipeline import _verified_emphasis_instruction
    contract = _verified_emphasis_instruction()
    assert contract in _premium_writer_system('default', 'english', response_style=style)
    assert contract in _verified_final_writer_instruction(style)
    assert 'main conclusion in the opening' in contract
    assert 'material cautions or qualifications' in contract
    assert 'Never bold entire paragraphs' in contract
    assert 'Keep sentiment-span contents plain text' in contract


def test_consultation_voice_removes_delivery_nouns_but_keeps_user_history():
    text = "Based on the supplied information, your Moon supports communication. The supplied package does not establish an exact date. In the provided D9 chart, Venus is strong. You mentioned that you married in 2020."
    result = redact_verified_internal_transport(text)
    assert 'supplied' not in result and 'provided' not in result
    assert 'does not establish an exact date' in result
    assert 'In the D9 chart, Venus is strong.' in result
    assert 'You mentioned that you married in 2020.' in result


@pytest.mark.parametrize('style', ['simple','technical'])
@pytest.mark.parametrize('mode', ['DEFAULT','PRASHNA','PREDICT_DAILY','PREDICT_EVENT_TIMING','PREDICT_PERIOD_OUTLOOK','CHART_DASHA_ANALYSIS','FACTUAL_LOOKUP','CUSTOM_READING'])
def test_consultation_guidance_survives_every_verified_layout(style,mode):
    from chat.verified_consultation import verified_consultation_instruction
    contract=verified_consultation_instruction()
    assert contract in _premium_writer_system(mode,'Hindi in Latin script',response_style=style)
    assert contract in _verified_final_writer_instruction(style,mode)
    assert 'conclusive' in contract
    assert 'do not stop at' in contract
    assert 'Do not guarantee an outcome or invent facts' in contract
    assert 'arbitrary midpoint' in contract


def test_all_verified_answers_seek_registered_calculations_before_claiming_missing_evidence():
    from chat.verified_consultation import verified_consultation_instruction
    instruction=verified_consultation_instruction()
    assert 'SEEK MISSING EVIDENCE BEFORE WRITING' in instruction
    assert 'request the necessary calculation' in instruction
    assert 'Do not ask the user to supply planetary calculations' in instruction
    assert 'within the selected reading' in instruction
    assert 'never imply that an unrequested calculation ran' in instruction
    assert 'exhausted tool budget' in instruction
