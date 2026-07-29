from prediction_engine.manifestation_synthesis import (
    _cache_key,
    _merge,
    _theme_cache_payload,
    build_minimal_synthesis_context,
    house_signification_tags,
)


def test_merge_preserves_engine_astrology_fields_and_accepts_llm_wording():
    deterministic = [{
        "manifestation_id": "m1",
        "subject": "self",
        "window": {"start_date": "2026-07-01", "end_date": "2026-07-20"},
        "house_roles": [{"native_house": 2, "relative_house": 2, "outcome_tone": "mixed"}],
        "outcome_tone": "mixed",
        "label": "Old label",
        "possibilities": ["bounded"],
    }]
    generated = {"themes": [{
        "theme_key": "theme-a",
        "label": "A financial decision with a partner",
        "summary": "Savings and shared obligations may need coordinated decisions.",
        "possibilities": ["A joint financial adjustment"],
        "synthesis_strength": "well_supported",
        "window": {"start_date": "2099-01-01", "end_date": "2099-01-02"},
        "outcome_tone": "supportive",
    }]}
    output = _merge(deterministic, generated, {"m1": "theme-a"})["manifestations"][0]
    assert output["label"] == "A financial decision with a partner"
    assert output["window"] == deterministic[0]["window"]
    assert output["outcome_tone"] == "mixed"
    assert output["house_roles"] == deterministic[0]["house_roles"]


def test_merge_dedupes_same_theme_across_windows():
    deterministic = [
        {
            "manifestation_id": "m1",
            "subject": "self",
            "window": {"start_date": "2026-01-01", "end_date": "2026-01-10"},
            "label": "Old A",
            "house_roles": [{"native_house": 2}],
        },
        {
            "manifestation_id": "m2",
            "subject": "self",
            "window": {"start_date": "2026-07-01", "end_date": "2026-07-20"},
            "label": "Old B",
            "house_roles": [{"native_house": 2}],
        },
    ]
    generated = {"themes": [{
        "theme_key": "theme-a",
        "label": "Shared LLM label",
        "possibilities": ["One possibility"],
    }]}
    merged = _merge(deterministic, generated, {"m1": "theme-a", "m2": "theme-a"})["manifestations"]
    assert len(merged) == 1
    assert merged[0]["label"] == "Shared LLM label"
    assert set(merged[0]["source_manifestation_ids"]) == {"m1", "m2"}
    assert len(merged[0]["related_windows"]) == 2


def test_per_theme_cache_key_ignores_batch_and_theme_key():
    theme_a = {
        "theme_key": "aaa",
        "subject": "self",
        "activated_houses": [{"house": 1, "significations": ["identity"]}],
        "tone_by_house": {"1": "constructive"},
    }
    theme_b = {
        "theme_key": "bbb",
        "subject": "self",
        "activated_houses": [{"house": 1, "significations": ["identity"]}],
        "tone_by_house": {"1": "constructive"},
    }
    theme_c = {
        "theme_key": "ccc",
        "subject": "self",
        "activated_houses": [{"house": 1, "significations": ["identity"]}],
        "tone_by_house": {"1": "pressure"},
    }
    key_a = _cache_key(_theme_cache_payload(theme_a), locale="en", provider="gemini", model="models/a")
    key_b = _cache_key(_theme_cache_payload(theme_b), locale="en", provider="gemini", model="models/a")
    key_c = _cache_key(_theme_cache_payload(theme_c), locale="en", provider="gemini", model="models/a")
    assert key_a == key_b
    assert key_a != key_c
    # Batching with another theme must not affect the per-combination key.
    assert "themes" not in _theme_cache_payload(theme_a)


