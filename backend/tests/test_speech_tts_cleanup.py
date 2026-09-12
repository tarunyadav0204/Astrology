from tts.routes import (
    _apply_pronunciation_plain,
    _apply_pronunciation_ssml,
    _fallback_spoken_tts_text,
    _strip_markdown_for_speech,
)


def test_speech_cleanup_removes_normal_and_escaped_markdown_markers():
    source = r"Your **Cancer Lagna** and \*\*Moon (Chandra)\*\* are important."

    cleaned = _fallback_spoken_tts_text(source, "en")

    assert "Cancer Lagna" in cleaned
    assert "Moon (Chandra)" in cleaned
    assert "*" not in cleaned
    assert r"\*" not in cleaned


def test_speech_cleanup_preserves_link_text_and_removes_other_markdown_syntax():
    source = """## Main reading
- **Moon** supports this.
- Read [the explanation](https://example.com) [[SH_D1_H4_OCC_MOON]].
- Use `D1` carefully.
"""

    cleaned = _strip_markdown_for_speech(source)

    assert "Main reading" in cleaned
    assert "Moon supports this." in cleaned
    assert "the explanation" in cleaned
    assert "D1" in cleaned
    assert "https://" not in cleaned
    assert "[[SH_" not in cleaned
    assert "**" not in cleaned
    assert "`" not in cleaned


def test_english_lagna_uses_short_a_pronunciation_alias():
    assert _apply_pronunciation_plain("Cancer Lagna") == "Cancer Lag-na"
    assert 'alias="Lag-na"' in _apply_pronunciation_ssml("Cancer Lagna")
