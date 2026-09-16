from calculators.event_timeline_accuracy_v3 import build_month_activation_graph, build_v3_prediction_model, user_fact_fingerprint
from calculators.event_timeline_delivery_v1 import (
    accuracy_layer_mode,
    ashtakavarga_judgment,
    birth_time_reliability_judgment,
    exact_transit_judgment,
    kp_judgment,
    natal_promise,
    node_chain,
    obstruction_profile,
    outcome_dimensions,
    planet_delivery,
    supporting_systems_judgment,
    timing_windows,
    varga_judgment,
)


def _context():
    return {
        "d1_chart": {
            "ascendant": 5.0,
            "planets": {
                "Sun": {"longitude": 125.0, "sign": 4, "house": 5, "retrograde": False},
                "Moon": {"longitude": 8.0, "sign": 0, "house": 1, "retrograde": False},
                "Mars": {"longitude": 215.0, "sign": 7, "house": 8, "retrograde": False},
                "Mercury": {"longitude": 65.0, "sign": 2, "house": 3, "retrograde": False},
                "Jupiter": {"longitude": 248.0, "sign": 8, "house": 9, "retrograde": True},
                "Venus": {"longitude": 39.0, "sign": 1, "house": 2, "retrograde": False},
                "Saturn": {"longitude": 305.0, "sign": 10, "house": 11, "retrograde": False},
                "Rahu": {"longitude": 42.0, "sign": 1, "house": 2, "retrograde": True},
                "Ketu": {"longitude": 222.0, "sign": 7, "house": 8, "retrograde": True},
            },
        },
        "divisional_charts": {
            "navamsa_chart": {
                "divisional_chart": {
                    "ascendant": 5.0,
                    "planets": {
                        "Jupiter": {"house": 9, "sign": 8, "dignity": "own_sign"},
                        "Saturn": {"house": 11, "sign": 10, "dignity": "own_sign"},
                        "Rahu": {"house": 12, "sign": 11, "dignity": "neutral"},
                    },
                }
            }
        },
    }


def _evidence(eid, level, planet, natal_house, lordships, transit_house, aspects, start="2030-01-01", end="2030-01-31"):
    return {
        "kind": "dasha_lord_transit", "evidence_id": eid, "dasha_level": level,
        "planet": planet, "natal_house": natal_house, "lordships": lordships,
        "transit_house": transit_house, "aspected_houses": aspects,
        "start_date": start, "end_date": end,
    }


def _graph():
    return build_month_activation_graph({"evidence": [
        _evidence("saturn", "mahadasha", "Saturn", 11, [10, 11], 9, [11, 3, 6]),
        _evidence("rahu", "antardasha", "Rahu", 2, [], 8, [2], end="2030-01-15"),
        _evidence("jupiter", "pratyantardasha", "Jupiter", 9, [9, 12], 12, [4, 6, 8], start="2030-01-16"),
    ]})


def test_natal_promise_delivery_and_node_chain_are_traced():
    context = _context()
    promise = natal_promise("foreign_travel", {9}, {3, 12}, {11}, context)
    assert promise["verdict"] in {"strong", "available"}
    assert promise["lord_links"] and promise["karaka_links"]
    assert promise["moon_repetition"]

    node = node_chain("Rahu", context, {3, 9, 11, 12})
    assert node["available"] is True
    assert node["dispositor"] == "Venus"
    assert node["nakshatra_lord"]
    assert node["doctrine"].endswith("no_node_lordship")

    delivery = planet_delivery("foreign_travel", ["Saturn", "Rahu", "Jupiter"], {3, 9, 11, 12}, context)
    assert delivery["verdict"] in {"supportive", "mixed", "obstructed"}
    assert len(delivery["carriers"]) == 3
    rahu = next(row for row in delivery["carriers"] if row["planet"] == "Rahu")
    assert rahu["node_chain"]["dispositor"] == "Venus"
    assert rahu["combustion"] == "unavailable"


def test_kp_requires_cusp_permission_and_every_active_carrier_for_strong_support():
    kp = {
        "cusp_lords": {9: {"sign_lord": "Jupiter", "star_lord": "Saturn", "sub_lord": "Jupiter", "sub_sub_lord": "Mercury"}},
        "planet_significators": {"Jupiter": [9, 12]},
        "four_step_theory": {
            planet: {
                "planet": {"name": planet, "houses": houses},
                "star_lord": {"name": "Jupiter", "houses": [9, 12]},
                "sub_lord": {"name": "Saturn", "houses": [11]},
                "sub_sub_lord": {"name": "Mercury", "houses": [3]},
            }
            for planet, houses in {"Saturn": [11], "Rahu": [12], "Jupiter": [9]}.items()
        },
    }
    supported = kp_judgment(kp, {9}, {3, 9, 11, 12}, {6, 8}, ["Saturn", "Rahu", "Jupiter"])
    assert supported["verdict"] == "supported"
    assert supported["active_carriers_confirmed"] == 3

    kp["four_step_theory"]["Rahu"] = {}
    qualified = kp_judgment(kp, {9}, {3, 9, 11, 12}, {6, 8}, ["Saturn", "Rahu", "Jupiter"])
    assert qualified["verdict"] == "qualified"