def test_minimal_context_uses_only_houses_significations_and_tone():
    deterministic = [
        {
            "manifestation_id": "self-1",
            "subject": "self",
            "window": {"start_date": "2026-07-01", "end_date": "2026-07-20", "mahadasha": "Saturn"},
            "label": "Engine wording must not reach the LLM",
            "summary": "Do not send this",
            "possibilities": ["engine possibility"],
            "house_roles": [
                {
                    "native_house": 2,
                    "relative_house": 2,
                    "outcome_tone": "challenging",
                    "dasha_connections": ["Saturn connects by natal occupation"],
                    "transit_connections": ["Transit Mars occupying H2"],
                    "direct_carriers": ["Saturn"],
                },
                {
                    "native_house": 7,
                    "relative_house": 7,
                    "outcome_tone": "mixed",
                },
            ],
            "helpful_reasons": [{"text": "secret"}],
            "pressure_reasons": [{"text": "secret"}],
        },
        {
            "manifestation_id": "mother-1",
            "subject": "mother",
            "house_roles": [
                {
                    "native_house": 8,
                    "relative_house": 5,
                    "outcome_tone": "supportive",
                }
            ],
        },
        {
            # Same house+tone combo as self-1 → shared theme_key / cache fingerprint.
            "manifestation_id": "self-2",
            "subject": "self",
            "house_roles": [
                {"native_house": 2, "relative_house": 2, "outcome_tone": "challenging"},
                {"native_house": 7, "relative_house": 7, "outcome_tone": "mixed"},
            ],
        },
    ]

    context, theme_by_id = build_minimal_synthesis_context(deterministic)
    payload = _canonical_like(context)

    assert "mahadasha" not in payload
    assert "Engine wording" not in payload
    assert "dasha_connections" not in payload
    assert "transit_connections" not in payload
    assert "helpful_reasons" not in payload
    assert "window" not in payload

    themes = context["themes"]
    assert len(themes) == 2
    assert theme_by_id["self-1"] == theme_by_id["self-2"]

    self_theme = next(item for item in themes if item["subject"] == "self")
    assert self_theme["activated_houses"] == [
        {"house": 2, "significations": house_signification_tags(2)},
        {"house": 7, "significations": house_signification_tags(7)},
    ]
    assert self_theme["tone_by_house"] == {"2": "pressure", "7": "mixed"}

    mother_theme = next(item for item in themes if item["subject"] == "mother")
    assert mother_theme["activated_houses"] == [{
        "relative_house": 5,
        "significations": house_signification_tags(5),
    }]
    assert mother_theme["tone_by_house"] == {"5": "constructive"}
    assert "native_house" not in mother_theme["activated_houses"][0]


def test_house_signification_tags_include_expanded_coverage():
    assert "change" in house_signification_tags(3)
    assert "mother" in house_signification_tags(4)
    assert "spouse" in house_signification_tags(7)
    assert "tax" in house_signification_tags(8)
    assert "insurance" in house_signification_tags(8)
    assert "inheritance" in house_signification_tags(8)
    assert "income" in house_signification_tags(11)
    assert "hospitals" in house_signification_tags(12)
    # Body parts stay in the registry but are not sent to the LLM.
    assert "kidneys" not in house_signification_tags(7)
    assert "knees" not in house_signification_tags(10)
    assert "teeth" not in house_signification_tags(2)


def test_extract_json_accepts_common_llm_shapes():
    from prediction_engine.manifestation_synthesis import _extract_json

    expected = ["theme-a", "theme-b"]
    bare_array = _extract_json(
        '[{"label":"One","possibilities":["a"]},{"label":"Two","summary":"b"}]',
        expected_theme_keys=expected,
    )
    assert [row["theme_key"] for row in bare_array["themes"]] == expected
    assert bare_array["themes"][0]["label"] == "One"

    alt_key = _extract_json(
        '{"life_themes":[{"theme_key":"theme-a","label":"Alt"}]}',
        expected_theme_keys=expected,
    )
    assert alt_key["themes"][0]["label"] == "Alt"

    fenced = _extract_json(
        '```json\n{"themes":[{"theme_key":"theme-a","label":"Fenced"}]}\n```',
        expected_theme_keys=expected,
    )
    assert fenced["themes"][0]["label"] == "Fenced"


def _canonical_like(value) -> str:
    import json
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
