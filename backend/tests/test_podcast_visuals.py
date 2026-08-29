import json
from types import SimpleNamespace

import pytest

from tts import podcast_visual_cache, podcast_visuals


def test_visual_copy_drops_pause_durations_but_keeps_spoken_cue_text():
    value = "[RISE:Welcome.] [PAUSE:short] The pattern [PAUSE:medium] is clear. [FALL:Use it well.]"

    assert podcast_visuals._strip_cues(value) == "Welcome. The pattern is clear. Use it well."
    assert podcast_visuals._clip_copy(value, 120) == "Welcome. The pattern is clear. Use it well."


def test_visible_copy_is_truncated_at_a_word_boundary_with_ellipsis():
    text = "This creative core is backed by solid secondary strengths in teaching, law, and strategy"

    clipped = podcast_visuals._clip_copy(text, 64)

    assert clipped == "This creative core is backed by solid secondary strengths in..."
    assert len(clipped) <= 64


def test_visible_copy_is_unchanged_when_it_fits():
    assert podcast_visuals._clip_copy("A complete heading", 64) == "A complete heading"


def test_visible_copy_removes_markdown_and_html_but_keeps_readable_text():
    value = "### **Career** <span class=\"chat-sentiment-positive\">growth</span> via [Jupiter](https://example.com)<br>soon"

    assert podcast_visuals._clip_copy(value, 120) == "Career growth via Jupiter soon"


def test_visible_copy_removes_list_and_code_markers():
    value = "- `Focus`\n* **Build steadily**\n1. Review timing"

    assert podcast_visuals._clip_copy(value, 120) == "Focus Build steadily Review timing"


def test_referenced_divisions_recognises_codes_and_traditional_names_in_order():
    text = "First examine the Navamsa, then compare D10 and the D-24 chart."

    assert podcast_visuals.referenced_divisions(text) == [9, 10, 24]


def test_referenced_houses_preserves_first_mention_order():
    text = "The 10th house activates the 2nd house; भाव 7 is also relevant."

    assert podcast_visuals.referenced_houses(text) == [10, 2, 7]


def test_referenced_houses_recognises_latin_hindi_ordinal():
    assert podcast_visuals.referenced_houses("10ve bhaav mein 35 SAV points hain") == [10]


def test_hindi_planets_and_named_houses_are_grounded_source_facts():
    source = podcast_visuals.visual_source(
        "unchanged",
        [("female", "शनि दशम भाव में है और गुरु द्वितीय भाव को प्रभावित करते हैं।")],
    )

    facts = podcast_visuals._source_facts(source)

    assert facts["houses"] == {2, 10}
    assert {"Saturn", "Jupiter"}.issubset(set(facts["planets"].values()))


def test_divisional_scene_keeps_only_a_chart_named_in_the_podcast(monkeypatch):
    source = podcast_visuals.visual_source(
        "unchanged",
        [("female", "Let us inspect your D9 Navamsa for marriage.")],
    )
    monkeypatch.setattr(
        podcast_visuals,
        "_generate_with_gemini",
        lambda *_: {
            "title": "Navamsa",
            "scenes": [{
                "type": "divisional_chart",
                "division": "D10",
                "headline": "Marriage pattern",
                "segment_start": 0,
                "segment_end": 0,
            }],
        },
    )

    manifest = podcast_visuals.generate_visual_manifest(source, "en")

    assert manifest["scenes"][0]["type"] == "divisional_chart"
    assert manifest["scenes"][0]["division"] == "D9"


def test_fallback_uses_real_visual_types_for_dasha_and_divisional_copy():
    source = podcast_visuals.visual_source(
        "unchanged",
        [("female", "Your Saturn mahadasha activates the D10 Dashamsa career chart.")],
    )

    manifest = podcast_visuals._add_timing(podcast_visuals._fallback_manifest(source, "en"), source)

    scene_types = {scene["type"] for scene in manifest["scenes"]}
    assert "divisional_chart" in scene_types or "dasha_timeline" in scene_types
    assert any(scene.get("division") == "D10" for scene in manifest["scenes"])


def test_fallback_uses_house_activation_map_for_activation_copy():
    source = podcast_visuals.visual_source(
        "unchanged",
        [("female", "Your dasha activates the 2nd and 10th houses now.")],
    )

    manifest = podcast_visuals._add_timing(podcast_visuals._fallback_manifest(source, "en"), source)

    assert any(scene["type"] == "house_activation_map" for scene in manifest["scenes"])