def test_varga_obstruction_dimensions_and_timing_windows_are_independent():
    context = _context()
    promise = natal_promise("foreign_travel", {9}, {3, 12}, {11}, context)
    delivery = planet_delivery("foreign_travel", ["Saturn", "Rahu", "Jupiter"], {3, 9, 11, 12}, context)
    varga = varga_judgment(
        context, "D9", "navamsa_chart", "foreign_travel", {9, 12},
        ["Saturn", "Rahu", "Jupiter"], promise, delivery,
    )
    assert varga["verdict"] in {"confirmed", "mixed"}
    assert varga["d1_repetition"] is True
    assert {row["planet"] for row in varga["confirmed_carriers"]} == {"Jupiter"}
    assert {row["planet"] for row in varga["non_confirming_carriers"]} == {"Saturn", "Rahu"}


def test_varga_does_not_claim_every_evaluated_dasha_planet_confirms():
    context = _context()
    promise = natal_promise("foreign_travel", {9}, {3, 12}, {11}, context)
    delivery = planet_delivery("foreign_travel", ["Jupiter", "Moon"], {3, 9, 11, 12}, context)
    varga = varga_judgment(
        context, "D9", "navamsa_chart", "foreign_travel", {9, 12},
        ["Jupiter", "Moon"], promise, delivery,
    )
    assert [row["planet"] for row in varga["confirmed_carriers"]] == ["Jupiter"]
    assert [row["planet"] for row in varga["non_confirming_carriers"]] == ["Moon"]
    assert varga["carrier_hits"][0]["d1_event_links"]

    graph = _graph()
    obstruction = obstruction_profile("foreign_travel", graph, {11})
    timing = timing_windows(graph, {9}, {3, 12}, {3, 9, 11, 12})
    assert obstruction["verdict"] in {"low", "moderate", "high"}
    assert timing["resolution"] == "calendar_day_segment_boundaries"
    assert timing["contact_phase"] == "sign_nakshatra_pada_level_only"
    assert timing["windows"]

    dimensions = outcome_dimensions("result_window", {"verdict": "high"}, {"verdict": "supportive"}, {"verdict": "supported"}, {"verdict": "confirmed"})
    assert dimensions["ease"] == "obstructed"
    assert dimensions["result"] != "strong"


def test_exact_transits_classify_phase_kp_cusp_and_reference_without_double_counting():
    context = _context()
    graph = {
        "transit_daily": {
            "Sun": [
                {"date": "2030-01-01", "longitude": 6.0, "speed": 1.0, "retrograde": False},
                {"date": "2030-01-02", "longitude": 8.0, "speed": 1.0, "retrograde": False},
                {"date": "2030-01-03", "longitude": 10.0, "speed": 1.0, "retrograde": False},
            ]
        },
        "transit_aspect_model": {"Sun": [1, 7]},
        "transit_stations": [{"date": "2030-01-02", "planet": "Sun", "direction": "direct"}],
    }
    result = exact_transit_judgment(
        context, graph, {"house_cusps": {6: 8.0}}, "health", {1, 6, 8, 12}, {6}, ["Sun"],
    )
    assert result["available"] is True
    assert any(row["peak_phase"] == "exact" and row["target"] == "Moon" for row in result["event_contacts"])
    assert any(row["target_type"] == "kp_anchor_cusp" for row in result["kp_cusp_contacts"])
    assert any(row["target_type"] == "moon_reference" for row in result["reference_contacts"])
    assert result["stations"]


def test_bav_kakshya_and_supporting_systems_are_capped_modifiers():
    context = _context()
    matrix = {ruler: {str(sign): 0 for sign in range(12)} for ruler in ("Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon", "Ascendant")}
    matrix["Mars"]["0"] = 1
    context["ashtakavarga"] = {
        "advanced": {"prastara": {"Sun": {"matrix": matrix, "sign_totals": {str(sign): (5 if sign == 0 else 0) for sign in range(12)}}}}
    }
    graph = {"transit_daily": {"Sun": [{"date": "2030-01-01", "longitude": 8.0, "retrograde": False}]}}
    av = ashtakavarga_judgment(context, graph, ["Sun"], {1})
    assert av["verdict"] == "supportive"
    assert av["role"] == "ease_modifier_only"

    context["supporting_systems"] = {
        "varshphal": {"available": True, "muntha": {"house": 9}, "year_lord": "Jupiter", "mudda_dasha": []},
        "chara_dasha": {"available": False, "periods": []},
        "monthly": {"1": {
            "yogini": {"available": True, "mahadasha": {"lord": "Jupiter"}, "antardasha": {"lord": "Saturn"}},
            "kalachakra": {"available": True, "mahadasha": {"planet": "Jupiter"}, "antardasha": {"planet": "Saturn"}},
        }},
        "sudarshana": {"available": True, "precision_triggers": []},
    }
    supporting = supporting_systems_judgment(context, "foreign_travel", {3, 9, 11, 12}, 1, 2030)
    assert supporting["available"] is True
    assert supporting["capped_priority_adjustment"] <= 3
    assert len(supporting["supportive_independence_groups"]) >= 2


