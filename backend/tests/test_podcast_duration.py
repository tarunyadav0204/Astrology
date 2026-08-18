from tts.podcast_narrator import (
    PODCAST_BODY_MAX_SPOKEN_WORDS,
    PODCAST_MAX_SPOKEN_WORDS,
    _spoken_word_count,
    constrain_podcast_script,
)
from tts.routes import _podcast_intro_line, _podcast_outro_lines


def test_podcast_script_keeps_complete_turns_within_budget():
    script = "\n".join(
        f"{'FEMALE' if index % 2 == 0 else 'MALE'}: [PAUSE:short] "
        + " ".join(f"word{index}_{word}" for word in range(12))
        for index in range(80)
    )

    constrained = constrain_podcast_script(script)

    assert _spoken_word_count(constrained) <= PODCAST_MAX_SPOKEN_WORDS
    assert all(line.startswith(("FEMALE: ", "MALE: ")) for line in constrained.splitlines())
    assert constrained.splitlines()[-1] in script.splitlines()


def test_short_podcast_script_is_unchanged():
    script = "FEMALE: [RISE:Ready?]\nMALE: [FALL:Let's begin.]"
    assert constrain_podcast_script(script) == script


def test_prosody_cues_and_roles_are_not_counted_as_spoken_words():
    script = "FEMALE: [PAUSE:short] Two spoken words"
    assert _spoken_word_count(script) == 3


def test_podcast_body_reserves_room_for_branded_frame():
    assert PODCAST_BODY_MAX_SPOKEN_WORDS < PODCAST_MAX_SPOKEN_WORDS


def test_english_podcast_frame_names_hosts_and_listener():
    frame = _podcast_intro_line("Deepika", "en") + _podcast_outro_lines("en")
    assert "AstroRoshni Podcast" in frame
    assert "Ananya" in frame
    assert "Arjun" in frame
    assert "Deepika" in frame


def test_hindi_podcast_frame_names_hosts():
    frame = _podcast_intro_line("दीपिका", "hi") + _podcast_outro_lines("hi")
    assert "अनन्या" in frame
    assert "अर्जुन" in frame
    assert "दीपिका" in frame