from tts import routes


def test_visual_source_preserves_the_existing_podcast_script_and_segments():
    script = "FEMALE: [RISE:Really?]\nMALE: [FALL:Yes.]"
    segments = [("female", "[RISE:Really?]"), ("male", "[FALL:Yes.]")]

    source = podcast_visuals.visual_source(
        script,
        segments,
        "Original answer",
        segment_audio_sizes=[1200, 1800],
    )

    assert source["script"] == script
    assert source["message_content"] == "Original answer"
    assert source["segments"] == [
        {"index": 0, "speaker": "female", "text": "[RISE:Really?]", "audio_weight": 1200, "audio_duration_ms": 0},
        {"index": 1, "speaker": "male", "text": "[FALL:Yes.]", "audio_weight": 1800, "audio_duration_ms": 0},
    ]


def test_visual_source_persists_selected_chart_identity_without_birth_data():
    source = podcast_visuals.visual_source(
        "script",
        [("female", "Welcome")],
        birth_chart_id=10308,
    )

    assert source["birth_chart_id"] == 10308
    assert not any(key in source for key in ("date", "time", "latitude", "longitude", "place"))


def test_mp3_frame_duration_is_measured_without_external_decoder():
    # MPEG-1 Layer III, 128 kbps, 44.1 kHz: 417-byte frames, 1152 samples each.
    frame = bytes.fromhex("fffb9000") + bytes(413)

    assert podcast_visuals.mp3_duration_ms(frame * 100) == pytest.approx(2612, abs=1)


def test_cached_source_is_upgraded_from_segment_byte_boundaries():
    frame = bytes.fromhex("fffb9000") + bytes(413)
    first = frame * 10
    second = frame * 30
    source = podcast_visuals.visual_source(
        "script",
        [("female", "First"), ("male", "Second")],
        segment_audio_sizes=[len(first), len(second)],
    )

    upgraded = podcast_visuals.add_audio_durations_to_source(source, first + second)

    assert upgraded["segments"][0]["audio_duration_ms"] == pytest.approx(261, abs=1)
    assert upgraded["segments"][1]["audio_duration_ms"] == pytest.approx(784, abs=1)


def test_visual_manifest_uses_segment_order_and_computed_fractional_timing(monkeypatch):
    source = podcast_visuals.visual_source(
        "unchanged",
        [
            ("female", "A short opening."),
            ("male", "The 2nd house and 10th house support this substantially longer explanation."),
            ("female", "A practical close."),
        ],
    )
    generated = {
        "title": "Career direction",
        "scenes": [
            {
                "type": "opening",
                "headline": "The question",
                "supporting_text": "Start here",
                "segment_start": 0,
                "segment_end": 0,
            },
            {
                "type": "house_highlight",
                "headline": "The evidence",
                "supporting_text": "What supports it",
                "segment_start": 1,
                "segment_end": 1,
                "houses": [2, 10],
            },
            {
                "type": "action_steps",
                "headline": "What to do",
                "supporting_text": "Move carefully",
                "segment_start": 2,
                "segment_end": 2,
                "steps": ["Focus", "Prove", "Grow"],
            },
        ],
    }
    monkeypatch.setattr(podcast_visuals, "_generate_with_gemini", lambda *_: generated)

    manifest = podcast_visuals.generate_visual_manifest(source, "en")

    assert manifest["title"] == "Career direction"
    assert manifest["scenes"][0]["start_fraction"] == 0.0
    assert manifest["scenes"][-1]["end_fraction"] == 1.0
    assert manifest["scenes"][0]["end_fraction"] < manifest["scenes"][1]["end_fraction"]
    assert manifest["scenes"][1]["houses"] == [2, 10]
    assert manifest["scenes"][2]["steps"] == ["Focus", "Prove", "Grow"]


