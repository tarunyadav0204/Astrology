from types import SimpleNamespace

from ai.parallel_chat.parallel_agent_payloads import build_jaimini_agent_payload
from calculators.chart_calculator import ChartCalculator
from calculators.chara_dasha_calculator import CharaDashaCalculator
from context_agents.base import AgentContext
from chat.chat_context_builder import ChatContextBuilder


def _birth_data():
    return {
        "name": "Reference Chart",
        "date": "1980-04-02",
        "time": "14:55",
        "latitude": 29.1492,
        "longitude": 75.7217,
        "place": "Hisar, Haryana, India",
        "timezone": 5.5,
    }


def test_jaimini_parallel_payload_includes_chara_dasha_and_a7_occupants():
    birth = _birth_data()
    builder = ChatContextBuilder()
    static = builder._build_static_context(birth)

    payload = build_jaimini_agent_payload(
        AgentContext(
            birth_data=birth,
            user_question="How is marriage in 2028?",
            precomputed_static=static,
        ),
        "How is marriage in 2028?",
    )

    assert "jaimini" in payload
    assert "chara_dasha" in payload
    assert "jx" in payload
    assert "JP" in payload["jaimini"]
    assert "PS" in payload["jaimini"]
    assert "A7" in payload["jaimini"]["JP"]
    assert "pp" in payload["jaimini"]["JP"]["A7"]
    assert "P" in payload["chara_dasha"]
    assert "rf" in payload["jx"]
    assert "kr" in payload["jx"]
    assert "dk_asp" in payload["jx"]
    assert "amk_ak" in payload["jx"]
    assert "ul2" in payload["jx"]
    assert "al10" in payload["jx"]
    assert "kl10" in payload["jx"]


def test_chara_dasha_respects_explicit_focus_date_for_current_md():
    birth = _birth_data()
    birth_obj = SimpleNamespace(**birth)
    chart = ChartCalculator({}).calculate_chart(birth_obj, "mean")
    calc = CharaDashaCalculator(chart)

    dob = __import__("datetime").datetime.strptime(birth["date"], "%Y-%m-%d")
    focus = __import__("datetime").datetime(2028, 1, 1)
    result = calc.calculate_dasha(dob, focus_date=focus)

    current_periods = [p for p in result["periods"] if p.get("is_current")]
    assert len(current_periods) == 1
    current_md = current_periods[0]
    current_ads = [ad for ad in current_md.get("antardashas", []) if ad.get("is_current")]
    assert len(current_ads) == 1


def test_jaimini_derived_payload_relative_facts_are_consistent():
    birth = _birth_data()
    static = ChatContextBuilder()._build_static_context(birth)

    payload = build_jaimini_agent_payload(
        AgentContext(
            birth_data=birth,
            user_question="Will marriage manifest well?",
            precomputed_static=static,
        ),
        "Will marriage manifest well?",
    )

    jx = payload["jx"]
    ul_sign = payload["jaimini"]["JP"]["UL"]["s"]
    md_sign = jx["md"]
    ad_sign = jx["ad"]

    assert jx["rf"]["UL"]["md"] == ((md_sign - ul_sign) % 12) + 1
    assert jx["rf"]["UL"]["ad"] == ((ad_sign - ul_sign) % 12) + 1

    ul2_sign = (ul_sign % 12) + 1
    assert jx["ul2"]["s"] == ul2_sign
    for planet in jx["ul2"]["pp"]:
        assert payload["jaimini"]["PS"][planet]["s"] == ul2_sign
