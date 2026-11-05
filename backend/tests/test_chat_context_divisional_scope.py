from chat.chat_context_builder import _restrict_divisional_chart_scope


def test_health_scope_removes_unrequested_d10_from_embedded_d1_divisions():
    context = {
        "d1_chart": {
            "divisions": {
                "D1": {"Sun": {"house": 4}},
                "D9": {"Sun": {"house": 6}},
                "D10": {"Mars": {"house": 5, "dignity": "exalted"}},
                "D30": {"Moon": {"house": 12}},
            }
        }
    }

    _restrict_divisional_chart_scope(context, ["D1", "D9", "D30"])

    assert set(context["d1_chart"]["divisions"]) == {"D1", "D9", "D30"}
    assert "D10" not in context["d1_chart"]["divisions"]


def test_cross_domain_scope_keeps_the_union_selected_by_router():
    context = {
        "d1_chart": {
            "divisions": {
                "D1": {},
                "D9": {},
                "D10": {},
                "D30": {},
            }
        }
    }

    _restrict_divisional_chart_scope(context, ["D1", "D9", "D10", "D30"])

    assert set(context["d1_chart"]["divisions"]) == {"D1", "D9", "D10", "D30"}


def test_scope_removes_other_explicit_navamsa_payloads_when_d9_is_not_selected():
    context = {
        "d1_chart": {"divisions": {"D1": {}, "D9": {}, "D10": {}}},
        "d9_planetary_analysis": {"Mars": {"house": 1}},
        "ashtakavarga": {"d1_rashi": {}, "d9_navamsa": {"sarvashtakavarga": {}}},
    }

    _restrict_divisional_chart_scope(context, ["D1", "D10"])

    assert "d9_planetary_analysis" not in context
    assert "d9_navamsa" not in context["ashtakavarga"]