def test_visual_manifest_rejects_unknown_scene_types(monkeypatch):
    source = podcast_visuals.visual_source("same script", [("female", "Only existing words.")])
    monkeypatch.setattr(
        podcast_visuals,
        "_generate_with_gemini",
        lambda *_: {
            "title": "Test",
            "scenes": [{
                "type": "invented_cinematic_scene",
                "headline": "Existing conclusion",
                "segment_start": 0,
                "segment_end": 0,
            }],
        },
    )

    manifest = podcast_visuals.generate_visual_manifest(source, "en")

    assert manifest["scenes"][0]["type"] == "key_takeaway"


def test_visual_manifest_prefers_generated_audio_segment_weights(monkeypatch):
    source = podcast_visuals.visual_source(
        "unchanged",
        [("female", "Many written words that are spoken quickly."), ("male", "Short.")],
        segment_audio_sizes=[100, 900],
    )
    monkeypatch.setattr(
        podcast_visuals,
        "_generate_with_gemini",
        lambda *_: {
            "title": "Timing",
            "scenes": [
                {"type": "opening", "headline": "First", "segment_start": 0, "segment_end": 0},
                {"type": "closing", "headline": "Second", "segment_start": 1, "segment_end": 1},
            ],
        },
    )

    manifest = podcast_visuals.generate_visual_manifest(source, "en")

    assert manifest["timing_basis"] == "audio_segments"
    assert manifest["scenes"][0]["end_fraction"] == 0.1
    assert manifest["turns"] == [
        {"speaker": "female", "start_fraction": 0.0, "end_fraction": 0.1},
        {"speaker": "male", "start_fraction": 0.1, "end_fraction": 1.0},
    ]


def test_visual_manifest_prefers_exact_duration_over_mp3_byte_size(monkeypatch):
    source = podcast_visuals.visual_source(
        "unchanged",
        [("female", "First."), ("male", "Second.")],
        segment_audio_sizes=[900, 100],
        segment_audio_durations_ms=[100, 900],
    )
    monkeypatch.setattr(
        podcast_visuals,
        "_generate_with_gemini",
        lambda *_: {
            "title": "Timing",
            "scenes": [
                {"type": "opening", "headline": "First", "segment_start": 0, "segment_end": 0},
                {"type": "closing", "headline": "Second", "segment_start": 1, "segment_end": 1},
            ],
        },
    )

    manifest = podcast_visuals.generate_visual_manifest(source, "en")

    assert manifest["scenes"][0]["end_fraction"] == 0.1
    assert manifest["audio_timing_measure"] == "duration_ms"
    assert manifest["captions"] == [
        {"speaker": "female", "text": "First.", "start_fraction": 0.0, "end_fraction": 0.1},
        {"speaker": "male", "text": "Second.", "start_fraction": 0.1, "end_fraction": 1.0},
    ]
    assert manifest["caption_timing_basis"] == "measured_audio_segments"


def test_caption_timeline_uses_actual_dialogue_without_production_cues(monkeypatch):
    source = podcast_visuals.visual_source(
        "script",
        [
            ("female", "[RISE:Welcome.] [PAUSE:short] This is your personal reading."),
            ("male", "[PAUSE:medium] Now let us examine the evidence carefully."),
        ],
        segment_audio_sizes=[100, 100],
        segment_audio_durations_ms=[1000, 1000],
    )
    monkeypatch.setattr(
        podcast_visuals,
        "_generate_with_gemini",
        lambda *_: {"title": "Reading", "scenes": [{"type": "opening", "headline": "Begin", "segment_start": 0, "segment_end": 1}]},
    )

    manifest = podcast_visuals.generate_visual_manifest(source, "en")
    caption_text = " ".join(item["text"] for item in manifest["captions"])

    assert "short" not in caption_text
    assert "medium" not in caption_text
    assert "Welcome." in caption_text
    assert manifest["captions"][0]["start_fraction"] == 0.0
    assert manifest["captions"][-1]["end_fraction"] == 1.0
    assert {item["speaker"] for item in manifest["captions"]} == {"female", "male"}


