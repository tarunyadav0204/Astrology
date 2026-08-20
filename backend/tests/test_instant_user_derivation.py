from instant_chat_v2.user_derivation import build_user_derivation


def test_marriage_capacity_explains_d1_and_d9_without_current_timing():
    instant_context = {
        "instant_parashari": {
            "focus_houses": [7, 2, 11, 5],
            "topic_signals": {
                "pattern": "The 7th-house marriage factors receive direct support",
                "risk": "Saturn adds delay and requires maturity",
                "hh": {
                    "7": {"sc": 3, "txt": "a stable partnership foundation"},
                },
            },
            "divisional_support": {
                "topic": {
                    "support": "supportive",
                    "charts": {
                        "D9": {
                            "support": "supportive",
                            "rows": [
                                {"h": 1, "lord": "Jupiter", "lord_h": 5, "occ": [], "band": "supportive"},
                                {"h": 7, "lord": "Mercury", "lord_h": 11, "occ": ["Venus"], "band": "supportive"},
                                {"h": 8, "lord": "Moon", "lord_h": 6, "occ": [], "band": "weak"},
                            ],
                        }
                    },
                },
                "current_topic": {
                    "support": "supportive",
                    "charts": {
                        "D9": {"rows": [{"h": 10, "lord": "Saturn", "band": "supportive"}]}
                    },
                },
            },
        },
        "normalized_evidence": {
            "natal_promise": {"status": "supported", "topic_support": "supportive"},
            "topic_confirmation": {},
            "divisional_specifics": [
                "Topic divisional support in D9 specifically highlights house 1, lord Jupiter.",
                "Current divisional timing in D9 specifically highlights house 10, lord Saturn.",
            ],
        },
        "intent_summary": {"focus_houses": [7, 2, 11, 5]},
    }
    result = build_user_derivation(
        query_plan={"category": "marriage", "answer_mode": "potential_capacity"},
        verdict={"direction": "supported_natal_promise", "confidence": 0.84},
        instant_context=instant_context,
    )

    promise = result["natal_promise"]
    combined = " ".join([
        *promise["basis"], *promise["d1_factors"],
        *promise["divisional_factors"], *promise["cautions"],
    ])
    assert result["schema_version"] == "instant-user-derivation/v2"
    assert promise["evidence_complete"] is True
    assert "D1 House 7" in combined
    assert "D9, House 7 governs the spouse" in combined
    assert "lord Mercury is placed in House 11" in combined
    assert "occupants are Venus" in combined
    assert "House 8 governs durability" in combined
    assert "house 10" not in combined.lower()
    assert "Current divisional timing" not in combined


def test_capacity_does_not_promote_current_topic_support_to_natal_promise():
    result = build_user_derivation(
        query_plan={"category": "marriage", "answer_mode": "potential_capacity"},
        verdict={"direction": "qualified_natal_promise"},
        instant_context={
            "instant_parashari": {},
            "normalized_evidence": {
                "natal_promise": {"status": "qualified", "current_topic_support": "supportive"},
            },
        },
    )
    assert not any("rated supportive" in line for line in result["natal_promise"]["basis"])
    assert result["natal_promise"]["evidence_complete"] is False


def test_validated_d1_house_factors_replace_aggregate_topic_copy():
    result = build_user_derivation(
        query_plan={"category": "marriage", "answer_mode": "potential_capacity"},
        verdict={"direction": "supported_natal_promise"},
        instant_context={
            "instant_parashari": {
                "focus_houses": [7],
                "divisional_support": {"topic": {"support": "supportive", "charts": {"D9": {"rows": [
                    {"h": 7, "lord": "Mercury", "lord_h": 2, "occ": [], "band": "supportive"}
                ]}}}},
            },
            "_user_evidence": {
                "natal_topic_factors": {
                    "source": "validated_d1_natal_promise",
                    "houses": [{
                        "house": 7,
                        "lord": "Saturn",
                        "occupants": ["Venus"],
                        "aspecting_planets": ["Jupiter"],
                        "karakas": ["Venus"],
                        "tone": "supportive",
                        "supportive_weight": 5.5,
                        "challenging_weight": 2.0,
                        "yogas": [{"key": "kendra_trikona", "name": "Kendra-Trikona sambandha"}],
                        "factors": [
                            {"source": "house_lord_condition", "planet": "Saturn", "polarity": "supportive", "weight": 1.5,
                             "facts": {"dignity": "own_sign", "placement_house": 11, "combustion": "normal"}},
                            {"source": "natural_karaka_condition", "planet": "Venus", "polarity": "supportive", "weight": 0.75,
                             "facts": {"dignity": "exalted", "placement_house": 7}},
                        ],
                    }],
                },
            },
            "normalized_evidence": {"natal_promise": {"status": "supported", "topic_support": "supportive"}},
        },
    )
    promise = result["natal_promise"]
    combined = " ".join(promise["d1_factors"])
    assert "D1 House 7" in combined
    assert "ruled by Saturn, placed in House 11 in own sign condition" in combined
    assert "contains Venus" in combined
    assert "classical aspects from Jupiter" in combined
    assert "Natural karaka check" in combined
    assert "Kendra-Trikona sambandha" in combined
    assert promise["d1_house_factors"][0]["strongest_supports"][0]["planet"] == "Saturn"
    assert promise["evidence_complete"] is True