def test_birth_time_boundary_risk_downgrades_sensitive_kp_and_varga(monkeypatch):
    monkeypatch.setenv("EVENT_TIMELINE_TRUST_SUPPLIED_BIRTH_TIME", "false")
    result = birth_time_reliability_judgment(
        {
            "birth_time_reliability": {"available": True, "uncertainty_minutes": 20, "source": "approximate_memory"},
            "birth_time_sensitivity": {"available": True, "boundary_risk": "high", "kp_cusp_sub_lord_changed": True},
        },
        {"available": True, "confirmed": True},
        {"complete": True, "verdict": "supported"},
    )
    assert result["verdict"] == "sensitive"
    assert result["kp_specificity"] == "downgraded"
    assert result["varga_specificity"] == "downgraded"


def test_accuracy_layer_defaults_on_and_has_cache_safe_rollback(monkeypatch):
    monkeypatch.delenv("EVENT_TIMELINE_V3_ACCURACY_LAYER", raising=False)
    assert accuracy_layer_mode() == "integrated_v2"
    current_fingerprint = user_fact_fingerprint({}, "en")

    monkeypatch.setenv("EVENT_TIMELINE_V3_ACCURACY_LAYER", "legacy_v3_6")
    assert accuracy_layer_mode() == "legacy_v3_6"
    assert user_fact_fingerprint({}, "en") != current_fingerprint
    ledger = {"months": {str(month): {"evidence": _graph_evidence() if month == 1 else []} for month in range(1, 13)}}
    legacy = build_v3_prediction_model(_context(), ledger, kp_evidence={}, user_facts={}, year=2030, age=40)
    assert legacy["accuracy_layer"] == "legacy_v3_6"
    assert all(row["accuracy_layer"] == "legacy_v3_6" for row in legacy["months"]["1"]["qualified_candidates"])


def test_month_only_and_yearly_models_use_the_same_accuracy_judgments(monkeypatch):
    monkeypatch.setenv("EVENT_TIMELINE_V3_ACCURACY_LAYER", "integrated_v2")
    evidence = _graph_evidence()
    annual_ledger = {"months": {str(month): {"evidence": evidence if month == 1 else []} for month in range(1, 13)}}
    month_ledger = {"months": {"1": {"evidence": evidence}}}
    annual = build_v3_prediction_model(_context(), annual_ledger, kp_evidence={}, user_facts={}, year=2030, age=40)
    monthly = build_v3_prediction_model(_context(), month_ledger, kp_evidence={}, user_facts={}, year=2030, age=40)
    annual_rows = annual["months"]["1"]["qualified_candidates"]
    monthly_rows = monthly["months"]["1"]["qualified_candidates"]
    assert [row["candidate_id"] for row in annual_rows] == [row["candidate_id"] for row in monthly_rows]
    assert [row["priority_score"] for row in annual_rows] == [row["priority_score"] for row in monthly_rows]
    assert [row["support_grade"] for row in annual_rows] == [row["support_grade"] for row in monthly_rows]


def test_delivery_v1_rollback_does_not_apply_integrated_supporting_modifiers(monkeypatch):
    monkeypatch.setenv("EVENT_TIMELINE_V3_ACCURACY_LAYER", "delivery_v1")
    ledger = {"months": {"1": {"evidence": _graph_evidence()}}}
    model = build_v3_prediction_model(_context(), ledger, kp_evidence={}, user_facts={}, year=2030, age=40)
    assert model["accuracy_layer"] == "delivery_v1"
    rows = model["months"]["1"]["qualified_candidates"]
    assert rows
    assert all(row["accuracy_layer"] == "delivery_v1" for row in rows)
    assert all(row["exact_transit_contacts"]["available"] is False for row in rows)
    assert all(row["ashtakavarga_confirmation"]["available"] is False for row in rows)
    assert all(row["supporting_systems"]["available"] is False for row in rows)


def test_legacy_layer_keeps_v36_saturn_rahu_jupiter_selection(monkeypatch):
    monkeypatch.setenv("EVENT_TIMELINE_V3_ACCURACY_LAYER", "legacy_v3_6")
    ledger = {"months": {str(month): {"evidence": _graph_evidence() if month == 1 else []} for month in range(1, 13)}}
    legacy = build_v3_prediction_model({"divisional_charts": {}}, ledger, kp_evidence={}, user_facts={}, year=2030, age=40)
    assert [row["event_key"] for row in legacy["months"]["1"]["publishable_candidates"]] == [
        "job_change", "foreign_travel", "income_gain", "children", "health",
    ]


def _graph_evidence():
    return [
        _evidence("saturn", "mahadasha", "Saturn", 11, [10, 11], 9, [11, 3, 6]),
        _evidence("rahu", "antardasha", "Rahu", 2, [], 8, [2]),
        _evidence("jupiter", "pratyantardasha", "Jupiter", 9, [9, 12], 12, [4, 6, 8]),
    ]