def test_v3_flattens_chapters_into_short_ordered_beats(monkeypatch):
    source = podcast_visuals.visual_source(
        "unchanged",
        [("female", "Mercury is in the 10th house through October 2027."), ("male", "Use this period carefully.")],
        segment_audio_sizes=[500, 500],
    )
    monkeypatch.setattr(
        podcast_visuals,
        "_generate_with_gemini",
        lambda *_: {
            "title": "Career timing",
            "chapters": [
                {
                    "title": "The pattern",
                    "segment_start": 0,
                    "segment_end": 0,
                    "beats": [
                        {"type": "natal_chart", "headline": "The chart", "houses": [10], "planets": ["Mercury"], "hold": 2},
                        {"type": "date_window", "headline": "The window", "dates": ["October 2027"], "hold": 1},
                    ],
                },
                {
                    "title": "The response",
                    "segment_start": 1,
                    "segment_end": 1,
                    "beats": [{"type": "decision_path", "headline": "Move carefully"}],
                },
            ],
        },
    )

    manifest = podcast_visuals.generate_visual_manifest(source, "en")

    assert manifest["version"] == 3
    scene_types = [scene["type"] for scene in manifest["scenes"]]
    assert scene_types[:2] == ["natal_chart", "date_window"]
    assert "decision_path" in scene_types
    assert len(manifest["scenes"]) == 6
    assert all(
        left["end_fraction"] <= right["end_fraction"]
        for left, right in zip(manifest["scenes"], manifest["scenes"][1:])
    )
    assert manifest["scenes"][-1]["end_fraction"] == 1.0
    assert len(manifest["chapters"]) == 2


def test_v3_removes_model_facts_not_present_in_dialogue(monkeypatch):
    source = podcast_visuals.visual_source(
        "unchanged",
        [("female", "Mercury activates the 10th house until October 2027.")],
    )
    monkeypatch.setattr(
        podcast_visuals,
        "_generate_with_gemini",
        lambda *_: {
            "chapters": [{
                "title": "Facts",
                "segment_start": 0,
                "segment_end": 0,
                "beats": [{
                    "type": "natal_chart",
                    "headline": "Evidence",
                    "houses": [7, 10],
                    "planets": ["Mercury", "Saturn"],
                    "dates": ["October 2027", "January 2030"],
                }],
            }],
        },
    )

    scene = podcast_visuals.generate_visual_manifest(source, "en")["scenes"][0]

    assert scene["houses"] == [10]
    assert scene["planets"] == ["Mercury"]
    assert scene["dates"] == ["October 2027"]


def test_v3_fallback_has_variety_and_bounded_beat_count(monkeypatch):
    segments = [("female" if index % 2 == 0 else "male", " ".join([f"word{index}"] * 36)) for index in range(18)]
    source = podcast_visuals.visual_source("unchanged", segments)
    monkeypatch.setattr(podcast_visuals, "_generate_with_gemini", lambda *_: (_ for _ in ()).throw(RuntimeError("offline")))

    manifest = podcast_visuals.generate_visual_manifest(source, "en")

    assert 18 <= len(manifest["scenes"]) <= 75
    assert len({scene["type"] for scene in manifest["scenes"]}) >= 7
    assert 1 <= len(manifest["chapters"]) <= 10
    assert manifest["planning_source"] == "deterministic_fallback"


def test_short_fallback_chapters_each_receive_a_grounded_visual(monkeypatch):
    source = podcast_visuals.visual_source(
        "unchanged",
        [
            ("female", "यह स्थिर प्रगति की कहानी है।"),
            ("male", "इसमें धैर्य से आगे बढ़ना उपयोगी रहेगा।"),
            ("female", "आप अपनी दिशा को स्पष्ट रख सकते हैं।"),
        ],
    )
    monkeypatch.setattr(podcast_visuals, "_generate_with_gemini", lambda *_: (_ for _ in ()).throw(RuntimeError("offline")))

    manifest = podcast_visuals.generate_visual_manifest(source, "hi")

    assert all(
        any(scene["type"] in podcast_visuals.GROUNDED_VISUAL_TYPES for scene in manifest["scenes"] if scene["chapter_index"] == index)
        for index, _chapter in enumerate(manifest["chapters"])
    )


def test_abstract_model_plan_is_rebalanced_with_chart_visuals(monkeypatch):
    source = podcast_visuals.visual_source(
        "unchanged",
        [("female", "Your direction becomes clearer."), ("male", "Move with patience and focus.")],
    )
    monkeypatch.setattr(
        podcast_visuals,
        "_generate_with_gemini",
        lambda *_: {
            "title": "Direction",
            "chapters": [{
                "title": "Direction",
                "segment_start": 0,
                "segment_end": 1,
                "beats": [
                    {"type": "celestial_interlude", "headline": "Pause"},
                    {"type": "balance", "headline": "Consider both sides"},
                ],
            }],
        },
    )

    manifest = podcast_visuals.generate_visual_manifest(source, "en")

    assert any(scene["type"] in podcast_visuals.GROUNDED_VISUAL_TYPES for scene in manifest["scenes"])


