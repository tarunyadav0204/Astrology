from reel_studio.worker import _scene_image_prompt


def _plan(language: str):
    return {
        "settings": {"language": language},
        "claims": [{"id": "claim_1", "text": "A verified chart fact."}],
    }


def _snapshot():
    return {
        "ascendant_sign": 4,  # Leo
        "placements": [{"planet": "Sun", "house": 4, "degree_in_sign": 11.2}],
        "visual_graph": {"nodes": [], "edges": []},
    }


def test_hindi_chart_prompt_supplies_hindi_labels_and_typography_lock():
    prompt = _scene_image_prompt(
        _plan("hi"),
        {"type": "chart_focus", "narration": "यह हिंदी वर्णन है।", "visual_instruction": "चार्ट दिखाएं।", "evidence_ids": ["claim_1"]},
        _snapshot(),
    )

    assert "भाव 1 — सिंह (5)" in prompt
    assert '"ग्रह": "सूर्य"' in prompt
    assert "HINDI TYPOGRAPHY LOCK: Every visible non-brand word MUST use Devanagari Hindi." in prompt


def test_english_chart_prompt_keeps_english_chart_labels():
    prompt = _scene_image_prompt(
        _plan("en"),
        {"type": "chart_focus", "narration": "Show the chart.", "visual_instruction": "Show chart.", "evidence_ids": ["claim_1"]},
        _snapshot(),
    )

    assert "House 1 — Leo (5)" in prompt
    assert "HINDI TYPOGRAPHY LOCK: Not applicable." in prompt
