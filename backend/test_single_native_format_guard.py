from ai.output_schema import build_final_prompt


def test_single_native_prompt_includes_non_relational_guard():
    prompt = build_final_prompt(
        user_question="Tell me about my marriage from my chart",
        context={
            "analysis_type": "birth",
            "birth_details": {"name": "Tarun"},
            "ascendant_info": {"sign_name": "Cancer", "exact_degree_in_sign": 10.0},
            "intent": {"mode": "ANALYZE_TOPIC_POTENTIAL", "category": "marriage"},
        },
        history=[],
        language="english",
        response_style="detailed",
        user_context={"user_name": "Tarun", "user_relationship": "self"},
        premium_analysis=False,
        mode="ANALYZE_TOPIC_POTENTIAL",
    )

    assert "FORMAT GUARD FOR SINGLE-NATIVE READINGS" in prompt
    assert "This is NOT a two-person synastry/relational reading" in prompt
    assert '"Behavioral Texture"' in prompt