def test_sav_reference_replaces_generic_grounded_scene_and_highlights_house(monkeypatch):
    source = podcast_visuals.visual_source(
        "unchanged",
        [("female", "10ve bhaav mein 35 SAV points hain, jo career ko support karte hain.")],
    )
    monkeypatch.setattr(
        podcast_visuals,
        "_generate_with_gemini",
        lambda *_: {
            "title": "Career",
            "chapters": [{
                "title": "Career",
                "segment_start": 0,
                "segment_end": 0,
                "beats": [
                    {"type": "natal_chart", "headline": "Career chart"},
                    {"type": "balance", "headline": "Support and pressure"},
                ],
            }],
        },
    )

    manifest = podcast_visuals.generate_visual_manifest(source, "hi")
    sav_scene = next(scene for scene in manifest["scenes"] if scene["type"] == "ashtakavarga_table")

    assert sav_scene["houses"] == [10]
    assert podcast_visuals._mentions_ashtakavarga("10ve bhaav mein 35 SAV points hain")


def test_fixed_podcast_greeting_and_signoff_receive_programme_bookends(monkeypatch):
    source = podcast_visuals.visual_source(
        "unchanged",
        [
            ("female", "Welcome to the AstroRoshni Podcast. I'm Ananya."),
            ("male", "And I'm Arjun. Let's understand your chart."),
            ("female", "Your 10th house is the main career signal."),
            ("female", "That's our reading for today. Keep the useful insight."),
            ("male", "Thank you for listening."),
            ("female", "And I'm Ananya. We'll meet you again on the AstroRoshni Podcast."),
        ],
    )
    monkeypatch.setattr(
        podcast_visuals,
        "_generate_with_gemini",
        lambda *_: {
            "title": "Career",
            "chapters": [
                {"title": "Welcome", "segment_start": 0, "segment_end": 1, "beats": [
                    {"type": "celestial_interlude", "headline": "Welcome"},
                    {"type": "balance", "headline": "Meet the hosts"},
                ]},
                {"title": "Career", "segment_start": 2, "segment_end": 2, "beats": [
                    {"type": "house_highlight", "headline": "Career", "houses": [10]},
                    {"type": "natal_chart", "headline": "Your chart"},
                ]},
                {"title": "Goodbye", "segment_start": 3, "segment_end": 5, "beats": [
                    {"type": "orbit", "headline": "Closing"},
                    {"type": "comparison", "headline": "Thank you"},
                ]},
            ],
        },
    )

    manifest = podcast_visuals.generate_visual_manifest(source, "en")

    assert {scene["type"] for scene in manifest["scenes"] if scene["segment_end"] <= 1} == {"opening"}
    assert {scene["type"] for scene in manifest["scenes"] if scene["segment_start"] >= 3} == {"closing"}
    assert any(scene["type"] == "house_highlight" for scene in manifest["scenes"])


def test_deterministic_fallback_also_reserves_bookends_for_real_intro_and_outro(monkeypatch):
    source = podcast_visuals.visual_source(
        "unchanged",
        [
            ("female", "नमस्ते! AstroRoshni Podcast में आपका स्वागत है। मैं हूँ अनन्या।"),
            ("male", "और मैं हूँ अर्जुन। आइए आपकी रीडिंग समझते हैं।"),
            ("female", "दशम भाव करियर का मुख्य संकेत देता है।"),
            ("male", "इसी संकेत पर व्यावहारिक रूप से काम कीजिए।"),
            ("female", "आज के लिए बस इतना ही।"),
            ("male", "सुनने के लिए धन्यवाद।"),
            ("female", "और मैं अनन्या। फिर मिलेंगे AstroRoshni Podcast पर।"),
        ],
    )
    monkeypatch.setattr(podcast_visuals, "_generate_with_gemini", lambda *_: (_ for _ in ()).throw(RuntimeError("offline")))

    manifest = podcast_visuals.generate_visual_manifest(source, "hi")
    opening_scenes = [scene for scene in manifest["scenes"] if scene["type"] == "opening"]
    closing_scenes = [scene for scene in manifest["scenes"] if scene["type"] == "closing"]

    assert opening_scenes and all(scene["segment_start"] <= 1 for scene in opening_scenes)
    assert closing_scenes and all(scene["segment_end"] >= 4 for scene in closing_scenes)
    assert not any(
        scene["type"] in {"opening", "closing"} and scene["segment_start"] >= 2 and scene["segment_end"] <= 3
        for scene in manifest["scenes"]
    )


