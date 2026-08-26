import asyncio

import chat.instant_chat_pipeline as pipeline


class _FailIfGeneratedAnalyzer:
    def __init__(self):
        self.generate_calls = 0

    async def generate_text_from_prompt(self, prompt, **kwargs):
        self.generate_calls += 1
        raise AssertionError("medical triage must not invoke the astrology composer")


def _run(question, intent=None, language="english"):
    analyzer = _FailIfGeneratedAnalyzer()
    result = asyncio.run(
        pipeline.generate_instant_chat_response(
            analyzer,
            question=question,
            birth_data={"name": "Test"},
            intent=intent or {},
            history=[],
            language=language,
        )
    )
    return analyzer, result


def test_active_chest_pain_bypasses_astrology_and_credit_charge():
    analyzer, result = _run("I have chest pain. Is it astrology or something serious?")

    assert analyzer.generate_calls == 0
    assert result["skip_instant_credit_charge"] is True
    assert result["timing"]["medical_safety_triage"] is True
    assert result["timing"]["medical_triage_source"] == "direct_fail_safe"
    assert result["timing"]["calculator_execution_skipped"] is True
    assert "medical emergency" in result["response"].lower()
    assert "astrology cannot" in result["response"].lower()
    assert "vulnerabil" not in result["response"].lower()
    assert result["follow_up_questions"] == []


def test_semantic_multilingual_triage_uses_router_message():
    localized = "यह आपात स्थिति हो सकती है। अभी चिकित्सा सहायता लें।"
    analyzer, result = _run(
        "मेरे सीने में अभी दर्द है",
        intent={
            "medical_triage": {
                "urgency": "emergency",
                "reason": "active chest pain",
                "user_message": localized,
            }
        },
        language="hindi",
    )

    assert analyzer.generate_calls == 0
    assert result["response"] == localized
    assert result["timing"]["medical_triage_source"] == "semantic_router"


def test_general_heart_susceptibility_is_not_direct_emergency_gate():
    assert pipeline._instant_medical_triage_decision(
        "Does my chart show a future vulnerability to heart issues?", {}
    ) is None
