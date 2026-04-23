from types import SimpleNamespace

from ai.progeny_ai_context_generator import ProgenyAIContextGenerator
from calculators.progeny_analyzer import ProgenyAnalyzer
from progeny.progeny_analysis_execute import _build_progeny_question, _merge_or_pad_progeny_questions


def _build_chart_data():
    houses = [{"sign": i} for i in range(12)]
    planets = {
        "Sun": {"house": 10, "sign": 9, "longitude": 285.0, "retrograde": False},
        "Moon": {"house": 4, "sign": 3, "longitude": 95.0, "retrograde": False},
        "Mars": {"house": 3, "sign": 2, "longitude": 65.0, "retrograde": False},
        "Mercury": {"house": 5, "sign": 4, "longitude": 132.0, "retrograde": False},
        "Jupiter": {"house": 5, "sign": 4, "longitude": 128.0, "retrograde": False},
        "Venus": {"house": 5, "sign": 4, "longitude": 140.0, "retrograde": False},
        "Saturn": {"house": 8, "sign": 7, "longitude": 210.0, "retrograde": True},
        "Rahu": {"house": 11, "sign": 10, "longitude": 320.0, "retrograde": True},
        "Ketu": {"house": 5, "sign": 4, "longitude": 140.0, "retrograde": True},
    }
    return {
        "ascendant": 0.0,
        "planets": planets,
        "houses": houses,
    }


def test_progeny_prompt_separates_promise_timing_and_parenting():
    request = SimpleNamespace(analysis_focus="parenting", children_count=2, gender="female")
    context = {
        "progeny_analysis": {
            "fertility_sphuta": {"type": "Kshetra Sphuta", "strength": "Strong (Favorable)"},
            "d1_fifth_house": {"sign": "Leo", "lord": "Sun", "planets": ["Jupiter"], "has_malefics": False},
            "d7_analysis": {"d7_lagna_lord": "Mars", "planets_in_d7_5th": ["Jupiter"], "summary": "Supportive"},
            "jupiter_status": {"sign": "Leo", "house": 5, "status": "Supportive"},
            "timing_indicators": ["Jupiter", "Sun"],
        },
        "progeny_evidence": {
            "promise": {"rating": "Strong", "notes": ["D7 shows strong child-supportive signatures."]},
            "safety_rules": ["Supportive guidance only, not medical diagnosis."],
        },
        "current_dashas": {
            "mahadasha": {"planet": "Jupiter"},
            "antardasha": {"planet": "Moon"},
        },
        "current_timing_summary": {"summary": "Current timing is Jupiter / Moon"},
    }

    prompt = _build_progeny_question(request, context)

    assert "Do NOT predict conception timing" in prompt
    assert "Current Dasha Summary" in prompt
    assert "Promise Rating" in prompt
    assert '"analysis_mode": "parenting"' in prompt
    assert '"parenting_guidance"' in prompt
    assert prompt.count('question": "') >= 10


def test_progeny_questions_are_padded_to_ten_sections():
    request = SimpleNamespace(analysis_focus="first_child", children_count=0, gender="female")
    context = {
        "current_timing_summary": {"summary": "Current timing is Jupiter / Moon"},
        "progeny_analysis": {
            "d1_fifth_house": {"sign": "Leo", "lord": "Sun", "planets": ["Jupiter"], "has_malefics": False},
            "d7_analysis": {"d7_lagna_lord": "Mars", "planets_in_d7_5th": ["Jupiter"], "planets_in_d7_9th": [], "planets_in_d7_2nd": [], "support_level": "Strong"},
            "jupiter_status": {"sign": "Leo", "house": 5, "status": "Supportive"},
            "fertility_sphuta": {"type": "Kshetra Sphuta", "strength": "Strong (Favorable)"},
        },
        "progeny_evidence": {
            "promise": {"rating": "Strong", "notes": ["D7 shows strong child-supportive signatures."]}
        },
    }

    merged = _merge_or_pad_progeny_questions(
        [{"question": "What is the core progeny promise in the chart?", "answer": "Custom answer"}],
        context,
        request,
    )

    assert len(merged) == 10
    assert merged[0]["answer"] == "Custom answer"
    assert merged[-1]["question"] == "What practical remedies and actions are supportive?"


def test_progeny_analyzer_emits_evidence_spine(monkeypatch):
    monkeypatch.setattr(
        ProgenyAnalyzer,
        "_get_d7_chart",
        lambda self: {
            "ascendant": 0.0,
            "planets": {
                "Jupiter": {"sign": 4},
                "Venus": {"sign": 8},
                "Saturn": {"sign": 4},
            },
        },
    )

    analyzer = ProgenyAnalyzer(_build_chart_data(), {"gender": "female"})
    result = analyzer.analyze_progeny()

    assert "progeny_evidence" in result
    assert result["progeny_evidence"]["promise"]["rating"] in {"Strong", "Moderate", "Sensitive"}
    assert "support_level" in result["d7_analysis"]
    assert "d7_ninth_house_sign" in result["d7_analysis"]
    assert "confidence" in result["fertility_sphuta"]


def test_progeny_context_generator_adds_focus_and_timing_summary(monkeypatch):
    generator = ProgenyAIContextGenerator()
    birth_data = {
        "name": "Test",
        "date": "1990-01-01",
        "time": "12:00",
        "place": "Delhi",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "gender": "female",
        "analysis_focus": "next_child",
        "children_count": 1,
    }

    chart_data = _build_chart_data()
    birth_hash = generator._create_birth_hash(birth_data)
    generator.static_cache[birth_hash] = {"d1_chart": chart_data}

    monkeypatch.setattr(
        generator,
        "build_base_context",
        lambda _birth_data: {
            "d1_chart": chart_data,
            "current_dashas": {
                "mahadasha": {"planet": "Jupiter"},
                "antardasha": {"planet": "Moon"},
                "pratyantardasha": {"planet": "Mercury"},
            },
        },
    )

    context = generator.build_progeny_context(birth_data)

    assert context["analysis_focus"] == "next_child"
    assert context["children_count"] == 1
    assert context["current_timing_summary"]["available"] is True
    assert context["current_timing_summary"]["summary"].startswith("Current timing is Jupiter / Moon")
    assert "focus_rule" in context["interpretative_guidelines"]
    assert context["progeny_evidence"]["promise"]["rating"] in {"Strong", "Moderate", "Sensitive"}