def test_personalised_intro_recovers_profile_name_without_other_birth_data():
    source = podcast_visuals.visual_source(
        "script",
        [
            ("female", "[RISE:नमस्ते!] आज की यह व्यक्तिगत रीडिंग Kavya Sharma के लिए है।"),
            ("male", "और मैं हूँ अर्जुन।"),
        ],
    )

    assert routes._podcast_native_name_hint(source) == "Kavya Sharma"


def test_english_personalised_intro_recovers_profile_name():
    source = podcast_visuals.visual_source(
        "script",
        [("female", "Welcome. Today's personal reading is for Kavya Sharma.")],
    )

    assert routes._podcast_native_name_hint(source) == "Kavya Sharma"


def test_legacy_source_estimates_both_speakers_instead_of_only_ananya(monkeypatch):
    source = podcast_visuals.visual_source_from_message(" ".join(f"word{index}" for index in range(120)))
    monkeypatch.setattr(podcast_visuals, "_generate_with_gemini", lambda *_: (_ for _ in ()).throw(RuntimeError("offline")))

    manifest = podcast_visuals.generate_visual_manifest(source, "en")

    assert {turn["speaker"] for turn in manifest["turns"]} == {"female", "male"}
    assert manifest["speaker_timing_basis"] == "estimated_visual_boundaries"


def test_hindi_visuals_do_not_reintroduce_english_when_densifying_legacy_source(monkeypatch):
    source = podcast_visuals.visual_source_from_message(
        "Career growth becomes clearer when you study the timing and take practical steps. " * 8
    )
    monkeypatch.setattr(
        podcast_visuals,
        "_generate_with_gemini",
        lambda *_: {
            "title": "आपकी दिशा",
            "chapters": [{
                "title": "करियर की दिशा",
                "segment_start": 0,
                "segment_end": len(source["segments"]) - 1,
                "beats": [
                    {"type": "opening", "headline": "मुख्य संकेत", "supporting_text": "समय को ध्यान से समझें।"},
                    {"type": "action_steps", "headline": "अगला कदम", "supporting_text": "व्यावहारिक रास्ता चुनें।"},
                ],
            }],
        },
    )

    manifest = podcast_visuals.generate_visual_manifest(source, "hi")

    assert manifest["language"] == "hi"
    assert all(podcast_visuals._has_devanagari(scene["headline"]) for scene in manifest["scenes"])
    assert all(
        not scene.get("supporting_text") or podcast_visuals._has_devanagari(scene["supporting_text"])
        for scene in manifest["scenes"]
    )


def test_hindi_deterministic_fallback_never_displays_english_source(monkeypatch):
    source = podcast_visuals.visual_source_from_message("An older English chat answer used for a Hindi podcast. " * 12)
    monkeypatch.setattr(podcast_visuals, "_generate_with_gemini", lambda *_: (_ for _ in ()).throw(RuntimeError("offline")))

    manifest = podcast_visuals.generate_visual_manifest(source, "hi")

    assert all(podcast_visuals._has_devanagari(scene["headline"]) for scene in manifest["scenes"])
    assert all(podcast_visuals._has_devanagari(scene["supporting_text"]) for scene in manifest["scenes"])


def test_ashtakavarga_dialogue_uses_the_table_visual_in_fallback(monkeypatch):
    source = podcast_visuals.visual_source(
        "script",
        [("female", "The 10th house has 32 SAV bindus in Sarvashtakavarga."), ("male", "Jupiter BAV adds 5 bindus there.")],
    )
    monkeypatch.setattr(podcast_visuals, "_generate_with_gemini", lambda *_: (_ for _ in ()).throw(RuntimeError("offline")))

    manifest = podcast_visuals.generate_visual_manifest(source, "en")

    assert "ashtakavarga_table" in {scene["type"] for scene in manifest["scenes"]}
    assert podcast_visuals._mentions_ashtakavarga("Compare the SAVs before deciding.")


