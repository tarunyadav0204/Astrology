import re

from tts.routes import (
    _fallback_spoken_tts_text,
    _podcast_audio_config,
    _replace_spoken_punctuation_with_breaks,
    _segment_text_to_ssml,
    _strip_spoken_control_cues_for_plain_tts,
    _strip_literal_punctuation_words,
)


def test_strip_literal_punctuation_words():
    assert "comma" not in _strip_literal_punctuation_words("Moon in Cancer comma that's the one").lower()
    assert "dot" not in _strip_literal_punctuation_words("Mars is strong dot Then Saturn").lower()
    assert "question mark" not in _strip_literal_punctuation_words("Really question mark").lower()
    assert "period" in _strip_literal_punctuation_words("this dasha period is intense")


def test_punctuation_becomes_breaks_not_spoken_chars():
    ssml = _replace_spoken_punctuation_with_breaks("Moon in Cancer. Mars, wait.")
    assert "," not in ssml
    assert "." not in ssml
    assert "<break time=" in ssml
    assert 'time="70ms"' in ssml
    tagged = _replace_spoken_punctuation_with_breaks('<prosody pitch="+0.8st">Wait.</prosody>')
    assert 'pitch="+0.8st"' in tagged
    assert "Wait." not in tagged


def test_plain_pause_cleanup_preserves_commas_without_adding_periods():
    source = "centered on coordination, data, or commerce."
    prepared = _fallback_spoken_tts_text(source, "en")
    cleaned = _strip_spoken_control_cues_for_plain_tts(prepared)

    assert cleaned == source
    assert ",." not in cleaned


def test_chirp_break_ssml_hides_commas_and_periods_from_voice():
    source = _fallback_spoken_tts_text(
        "centered on coordination, data, or commerce.",
        "en",
    )
    ssml = _segment_text_to_ssml(source, ssml_mode="breaks")
    spoken_nodes = re.sub(r"<[^>]+>", "", ssml)

    assert "," not in spoken_nodes
    assert "." not in spoken_nodes
    assert "coordination" in spoken_nodes
    assert "data" in spoken_nodes
    assert "commerce" in spoken_nodes


def test_segment_ssml_does_not_keep_commas_or_dots():
    ssml = _segment_text_to_ssml(
        "Moon in Cancer, that's the big one. [PAUSE:short] Mars is strong.",
        "male",
    )
    spoken = re.sub(r"<[^>]+>", " ", ssml)
    assert "," not in spoken
    assert "." not in spoken
    assert "comma" not in ssml.lower()
    assert "dot" not in ssml.lower()


def test_male_podcast_host_uses_requested_speaking_rate():
    male = _podcast_audio_config("male")
    female = _podcast_audio_config("female")
    assert male.speaking_rate == 1.15
    assert female.speaking_rate == 1.0


def test_indic_voices_use_break_only_ssml():
    from tts.routes import _is_indic_voice, _ssml_mode_for_voice

    assert _is_indic_voice("en-IN-Neural2-A")
    assert _is_indic_voice("hi-IN-Wavenet-A")
    assert not _is_indic_voice("en-GB-Chirp3-HD-Algenib")
    assert _ssml_mode_for_voice("en-IN-Neural2-A") == "cues"
    assert _ssml_mode_for_voice("en-IN-Neural2-B") == "cues"
    assert _ssml_mode_for_voice("en-IN-Journey-F") == "plain"
    assert _ssml_mode_for_voice("en-GB-Chirp3-HD-Algenib") == "breaks"

    ssml = _segment_text_to_ssml("Moon in Cancer. [RISE:Really?] Mars.", "female", ssml_mode="breaks")
    assert "<prosody" not in ssml
    assert "pitch=" not in ssml
    assert "<emphasis" not in ssml
    assert "<say-as" not in ssml
    assert ssml.startswith("<speak>")
    assert "<break time=" in ssml
    from tts.routes import _language_code_from_voice_name

    assert _language_code_from_voice_name("en-GB-Chirp3-HD-Algenib") == "en-GB"
    assert _language_code_from_voice_name("hi-IN-Neural2-A") == "hi-IN"
    assert _language_code_from_voice_name("", "en-GB") == "en-GB"


def test_neural2_keeps_punctuation_instead_of_stacking_breaks():
    male = _segment_text_to_ssml(
        "Moon in Cancer, that's the big one. [PAUSE:medium] Mars is strong.",
        "male",
        ssml_mode="cues",
    )
    assert "<prosody" not in male
    assert "Moon in Cancer, that's the big one." in male
    assert male.count("<break") == 1
    assert 'time="260ms"' in male
    assert "Daa-sha" not in _segment_text_to_ssml("This Dasha is strong", "male", ssml_mode="cues")
    assert "Daasha" in _segment_text_to_ssml("This Dasha is strong", "male", ssml_mode="cues")


def test_ssml_does_not_emit_apostrophe_entity():
    from tts.routes import _escape_ssml_text

    assert "&#x27;" not in _escape_ssml_text("that's the one").lower()
    assert "that's" in _escape_ssml_text("that&#x27;s the one")
    ssml = _segment_text_to_ssml("that's the big one", "female", ssml_mode="breaks")
    assert "&#x27;" not in ssml.lower()
    assert "&#39;" not in ssml
    assert "that's" in ssml


def _spoken_ssml_text(ssml: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", ssml or "")).strip().lower()


def test_malformed_pause_cues_are_not_spoken():
    samples = [
        "Moon in Cancer. [PAUSE: short] Mars is strong.",
        "Moon in Cancer. PAUSE short Mars is strong.",
        "Moon in Cancer. pause short Mars is strong.",
        "Moon in Cancer. [pause] Mars is strong.",
        "Moon in Cancer. short pause Mars is strong.",
        "Moon in Cancer. (pause) Mars is strong.",
        "Yeah. pause. Mars is strong.",
        "Moon in Cancer. pause, pause short pause long Mars is strong.",
        "Moon in Cancer. [PAUSE:long] Mars is strong.",
    ]
    for source in samples:
        ssml = _segment_text_to_ssml(source, "female", ssml_mode="breaks")
        spoken = _spoken_ssml_text(ssml)
        assert "pause" not in spoken, source
        assert "<break time=" in ssml
        plain = _strip_spoken_control_cues_for_plain_tts(source).lower()
        assert "pause" not in plain, source
        assert "mars is strong" in spoken
        assert "mars is strong" in plain


def test_pause_breaks_stay_short_and_do_not_stack():
    short = _segment_text_to_ssml("Moon. [PAUSE:short] Mars.", "female", ssml_mode="breaks")
    assert "[<" not in short
    assert 'time="240ms"' in short or 'time="380ms"' in short
    stacked = _segment_text_to_ssml(
        "Moon. pause, pause short pause long Mars.",
        "female",
        ssml_mode="breaks",
    )
    assert "[<" not in stacked
    times = [int(value) for value in re.findall(r'time="(\d+)ms"', stacked)]
    assert times
    assert max(times) <= 380
    assert stacked.count("<break") <= 3


def test_real_pause_verb_is_kept():
    source = "Pause before you send that message. Then wait."
    plain = _strip_spoken_control_cues_for_plain_tts(source)
    assert "Pause before you send that message" in plain
    ssml = _segment_text_to_ssml(source, "female", ssml_mode="breaks")
    assert "Pause before you send that message" in re.sub(r"<[^>]+>", " ", ssml)