def test_podcast_ashtakavarga_visual_is_house_indexed_and_privacy_minimised():
    planets = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
    chart = {
        "ascendant": 90.0,
        "planets": {planet: {"sign": index % 12} for index, planet in enumerate(planets)},
    }

    payload = routes._podcast_ashtakavarga_visual(SimpleNamespace(), chart)

    assert len(payload["rows"]) == 12
    assert payload["rows"][0]["house"] == 1
    assert payload["rows"][0]["sign"] == 3
    assert set(payload["rows"][0]["bav"]) == set(planets)
    assert sum(row["sav"] for row in payload["rows"]) == payload["total_bindus"]
    assert set(payload) == {"rows", "total_bindus"}


def test_visual_json_cache_round_trip_uses_separate_metadata(monkeypatch, tmp_path):
    monkeypatch.setenv("PODCAST_CACHE_DIR", str(tmp_path))
    monkeypatch.delenv("PODCAST_CACHE_BUCKET", raising=False)
    message_id = "visual-test-98127"
    payload = {"version": 1, "scenes": [{"headline": "Hello"}]}

    podcast_visual_cache.put_visual_json(message_id, "en", "manifest", payload)
    podcast_visual_cache._MEMORY.clear()

    assert podcast_visual_cache.get_visual_json(message_id, "en", "manifest") == payload


def test_visual_source_survives_manifest_version_changes(monkeypatch, tmp_path):
    monkeypatch.setenv("PODCAST_CACHE_DIR", str(tmp_path))
    monkeypatch.delenv("PODCAST_CACHE_BUCKET", raising=False)
    message_id = "legacy-speaker-source"
    payload = {"segments": [{"speaker": "female"}, {"speaker": "male"}]}
    legacy_path = tmp_path / "visual" / f"{message_id}_en_v4_source.json"
    legacy_path.parent.mkdir(parents=True)
    legacy_path.write_text(json.dumps(payload), encoding="utf-8")
    podcast_visual_cache._MEMORY.clear()

    assert podcast_visual_cache.get_visual_json(message_id, "en", "source") == payload


def test_new_visual_source_uses_stable_unversioned_key(monkeypatch, tmp_path):
    monkeypatch.setenv("PODCAST_CACHE_DIR", str(tmp_path))
    monkeypatch.delenv("PODCAST_CACHE_BUCKET", raising=False)
    message_id = "stable-speaker-source"
    payload = {"segments": [{"speaker": "female"}, {"speaker": "male"}]}

    podcast_visual_cache.put_visual_json(message_id, "en", "source", payload)

    assert (tmp_path / "visual" / f"{message_id}_en_source.json").is_file()


@pytest.mark.asyncio
async def test_visual_endpoint_attaches_sanitised_chart_and_caches_manifest(monkeypatch):
    source = podcast_visuals.visual_source("script", [("female", "Opening")])
    monkeypatch.setattr(routes, "_find_podcast_history", lambda *_: ("81", "session-1", "en", "preview"))
    monkeypatch.setattr(
        routes,
        "get_visual_json",
        lambda _message_id, _lang, kind: source if kind == "source" else None,
    )
    monkeypatch.setattr(
        routes,
        "generate_visual_manifest",
        lambda *_: {"version": 3, "scenes": [{"headline": "Opening"}]},
    )
    monkeypatch.setattr(
        routes,
        "_podcast_chart_visual",
        lambda *_: {"ascendant": 12.5, "ascendant_sign": 0, "planets": [{"name": "Sun", "house": 1}]},
    )
    cached = {}
    monkeypatch.setattr(
        routes,
        "put_visual_json",
        lambda message_id, lang, kind, payload: cached.update({"key": (message_id, lang, kind), "payload": payload}),
    )

    response = await routes.podcast_visuals(
        message_id="81",
        lang="en",
        current_user=SimpleNamespace(userid=18),
    )
    payload = json.loads(response.body)

    assert payload["manifest"]["visual_style"] == "cinematic_v3"
    assert payload["manifest"]["chart"]["planets"][0]["name"] == "Sun"
    assert cached["key"] == ("81", "en", "manifest")
